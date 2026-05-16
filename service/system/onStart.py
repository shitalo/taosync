"""
@Author: dr34m
@Date: 2024/8/16 14:26
"""
import logging
import os

from common import sqlInit, commonService
from common.config import getConfig
from service.syncJob.jobService import initJob
from service.system import logJobService


def init():
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/log'):
        os.mkdir('data/log')
    # 初始化日志
    commonService.setLogger()
    commonService.install_global_exception_logger()
    logger = logging.getLogger()
    cfg = getConfig()['server']
    logger.critical(
        "Runtime config | %s",
        commonService.dump_for_log({
            'port': cfg.get('port'),
            'expires': cfg.get('expires'),
            'log_level': cfg.get('log_level'),
            'console_level': cfg.get('console_level'),
            'log_save': cfg.get('log_save'),
            'task_save': cfg.get('task_save'),
            'task_timeout': cfg.get('task_timeout'),
            'copy_parallel': cfg.get('copy_parallel'),
            'openlist_connect_timeout': cfg.get('openlist_connect_timeout'),
            'openlist_read_timeout': cfg.get('openlist_read_timeout'),
            'openlist_status_timeout': cfg.get('openlist_status_timeout'),
            'openlist_task_list_timeout': cfg.get('openlist_task_list_timeout'),
            'status_query_fast_interval': cfg.get('status_query_fast_interval'),
            'status_query_slow_interval': cfg.get('status_query_slow_interval'),
            'scan_retry_backoff_base': cfg.get('scan_retry_backoff_base'),
            'scan_retry_backoff_max': cfg.get('scan_retry_backoff_max')
        }, 2000)
    )
    # 初始化数据库，没有则创建
    passwd = sqlInit.init_sql()
    if passwd is not None:
        msg = f"Password for admin_/_已为admin生成随机密码：{passwd}"
        logger.critical(msg)
    logger.info("初始化数据库完成_/_Initializing the database completed")
    # 启动日志文件与任务定时清理任务
    logJobService.startJob()
    # 修改异常中止状态，启动任务
    initJob()
