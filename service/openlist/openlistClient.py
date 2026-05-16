"""
@Author: dr34m
@Date: 2024/7/4 13:57
"""
import logging
import threading
import time
import uuid

import requests
from requests.adapters import HTTPAdapter

from common import commonService
from common.config import getConfig
from common.LNG import G


def checkExs(path, rts, spec):
    """
    检查并排除排除项
    :param path: 所在路径
    :param rts: 内容列表，例如
        {
            "test1-1/": {},  # key以/结尾表示目录
            "test1.txt": 4  # 不以/结尾，表示文件，存文件大小
        }
    :param spec: 排除规则
    :return: 排除后的内容列表
    """
    rtsNew = rts.copy()
    for rtsItem in rts.keys():
        if spec.match_file(path + '/' + rtsItem):
            del rtsNew[rtsItem]
    return rtsNew


class OpenListClient:
    RETRYABLE_REQS = {
        ('get', '/api/me'),
        ('post', '/api/fs/list'),
        ('post', '/api/admin/task/copy/info'),
        ('get', '/api/admin/task/copy/done'),
        ('get', '/api/admin/task/copy/undone')
    }
    _REQ_STATS_LOCK = threading.Lock()
    _REQ_STATS = {}
    _REQ_STATS_LAST_EMIT = 0.0
    _REQ_STATS_EMIT_INTERVAL = 60
    TASK_CACHE_TTL = 1.5

    def __init__(self, url, token, openlistId=None):
        """
        初始化
        :param url: 请求地址，例如'http://localhost:5244'，注意结尾不要/
        :param openlistId: 存在数据库中的id
        :param token: 登录鉴权信息
        """
        self.url = url
        self.user = None
        self.openlistId = openlistId
        self.token = token
        self._session_local = threading.local()
        self._task_cache_lock = threading.Lock()
        self._task_cache = {}
        self._task_cache_time = 0.0
        self._task_cache_refreshing = False
        self._task_cache_refresh_event = threading.Event()
        self._task_cache_refresh_event.set()
        # key-根目录，val-上次操作时间，或计划下次操作时间，用于间隔等待
        self.waits = {}
        self.getUser()

    def _create_session(self):
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _get_session(self):
        session = getattr(self._session_local, 'session', None)
        if session is None:
            session = self._create_session()
            self._session_local.session = session
        return session

    def _is_retryable_req(self, method, url):
        return (method.lower(), url) in self.RETRYABLE_REQS

    @staticmethod
    def _slow_request_threshold_ms(timeout_cfg):
        return max(3000, int(timeout_cfg[1] * 250))

    @staticmethod
    def _trim_response_text(text, limit=600):
        if text is None:
            return None
        text = text.strip()
        if len(text) > limit:
            return text[:limit] + '...(truncated)'
        return text

    @staticmethod
    def _build_timeout(url):
        cfg = getConfig()['server']
        connect_timeout = max(3, int(cfg.get('openlist_connect_timeout', 15)))
        default_read_timeout = max(5, int(cfg.get('openlist_read_timeout', 60)))
        status_read_timeout = max(5, int(cfg.get('openlist_status_timeout', 20)))
        task_list_timeout = max(5, int(cfg.get('openlist_task_list_timeout', 15)))
        if url == '/api/admin/task/copy/info':
            read_timeout = status_read_timeout
        elif url in ['/api/admin/task/copy/undone', '/api/admin/task/copy/done']:
            read_timeout = task_list_timeout
        else:
            read_timeout = default_read_timeout
        return connect_timeout, read_timeout

    @classmethod
    def _record_req_stat(cls, openlist_id, path, outcome, duration_ms, status_code=None, detail=None):
        now = time.time()
        emit_items = None
        with cls._REQ_STATS_LOCK:
            key = (openlist_id, path, outcome, status_code)
            item = cls._REQ_STATS.get(key)
            if item is None:
                item = {
                    'openlist_id': openlist_id,
                    'path': path,
                    'outcome': outcome,
                    'status_code': status_code,
                    'count': 0,
                    'total_duration_ms': 0,
                    'max_duration_ms': 0,
                    'first_at': now,
                    'last_at': now,
                    'sample': None
                }
                cls._REQ_STATS[key] = item
            item['count'] += 1
            item['total_duration_ms'] += duration_ms
            item['max_duration_ms'] = max(item['max_duration_ms'], duration_ms)
            item['last_at'] = now
            if detail:
                item['sample'] = str(detail)[:300]
            if now - cls._REQ_STATS_LAST_EMIT >= cls._REQ_STATS_EMIT_INTERVAL and cls._REQ_STATS:
                emit_items = list(cls._REQ_STATS.values())
                cls._REQ_STATS = {}
                cls._REQ_STATS_LAST_EMIT = now
        if emit_items:
            logger = logging.getLogger()
            for stat in emit_items:
                logger.warning(
                    "OpenList request summary | %s",
                    commonService.dump_for_log({
                        'openlist_id': stat['openlist_id'],
                        'path': stat['path'],
                        'outcome': stat['outcome'],
                        'status_code': stat['status_code'],
                        'count': stat['count'],
                        'avg_duration_ms': int(stat['total_duration_ms'] / stat['count']),
                        'max_duration_ms': stat['max_duration_ms'],
                        'window_seconds': int(stat['last_at'] - stat['first_at']) + 1,
                        'sample': stat['sample']
                    }, 1000)
                )

    @staticmethod
    def _is_transient_error(err):
        if isinstance(err, (requests.exceptions.ConnectionError, requests.exceptions.SSLError,
                            requests.exceptions.Timeout)):
            return True
        err_str = str(err)
        return any(item in err_str for item in [
            'Connection aborted',
            'Remote end closed connection without response',
            'EOF occurred in violation of protocol',
            'Connection reset by peer',
            'WinError 10054'
        ])

    def req(self, method, url, data=None, params=None):
        """
        通用请求
        :param method: get/post
        :param url: 请求地址，/api/xxx
        :param data: 需要放在请求体中用json传的数据
        :param params: 在url中的请求参数
        :return: 200返回res['data']，401自动登录后重试，失败抛出异常
        """
        res = {
            'code': 500,
            'message': None,
            'data': None
        }
        headers = None
        if self.token is not None:
            headers = {
                'Authorization': self.token
            }
        logger = logging.getLogger()
        req_id = uuid.uuid4().hex[:8]
        req_log = {
            'req_id': req_id,
            'openlist_id': self.openlistId,
            'method': method.upper(),
            'url': self.url + url,
            'path': url,
            'params': params,
            'json': data
        }
        timeout_cfg = self._build_timeout(url)
        req_times = 3 if self._is_retryable_req(method, url) else 1
        for req_num in range(req_times):
            start_at = time.time()
            try:
                r = self._get_session().request(method, self.url + url, json=data, params=params, headers=headers,
                                                timeout=timeout_cfg)
                duration_ms = int((time.time() - start_at) * 1000)
                response_preview = self._trim_response_text(getattr(r, 'text', None))
                logger.info(
                    "OpenList request ok | %s | attempt=%s/%s status=%s duration_ms=%s timeout=%s response=%s",
                    commonService.dump_for_log(req_log, 1200),
                    req_num + 1,
                    req_times,
                    r.status_code,
                    duration_ms,
                    timeout_cfg,
                    commonService.dump_for_log(response_preview, 800)
                )
                if r.status_code == 200:
                    self._record_req_stat(self.openlistId, url, 'ok', duration_ms, status_code=r.status_code)
                    if duration_ms >= self._slow_request_threshold_ms(timeout_cfg):
                        logger.warning(
                            "OpenList request slow | %s | status=%s duration_ms=%s timeout=%s",
                            commonService.dump_for_log(req_log, 1200),
                            r.status_code,
                            duration_ms,
                            timeout_cfg
                        )
                        self._record_req_stat(self.openlistId, url, 'slow', duration_ms, status_code=r.status_code)
                else:
                    self._record_req_stat(
                        self.openlistId, url, 'http_error', duration_ms, status_code=r.status_code, detail=response_preview
                    )
                if r.status_code == 200:
                    res = r.json()
                else:
                    res['code'] = r.status_code
                    res['message'] = response_preview if response_preview else G('code_not_200')
                break
            except Exception as e:
                duration_ms = int((time.time() - start_at) * 1000)
                logger.warning(
                    "OpenList request exception | %s | attempt=%s/%s duration_ms=%s timeout=%s err=%s",
                    commonService.dump_for_log(req_log, 1200),
                    req_num + 1,
                    req_times,
                    duration_ms,
                    timeout_cfg,
                    str(e)
                )
                self._record_req_stat(self.openlistId, url, 'exception', duration_ms, detail=str(e))
                if 'Invalid URL' in str(e):
                    raise Exception(G('address_incorrect'))
                if req_num + 1 >= req_times or not self._is_transient_error(e):
                    if 'Max retries' in str(e):
                        raise Exception(G('openlist_connect_fail'))
                    raise Exception(e)
                time.sleep(0.4 * (req_num + 1))
        if res['code'] != 200:
            if res['code'] == 401:
                raise Exception(G('openlist_un_auth'))
            raise Exception(G('openlist_fail_code_reason').format(res['code'], res['message']))
        return res['data']

    def post(self, url, data=None, params=None):
        """
        发送post请求
        :param url: 请求地址，/api/xxx
        :param data: 需要放在请求体中用json传的数据
        :param params: 放在url中的请求参数
        :return: 200返回res['data']，401自动登录后重试，失败抛出异常
        """
        return self.req('post', url, data, params)

    def get(self, url, params=None):
        """
        发送get请求
        :param url: 请求地址，/api/xxx
        :param params: 放在url中的请求参数
        :return: 200返回res['data']，401自动登录后重试，失败抛出异常
        """
        return self.req('get', url, params=params)

    def getUser(self):
        """
        获取当前用户
        :return:
        """
        self.user = self.get('/api/me')['username']

    def updateOpenListId(self, openlistId):
        """
        更新openlistId
        :param openlistId:
        :return:
        """
        self.openlistId = openlistId

    def checkWait(self, path, scanInterval=0):
        """
        检查是否等待
        :param path: 路径
        :param scanInterval: 间隔
        :return:
        """
        if scanInterval != 0:
            pathFirst = path.split('/', maxsplit=2)[1]
            if pathFirst in self.waits:
                timeC = time.time() - self.waits[pathFirst]
                if timeC < scanInterval:
                    self.waits[pathFirst] = time.time() + timeC
                    time.sleep(scanInterval - timeC)
                    return
            self.waits[pathFirst] = time.time()

    def fileListApi(self, path, useCache=0, scanInterval=0, spec=None, rootPath=None):
        """
        目录列表
        :param path: 目录，以/开头并以/结尾
        :param useCache: 是否使用缓存，0-不使用，1-使用
        :param scanInterval: 目录扫描间隔，单位秒
        :param spec: 排除项规则
        :return: {
            "test1-1/": {},  # key以/结尾表示目录
            "test1.txt": 4  # 不以/结尾，表示文件，存文件大小
        }
        :param rootPath: 同步根目录
        """
        self.checkWait(path, scanInterval)
        res = self.post('/api/fs/list', data={
            'path': path,
            'refresh': useCache != 1
        })['content']
        if res is not None:
            rts = {
                f"{item['name']}/" if item['is_dir'] else item['name']: {} if item['is_dir']
                else item['size'] for item in res
            }
        else:
            rts = {}
        if spec and rts:
            if rootPath is None:
                rootPath = path
            rts = checkExs(path[len(rootPath):], rts, spec)
        return rts

    def filePathList(self, path):
        """
        通过路径获取其下路径列表
        :param path:
        :return:
        """
        res = self.post('/api/fs/list', data={
            'path': path,
            'refresh': True
        })['content']
        if res is not None:
            return [{'path': item['name']} for item in res if item['is_dir']]
        else:
            return []

    def allFileList(self, path, useCache=0, scanInterval=0, spec=None, rootPath=None):
        """
        递归获取文件列表，暂时弃用
        :param path: 根路径
        :param useCache: 是否使用缓存，0-不使用，1-使用
        :param scanInterval: 目录扫描间隔，单位秒
        :param spec: 排除项规则
        :param rootPath: 同步根目录
        :return: {
            "test1-1/": {
                "test1-3/": {
                    "test1.txt": 4
                },
                "test1.txt": 4
            },
            "test1.txt": 4
        }
        """
        if rootPath is None:
            rootPath = path
        fList = self.fileListApi(path, useCache, scanInterval, spec, rootPath)
        for key in fList.keys():
            if key.endswith('/'):
                fList[key] = self.allFileList(f"{path}/{key[:-1]}", useCache, scanInterval, spec, rootPath)
        return fList

    def mkdir(self, path, scanInterval=0):
        """
        创建目录
        :param path: 路径
        :param scanInterval:
        """
        self.checkWait(path, scanInterval)
        return self.post('/api/fs/mkdir', data={
            'path': path
        })

    def deleteFile(self, path, names, scanInterval=0):
        """
        删除文件或目录
        :param path: 路径
        :param names: 文件/目录名，列表
        :param scanInterval:
        """
        self.checkWait(path, scanInterval)
        self.post('/api/fs/remove', data={
            'names': names,
            'dir': path
        })

    def copyFile(self, srcDir, dstDir, name):
        """
        复制文件
        :param srcDir: 源目录
        :param dstDir: 目标目录
        :param name: 文件名
        :return: 任务id
        """
        tasks = self.post('/api/fs/copy', data={
            'src_dir': srcDir,
            'dst_dir': dstDir,
            'overwrite': True,
            'names': [
                name
            ]
        })['tasks']
        if tasks:
            return tasks[0]['id']
        else:
            return None

    def moveFile(self, srcDir, dstDir, name):
        """
        移动文件
        :param srcDir: 源目录
        :param dstDir: 目标目录
        :param name: 文件名
        :return: 任务id
        """
        tasks = self.post('/api/fs/move', data={
            'src_dir': srcDir,
            'dst_dir': dstDir,
            'overwrite': True,
            'names': [
                name
            ]
        })['tasks']
        if tasks:
            return tasks[0]['id']
        else:
            return None

    def taskInfo(self, taskId):
        """
        任务详情
        :param taskId: 任务id
        :return: {
            "id": "26GQSD1mZHDlDq1V1Lf7G",
            "name": "copy [/test1](/test1/test1.txt) to [/test2](/)",
            "state": 2, # 0-等待中，1-进行中，2-成功
            "status": "getting src object",
            "progress": 0, # 进度
            "error": ""
        }
        """
        return self.post('/api/admin/task/copy/info', params={
            'tid': taskId
        })

    def refreshTaskCache(self, force=False):
        now = time.time()
        with self._task_cache_lock:
            old_cache = self._task_cache.copy()
            old_cache_time = self._task_cache_time
            if not force and now - self._task_cache_time < self.TASK_CACHE_TTL and self._task_cache:
                return self._task_cache
            if self._task_cache_refreshing:
                refresh_event = self._task_cache_refresh_event
            else:
                self._task_cache_refreshing = True
                self._task_cache_refresh_event.clear()
                refresh_event = None
        if refresh_event is not None:
            refresh_event.wait(timeout=self._build_timeout('/api/admin/task/copy/undone')[1] + 2)
            with self._task_cache_lock:
                return self._task_cache
        task_cache = {}
        try:
            for taskItem in self.copyTaskUnDone():
                task_cache[taskItem['id']] = taskItem
        except Exception:
            with self._task_cache_lock:
                self._task_cache = old_cache
                self._task_cache_time = old_cache_time
                self._task_cache_refreshing = False
                self._task_cache_refresh_event.set()
            raise
        finally:
            if self._task_cache_refreshing:
                with self._task_cache_lock:
                    self._task_cache_refreshing = False
                    self._task_cache_refresh_event.set()
        if force:
            for taskItem in self.copyTaskDone():
                task_cache[taskItem['id']] = taskItem
        with self._task_cache_lock:
            self._task_cache = task_cache
            self._task_cache_time = now
            return self._task_cache

    def taskInfoCached(self, taskId, force=False):
        task_cache = self.refreshTaskCache(force=force)
        return task_cache.get(taskId)

    def taskInfoByLists(self, taskId):
        """
        閫氳繃宸插畬鎴愬拰鏈畬鎴愪换鍔″垪琛ㄥ洖鎺ㄤ换鍔＄姸鎬?
        :param taskId: 浠诲姟id
        :return:
        """
        return self.taskInfoCached(taskId, force=True)

    def copyTaskDone(self):
        """
        已完成的复制任务
        :return: [{
            "id": "26GQSD1mZHDlDq1V1Lf7G",
            "name": "copy [/test1](/test1/test1.txt) to [/test2](/)",
            "state": 2, # 0-等待中，1-进行中，2-成功
            "status": "getting src object",
            "progress": 0, # 进度
            "error": ""
        }]
        """
        return self.get('/api/admin/task/copy/done')

    def copyTaskUnDone(self):
        """
        未完成的复制任务
        :return: [{
            "id": "26GQSD1mZHDlDq1V1Lf7G",
            "name": "copy [/test1](/test1/test1.txt) to [/test2](/)",
            "state": 1, # 0-等待中，1-进行中，2-成功
            "status": "getting src object",
            "progress": 0, # 进度
            "error": ""
        }]
        """
        return self.get('/api/admin/task/copy/undone')

    def copyTaskRetry(self, taskId):
        """
        重试复制任务
        :param taskId: 任务id
        """
        self.post('/api/admin/task/copy/retry', params={
            'tid': taskId
        })

    def copyTaskClearSucceeded(self):
        """
        清除已成功的复制任务
        """
        self.post('/api/admin/task/copy/clear_succeeded')

    def copyTaskDelete(self, taskId):
        """
        删除复制任务
        :param taskId: 任务id
        """
        self.post('/api/admin/task/copy/delete', params={
            'tid': taskId
        })

    def copyTaskCancel(self, taskId):
        """
        取消复制任务
        :param taskId: 任务id
        """
        self.post('/api/admin/task/copy/cancel', params={
            'tid': taskId
        })
