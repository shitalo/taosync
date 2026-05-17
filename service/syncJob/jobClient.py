"""
@Author: Dr34m
@Date  : 2024/7/11 12:14
"""
import itertools
import json
import datetime
import logging
import threading
import time
from collections import defaultdict

from apscheduler.schedulers.background import BackgroundScheduler
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

from common.config import getConfig
from common.LNG import G
from mapper import jobMapper
from service.openlist import openlistService
from service.syncJob import taskService


class CopyItem:
    STATUS_QUERY_FAST_INTERVAL = 2.0
    STATUS_QUERY_SLOW_INTERVAL = 8.0
    STATUS_QUERY_MAX_TRANSIENT_FAILS = 4
    STATUS_LOST_RECHECK_TIMES = 3

    def __init__(self, srcPath, dstPath, fileName, fileSize, method, jobTask):
        self.jobTask = jobTask
        self.openlistClient = self.jobTask.openlistClient
        self.taskId = self.jobTask.taskId
        self.srcPath = srcPath
        self.dstPath = dstPath
        self.fileName = fileName
        self.fileSize = fileSize
        self.copyType = 0 if method < 2 else 2
        self.openlistTaskId = None
        self.status = 0
        self.progress = 0.0
        self.errMsg = None
        self.createTime = int(time.time())
        self.doingKey = None
        self.statusQueryFailNum = 0
        self.remoteStateConfirmed = False

    def doByThread(self):
        threading.Thread(target=self.doIt).start()

    @staticmethod
    def _get_query_intervals():
        cfg = getConfig()['server']
        fast_interval = max(1.0, float(cfg.get('status_query_fast_interval', CopyItem.STATUS_QUERY_FAST_INTERVAL)))
        slow_interval = max(fast_interval, float(cfg.get('status_query_slow_interval', CopyItem.STATUS_QUERY_SLOW_INTERVAL)))
        return fast_interval, slow_interval

    def doIt(self):
        try:
            if self.jobTask.breakFlag:
                self.status = 4
            else:
                self.openlistTaskId = self.openlistClient.copyFile(self.srcPath, self.dstPath, self.fileName)
        except Exception as e:
            self.errMsg = str(e)
            self.status = 7
        else:
            if self.openlistTaskId is None:
                self.status = 2
            elif self.status != 4:
                self.checkAndGetStatus()
        self.endIt()

    def checkAndGetStatus(self):
        while True:
            if self.jobTask.breakFlag:
                self.status = 4
                if self.openlistTaskId is not None:
                    try:
                        self.openlistClient.copyTaskCancel(self.openlistTaskId)
                        self.openlistClient.copyTaskDelete(self.openlistTaskId)
                    except Exception as e:
                        self.status = 7
                        self.errMsg = str(e)
                break
            cuTime = time.time()
            fast_interval, slow_interval = self._get_query_intervals()
            time.sleep(fast_interval if cuTime - self.jobTask.lastWatching < 3 else slow_interval)
            try:
                taskInfo = self.openlistClient.taskInfoCached(self.openlistTaskId)
                if taskInfo is None:
                    taskInfo = self.openlistClient.taskInfo(self.openlistTaskId)
                self.statusQueryFailNum = 0
                self.remoteStateConfirmed = True
            except Exception as e:
                logger = logging.getLogger()
                logger.exception(e)
                eMsg = str(e)
                if '404' in eMsg:
                    taskInfo = self.confirmRemoteTaskState(G('task_may_delete'))
                    if taskInfo is None:
                        continue
                else:
                    self.statusQueryFailNum += 1
                    self.errMsg = eMsg
                    if self.statusQueryFailNum < self.STATUS_QUERY_MAX_TRANSIENT_FAILS:
                        continue
                    taskInfo = self.confirmRemoteTaskState(eMsg)
                    if taskInfo is None:
                        continue
            if taskInfo['state'] == self.status and taskInfo['progress'] == self.progress:
                continue
            self.status = taskInfo['state']
            self.progress = taskInfo['progress']
            self.errMsg = taskInfo['error'] if taskInfo['error'] else None
            if taskInfo['state'] in [2, 4, 7]:
                if self.remoteStateConfirmed:
                    try:
                        self.openlistClient.copyTaskDelete(self.openlistTaskId)
                        break
                    except Exception:
                        break
                break

    def confirmRemoteTaskState(self, errMsg):
        taskInfo = None
        for _ in range(self.STATUS_LOST_RECHECK_TIMES):
            try:
                taskInfo = self.openlistClient.taskInfoByLists(self.openlistTaskId)
            except Exception:
                taskInfo = None
            if taskInfo is not None:
                self.remoteStateConfirmed = True
                self.statusQueryFailNum = 0
                return taskInfo
            time.sleep(1.0)
        self.remoteStateConfirmed = False
        self.status = 12
        self.errMsg = errMsg
        return None

    def endIt(self):
        if self.copyType == 2 and self.status == 2:
            try:
                self.openlistClient.deleteFile(self.srcPath, [self.fileName], self.jobTask.job['scanIntervalS'])
            except Exception as e:
                self.status = 7
                self.errMsg = G('copy_success_but_delete_fail').format(str(e))
        self.jobTask.copyHook(self.srcPath, self.dstPath, self.fileName, self.fileSize, self.openlistTaskId, self.status,
                              errMsg=self.errMsg, copyType=self.copyType, createTime=self.createTime)
        del self.jobTask.doing[self.doingKey]


class JobTask:
    def __init__(self, taskId, vm):
        self.taskId = taskId
        self.jobClient = vm
        self.job = self.jobClient.job
        self.openlistClient = openlistService.getClientById(self.job['openlistId'])
        self.createTime = time.time()
        self.finish = []
        self.doing = {}
        self.waiting = []
        self.lastWatching = 0.0
        self.queueNum = 0
        self.scanFinish = False
        self.firstSync = None
        self.breakFlag = False
        self.scanBackoff = {}
        self.scanBackoffSkipStats = {}
        self.finalized = False
        self.finalizeLock = threading.Lock()
        threading.Thread(target=self._run_sync, name=f"job-sync-{taskId}", daemon=True).start()
        self.currentTasks = {}
        threading.Thread(target=self._run_task_submit, name=f"job-submit-{taskId}", daemon=True).start()

    def getCurrent(self):
        self.lastWatching = time.time()
        waits = [{
            'srcPath': waitItem.srcPath,
            'dstPath': waitItem.dstPath,
            'isPath': 0,
            'fileName': waitItem.fileName,
            'fileSize': waitItem.fileSize,
            'status': waitItem.status,
            'type': waitItem.copyType,
            'progress': waitItem.progress,
            'errMsg': waitItem.errMsg,
            'createTime': waitItem.createTime
        } for waitItem in self.waiting]
        dos = [{
            'srcPath': doItem.srcPath,
            'dstPath': doItem.dstPath,
            'isPath': 0,
            'fileName': doItem.fileName,
            'fileSize': doItem.fileSize,
            'status': doItem.status,
            'type': doItem.copyType,
            'progress': doItem.progress,
            'errMsg': doItem.errMsg,
            'createTime': doItem.createTime
        } for doItem in self.doing.values()]
        allTask = list(itertools.chain(waits, dos, self.finish))
        keyValSpace = {'wait': 0, 'running': 1, 'success': 2, 'fail': 7, 'other': -1}
        currentTasks = {val: [] for val in keyValSpace.values()}
        otk = []
        otkStatus = [3, 4, 5, 6, 8, 9, 10, 11, 12]
        grouped = defaultdict(list)
        for taskItem in allTask:
            grouped[taskItem['status']].append(taskItem)
        for status, tasks in grouped.items():
            tasks.sort(key=lambda x: x['createTime'])
            if status in otkStatus:
                otk.extend(tasks)
            else:
                currentTasks[status] = tasks
        currentTasks[-1] = otk
        self.currentTasks = currentTasks
        result = {
            'scanFinish': self.scanFinish,
            'doingTask': currentTasks[1],
            'createTime': int(self.createTime),
            'duration': int(self.lastWatching - self.createTime),
            'firstSync': int(self.firstSync) if self.firstSync is not None else None,
            'num': {},
            'size': {}
        }
        for key, val in keyValSpace.items():
            result['num'][key] = len(currentTasks[val])
            result['size'][key] = sum(item['fileSize'] for item in currentTasks[val]
                                      if item['fileSize'] is not None and item['type'] != 1)
        return result

    def _scan_backoff_key(self, path, isSrc):
        return ('src' if isSrc else 'dst', path)

    def _get_scan_backoff_cfg(self):
        cfg = getConfig()['server']
        base_seconds = max(5, int(cfg.get('scan_retry_backoff_base', 60)))
        max_seconds = max(base_seconds, int(cfg.get('scan_retry_backoff_max', 1800)))
        return base_seconds, max_seconds

    def _check_scan_backoff(self, path, isSrc):
        item = self.scanBackoff.get(self._scan_backoff_key(path, isSrc))
        if item is None:
            return None
        now = time.time()
        if now >= item['until']:
            del self.scanBackoff[self._scan_backoff_key(path, isSrc)]
            return None
        remain = int(item['until'] - now)
        return f"scan backoff active, retry after {remain}s"

    def _log_scan_backoff_skip(self, path, rootPath, isSrc, useCache, scanInterval, backoff_msg):
        logger = logging.getLogger()
        key = self._scan_backoff_key(path, isSrc)
        stat = self.scanBackoffSkipStats.get(key)
        if stat is None:
            stat = {'count': 0, 'path': path, 'rootPath': rootPath, 'isSrc': isSrc,
                    'totalBackoffSeconds': 0, 'maxFailCount': 0}
            self.scanBackoffSkipStats[key] = stat
        stat['count'] += 1
        backoff_state = self.scanBackoff.get(key)
        if backoff_state is not None:
            stat['totalBackoffSeconds'] += int(backoff_state.get('last_backoff_seconds', 0))
            stat['maxFailCount'] = max(stat['maxFailCount'], int(backoff_state.get('count', 0)))
        logger.warning(
            "Scan skipped by backoff | job_id=%s task_id=%s openlist_id=%s is_src=%s path=%s root_path=%s use_cache=%s scan_interval=%s reason=%s",
            self.jobClient.jobId,
            self.taskId,
            self.job.get('openlistId'),
            isSrc,
            path,
            rootPath,
            useCache,
            scanInterval,
            backoff_msg
        )

    def _emit_scan_backoff_summary(self):
        if not self.scanBackoffSkipStats:
            return
        logger = logging.getLogger()
        for stat in self.scanBackoffSkipStats.values():
            logger.warning(
                "Scan backoff summary | job_id=%s task_id=%s is_src=%s path=%s root_path=%s skip_count=%s total_backoff_seconds=%s max_fail_count=%s",
                self.jobClient.jobId,
                self.taskId,
                stat['isSrc'],
                stat['path'],
                stat['rootPath'],
                stat['count'],
                stat['totalBackoffSeconds'],
                stat['maxFailCount']
            )
        self.scanBackoffSkipStats = {}

    def _record_scan_backoff(self, path, isSrc):
        key = self._scan_backoff_key(path, isSrc)
        base_seconds, max_seconds = self._get_scan_backoff_cfg()
        old = self.scanBackoff.get(key)
        fail_count = 1 if old is None else old['count'] + 1
        backoff_seconds = min(max_seconds, base_seconds * (2 ** (fail_count - 1)))
        self.scanBackoff[key] = {'count': fail_count, 'until': time.time() + backoff_seconds,
                                 'last_backoff_seconds': backoff_seconds}
        return backoff_seconds, fail_count

    def _clear_scan_backoff(self, path, isSrc):
        key = self._scan_backoff_key(path, isSrc)
        if key in self.scanBackoff:
            del self.scanBackoff[key]

    def getCurrentByStatus(self, status):
        return self.currentTasks[status]

    def taskSubmit(self):
        copy_parallel = min(20, max(1, int(getConfig()['server'].get('copy_parallel', 8))))
        while True:
            if self.breakFlag:
                break
            time.sleep(0.5)
            doingNums = len(self.doing.keys())
            waitingNums = len(self.waiting)
            if not self.scanFinish or doingNums != 0 or waitingNums != 0:
                while doingNums < copy_parallel:
                    if self.breakFlag:
                        break
                    if waitingNums == 0:
                        break
                    if self.firstSync is None:
                        self.firstSync = time.time()
                    self.queueNum += 1
                    self.doing[self.queueNum] = self.waiting.pop(0)
                    self.doing[self.queueNum].doingKey = self.queueNum
                    self.doing[self.queueNum].doByThread()
                    doingNums = len(self.doing.keys())
                    waitingNums = len(self.waiting)
            else:
                break
        tryTime = 0
        while len(self.doing.keys()) > 0:
            tryTime += 1
            time.sleep(.5)
            if tryTime > 3:
                break
        self.finalizeTask()

    def copyHook(self, srcPath, dstPath, name, size, openlistTaskId=None, status=0, errMsg=None, isPath=0,
                 copyType=0, createTime=int(time.time())):
        self.finish.append({
            'taskId': self.taskId,
            'srcPath': srcPath,
            'dstPath': dstPath,
            'isPath': isPath,
            'fileName': name,
            'fileSize': size,
            'type': copyType,
            'openlistTaskId': openlistTaskId,
            'status': status,
            'errMsg': errMsg,
            'createTime': createTime
        })

    def delHook(self, dstPath, name, size, status=2, errMsg=None, isPath=0, createTime=int(time.time())):
        self.finish.append({
            'taskId': self.taskId,
            'srcPath': None,
            'dstPath': dstPath,
            'isPath': isPath,
            'fileName': name,
            'fileSize': size,
            'type': 1,
            'openlistTaskId': None,
            'status': status,
            'errMsg': errMsg,
            'createTime': createTime
        })

    def sync(self):
        srcPath = self.job['srcPath']
        jobExclude = self.job['exclude']
        spec = None
        if jobExclude is not None:
            spec = PathSpec.from_lines(GitWildMatchPattern, jobExclude.split(':'))
        if not srcPath.endswith('/'):
            srcPath = srcPath + '/'
        dstPathList = self.job['dstPath'].split(':')
        for i, dstItem in enumerate(dstPathList, start=1):
            self.syncWithHave(srcPath, dstItem, spec, srcPath, dstItem, i == 1)
        self.scanFinish = True

    def _run_sync(self):
        try:
            self.sync()
        except Exception as e:
            logger = logging.getLogger()
            logger.error(
                "Job scan crashed | job_id=%s task_id=%s src=%s dst=%s err=%s",
                self.jobClient.jobId,
                self.taskId,
                self.job.get('srcPath'),
                self.job.get('dstPath'),
                str(e)
            )
            logger.exception(e)
            self.copyHook(self.job.get('srcPath'), self.job.get('dstPath'), None, None, status=7, errMsg=str(e), isPath=1)
            self.scanFinish = True

    def _run_task_submit(self):
        try:
            self.taskSubmit()
        except Exception as e:
            logger = logging.getLogger()
            logger.error(
                "Job submit loop crashed | job_id=%s task_id=%s err=%s",
                self.jobClient.jobId,
                self.taskId,
                str(e)
            )
            logger.exception(e)
            self.finalizeTask(status=6, errMsg=str(e))

    def finalizeTask(self, status=None, errMsg=None):
        with self.finalizeLock:
            if self.finalized:
                return
            self.finalized = True
        try:
            self._emit_scan_backoff_summary()
            if self.finish:
                jobMapper.addJobTaskItemMany(self.finish)
            if status is None:
                self.updateTaskStatus()
            else:
                self.getCurrent()
                taskService.updateJobTaskStatus(
                    self.taskId,
                    status,
                    errMsg,
                    taskList=self.currentTasks,
                    createTime=self.createTime
                )
        except Exception as finalize_error:
            logger = logging.getLogger()
            logger.error(
                "Job finalize failed | job_id=%s task_id=%s status=%s err=%s",
                self.jobClient.jobId,
                self.taskId,
                status,
                str(finalize_error)
            )
            logger.exception(finalize_error)
            try:
                fallback_status = 6 if status is None else status
                taskService.updateJobTaskStatus(self.taskId, fallback_status, str(finalize_error))
            except Exception as fallback_error:
                logger.error(
                    "Job finalize fallback failed | job_id=%s task_id=%s err=%s",
                    self.jobClient.jobId,
                    self.taskId,
                    str(fallback_error)
                )
                logger.exception(fallback_error)
        finally:
            self.jobClient.jobDoing = False
            self.jobClient.currentJobTask = None

    def copyFile(self, srcPath, dstPath, fileName, fileSize):
        if self.breakFlag:
            return
        self.waiting.append(CopyItem(srcPath, dstPath, fileName, fileSize, self.job['method'], self))

    def delFile(self, path, fileName, size):
        if self.breakFlag:
            return
        isPath = fileName.endswith('/')
        status = 2
        errMsg = None
        createTime = int(time.time())
        try:
            self.openlistClient.deleteFile(path, [fileName if not isPath else fileName[:-1]], self.job['scanIntervalT'])
        except Exception as e:
            status = 7
            errMsg = str(e)
        self.delHook(path, fileName, None if isPath else size, status, errMsg, isPath, createTime)

    def listDir(self, path, firstDst, spec, rootPath, isSrc=True):
        useCache = 1 if isSrc and not firstDst else self.job[f"useCache{'S' if isSrc else 'T'}"]
        scanInterval = self.job[f"scanInterval{'S' if isSrc else 'T'}"]
        backoff_msg = self._check_scan_backoff(path, isSrc)
        if backoff_msg is not None:
            self._log_scan_backoff_skip(path, rootPath, isSrc, useCache, scanInterval, backoff_msg)
            return {}
        try:
            result = self.openlistClient.fileListApi(path, useCache, scanInterval, spec, rootPath)
            self._clear_scan_backoff(path, isSrc)
            return result
        except Exception as e:
            logger = logging.getLogger()
            errMsg = G('scan_error').format(G('src' if isSrc else 'dst'), str(e))
            backoff_seconds = None
            backoff_count = None
            if 'timed out' in str(e).lower() or 'scan backoff active' in str(e).lower():
                if 'scan backoff active' not in str(e).lower():
                    backoff_seconds, backoff_count = self._record_scan_backoff(path, isSrc)
            logger.error(
                "%s | job_id=%s task_id=%s openlist_id=%s is_src=%s path=%s root_path=%s use_cache=%s scan_interval=%s backoff_seconds=%s backoff_count=%s",
                errMsg,
                self.jobClient.jobId,
                self.taskId,
                self.job.get('openlistId'),
                isSrc,
                path,
                rootPath,
                useCache,
                scanInterval,
                backoff_seconds,
                backoff_count
            )
            logger.exception(e)
            self.copyHook(path if isSrc else None, None if isSrc else path, None, None, status=7, errMsg=errMsg,
                          isPath=1)
            raise e

    def syncWithHave(self, srcPath, dstPath, spec, srcRootPath, dstRootPath, firstDst):
        if self.breakFlag:
            return
        try:
            srcFiles = self.listDir(srcPath, firstDst, spec, srcRootPath)
            dstFiles = self.listDir(dstPath, firstDst, spec, dstRootPath, False)
        except Exception:
            return
        for key in srcFiles.keys():
            if not key.endswith('/'):
                if key not in dstFiles or dstFiles[key] != srcFiles[key]:
                    self.copyFile(srcPath, dstPath, key, srcFiles[key])
            else:
                if key not in dstFiles:
                    self.syncWithOutHave(srcPath + key, dstPath + key, spec, srcRootPath, dstRootPath, firstDst)
                else:
                    self.syncWithHave(srcPath + key, dstPath + key, spec, srcRootPath, dstRootPath, firstDst)
        if self.job['method'] == 1:
            for dstKey in dstFiles.keys():
                if dstKey not in srcFiles:
                    self.delFile(dstPath, dstKey, dstFiles[dstKey])

    def syncWithOutHave(self, srcPath, dstPath, spec, srcRootPath, dstRootPath, firstDst):
        if self.breakFlag:
            return
        status = 2
        errMsg = None
        try:
            self.openlistClient.mkdir(dstPath, self.job['scanIntervalT'])
        except Exception as e:
            status = 7
            errMsg = str(e)
        self.copyHook(srcPath, dstPath, None, None, status=status, errMsg=errMsg, isPath=1)
        if status != 2:
            return
        try:
            srcFiles = self.listDir(srcPath, firstDst, spec, srcRootPath)
        except Exception:
            return
        for key in srcFiles.keys():
            if self.breakFlag:
                break
            if key.endswith('/'):
                self.syncWithOutHave(srcPath + key, dstPath + key, spec, srcRootPath, dstRootPath, firstDst)
            else:
                self.copyFile(srcPath, dstPath, key, srcFiles[key])

    def updateTaskStatus(self):
        self.getCurrent()
        failOrOtherNum = len(self.currentTasks[7]) + len(self.currentTasks[-1])
        status = 7 if self.breakFlag else 2 if failOrOtherNum == 0 else 3
        taskService.updateJobTaskStatus(self.taskId, status, taskList=self.currentTasks, createTime=self.createTime)


class JobClient:
    def __init__(self, job, isInit=False):
        addJobId = 0
        if 'enable' not in job:
            job['enable'] = 1
        if 'method' not in job:
            job['method'] = 0
        if 'id' not in job:
            addJobId = jobMapper.addJob(job)
            job = jobMapper.getJobById(addJobId)
        self.jobId = job['id']
        self.job = job
        self.scheduled = None
        self.scheduledJob = None
        self.timeWindowRunning = False
        self.timeWindowStarted = False
        self.jobDoing = False
        self.currentJobTask = None
        try:
            self.doByTime()
        except Exception as e:
            if isInit or addJobId != 0:
                logger = logging.getLogger()
                logger.error(G('del_job_course_error').format(json.dumps(self.job)))
                jobMapper.deleteJob(self.jobId)
            raise e

    def doJob(self):
        while self.jobDoing:
            if self.job['enable'] == 0:
                return
            time.sleep(10)
        self.jobDoing = True
        taskId = None
        try:
            taskId = jobMapper.addJobTask({
                'jobId': self.jobId,
                'runTime': int(time.time())
            })
            if self.job['enable'] == 0:
                raise Exception("abort")
            self.currentJobTask = JobTask(taskId, self)
        except Exception as e:
            self.jobDoing = False
            logger = logging.getLogger()
            errMsg = G('do_job_err').format(str(e))
            logger.error(errMsg)
            if taskId is not None:
                taskService.updateJobTaskStatus(taskId, 6, errMsg)
            logger.exception(e)

    def doManual(self):
        if self.jobDoing:
            raise Exception(G('job_running'))
        threading.Thread(target=self.doJob).start()

    def getTimeWindowConfig(self):
        raw_config = self.job.get('timeWindow')
        if raw_config is None or str(raw_config).strip() == '':
            return None
        if isinstance(raw_config, dict):
            return raw_config
        try:
            return json.loads(raw_config)
        except Exception as e:
            raise Exception(f"timeWindow配置错误: {str(e)}")

    def parseWindowMinute(self, value, field_name):
        if value is None or str(value).strip() == '':
            raise Exception(f"时间窗{field_name}不能为空")
        value = str(value).strip()
        if ':' not in value:
            raise Exception(f"时间窗{field_name}格式应为HH:mm")
        hour, minute = value.split(':', 1)
        hour = int(hour)
        minute = int(minute)
        if hour < 0 or hour > 24 or minute < 0 or minute > 59:
            raise Exception(f"时间窗{field_name}超出范围")
        if hour == 24 and minute != 0:
            raise Exception(f"时间窗{field_name}的24点时分必须为0")
        return hour * 60 + minute

    def getSelectedWindowDays(self, config):
        mode = config.get('mode', 'daily')
        if mode == 'daily':
            return set(range(7))
        days = config.get('days', [])
        if mode == 'day':
            days = config.get('daysOfMonth', days)
        selected = set()
        for item in days:
            try:
                selected.add(int(item))
            except Exception:
                continue
        return selected

    def windowDayMatches(self, config, dt):
        mode = config.get('mode', 'daily')
        if mode == 'daily':
            return True
        selected = self.getSelectedWindowDays(config)
        if mode == 'week':
            return dt.weekday() in selected
        if mode == 'day':
            return dt.day in selected
        return False

    def timeWindowActive(self, dt=None):
        config = self.getTimeWindowConfig()
        if config is None:
            raise Exception('timeWindow配置不能为空')
        windows = config.get('ranges', [])
        if not windows:
            raise Exception('时间窗至少需要一个时间段')
        if dt is None:
            dt = datetime.datetime.now()
        minute_of_day = dt.hour * 60 + dt.minute
        previous_day = dt - datetime.timedelta(days=1)
        for item in windows:
            start = self.parseWindowMinute(item.get('start'), '开始时间')
            end = self.parseWindowMinute(item.get('end'), '结束时间')
            if start == end:
                continue
            if start < end:
                if self.windowDayMatches(config, dt) and start <= minute_of_day < end:
                    return True
            else:
                if self.windowDayMatches(config, dt) and start <= minute_of_day < 24 * 60:
                    return True
                if self.windowDayMatches(config, previous_day) and 0 <= minute_of_day < end:
                    return True
        return False

    def doTimeWindowCheck(self):
        if self.job['enable'] == 0:
            if self.currentJobTask:
                self.currentJobTask.breakFlag = True
            self.timeWindowRunning = False
            self.timeWindowStarted = False
            return
        active = self.timeWindowActive()
        if active:
            self.timeWindowRunning = True
            if not self.timeWindowStarted:
                self.timeWindowStarted = True
                if not self.jobDoing:
                    self.doManual()
        else:
            self.timeWindowRunning = False
            self.timeWindowStarted = False
            if self.currentJobTask:
                self.currentJobTask.breakFlag = True

    def doByTime(self):
        params = {
            'func': self.doJob,
            'misfire_grace_time': 15 * 60,
            'trigger': 'interval' if self.job['isCron'] in [0, 3] else 'cron'
        }
        if self.job['isCron'] == 0:
            interval = self.job['interval']
            if interval is not None and str(interval).strip() != '':
                params['minutes'] = interval
            else:
                raise Exception(G('interval_lost'))
        elif self.job['isCron'] == 1:
            flag = 0
            for item in ['year', 'month', 'day', 'week', 'day_of_week', 'hour', 'minute', 'second', 'start_date',
                         'end_date']:
                if item in self.job and self.job[item] is not None and self.job[item] != '':
                    flag += 1
                    params[item] = self.job[item]
            if flag == 0:
                raise Exception(G('cron_lost'))
        elif self.job['isCron'] == 3:
            self.timeWindowActive()
            params['func'] = self.doTimeWindowCheck
            params['minutes'] = 1
            params['next_run_time'] = datetime.datetime.now()
        else:
            return
        self.scheduled = BackgroundScheduler()
        self.scheduledJob = self.scheduled.add_job(**params)
        self.scheduled.start()
        if self.job['enable'] == 0:
            self.scheduledJob.pause()

    def resumeJob(self):
        if self.scheduledJob is None:
            raise Exception(G('cannot_resume_lost_job'))
        jobMapper.updateJobEnable(self.jobId, 1)
        self.job['enable'] = 1
        self.scheduledJob.resume()

    def abortJob(self):
        if self.currentJobTask:
            self.currentJobTask.breakFlag = True

    def stopJob(self, remove=False):
        self.job['enable'] = 0
        if self.currentJobTask:
            self.currentJobTask.breakFlag = True
        if remove:
            if self.scheduled is not None:
                try:
                    self.scheduled.shutdown(wait=False)
                except Exception as e:
                    logger = logging.getLogger()
                    logger.warning(G('stop_fail').format(str(e)))
                    logger.exception(e)
                self.scheduled = None
        else:
            if self.scheduledJob is not None:
                try:
                    self.scheduledJob.pause()
                except Exception as e:
                    logger = logging.getLogger()
                    logger.warning(G('disable_fail').format(str(e)))
                    logger.exception(e)
        self.jobDoing = False
        if not remove:
            jobMapper.updateJobEnable(self.jobId, 0)
            jobMapper.updateJobTaskStatusByStatusAndJobId(self.jobId)
