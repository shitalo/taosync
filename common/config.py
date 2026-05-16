import configparser
import logging
import os

from common.commonUtils import generatePasswd, readOrSet

sysConfig = None


def getPasswordStr():
    """
    获取加密字符串
    :return: 加密字符串
    """
    fileName = 'data/secret.key'
    passwdStr = readOrSet(fileName, generatePasswd(256))
    return passwdStr


def getConfig():
    global sysConfig
    if sysConfig is None:
        passwdStr = getPasswordStr()
        dbname = 'data/taoSync.db'
        sCfg = {
            'port': 8023,
            'expires': 9999,
            'log_level': 1,
            'console_level': 2,
            'log_save': 7,
            'task_save': 30,
            'task_timeout': 72,
            'copy_parallel': 5,
            'openlist_connect_timeout': 15,
            'openlist_read_timeout': 60,
            'openlist_status_timeout': 30,
            'openlist_task_list_timeout': 45,
            'status_query_fast_interval': 3,
            'status_query_slow_interval': 20,
            'scan_retry_backoff_base': 60,
            'scan_retry_backoff_max': 1800
        }
        if os.path.exists('data/config.ini'):
            try:
                cfg = configparser.ConfigParser()
                cfg.read('data/config.ini', encoding='utf-8-sig')
                tao = cfg['tao']
                for keyItem in sCfg.keys():
                    if keyItem in tao:
                        sCfg[keyItem] = int(tao[keyItem])
            except Exception as e:
                logger = logging.getLogger()
                logger.error(f"配置文件读取失败，将使用默认配置_/_config.ini read error: {e}")
                logger.exception(e)
        else:
            try:
                sCfg['port'] = int(os.getenv('TAO_PORT', 8023))
                sCfg['expires'] = int(os.getenv('TAO_EXPIRES', 9999))
                sCfg['log_level'] = int(os.getenv('TAO_LOG_LEVEL', 1))
                sCfg['console_level'] = int(os.getenv('TAO_CONSOLE_LEVEL', 2))
                sCfg['log_save'] = int(os.getenv('TAO_LOG_SAVE', 7))
                sCfg['task_save'] = int(os.getenv('TAO_TASK_SAVE', 30))
                sCfg['task_timeout'] = int(os.getenv('TAO_TASK_TIMEOUT', 72))
                sCfg['copy_parallel'] = int(os.getenv('TAO_COPY_PARALLEL', 5))
                sCfg['openlist_connect_timeout'] = int(os.getenv('TAO_OPENLIST_CONNECT_TIMEOUT', 15))
                sCfg['openlist_read_timeout'] = int(os.getenv('TAO_OPENLIST_READ_TIMEOUT', 60))
                sCfg['openlist_status_timeout'] = int(os.getenv('TAO_OPENLIST_STATUS_TIMEOUT', 30))
                sCfg['openlist_task_list_timeout'] = int(os.getenv('TAO_OPENLIST_TASK_LIST_TIMEOUT', 45))
                sCfg['status_query_fast_interval'] = int(os.getenv('TAO_STATUS_QUERY_FAST_INTERVAL', 3))
                sCfg['status_query_slow_interval'] = int(os.getenv('TAO_STATUS_QUERY_SLOW_INTERVAL', 20))
                sCfg['scan_retry_backoff_base'] = int(os.getenv('TAO_SCAN_RETRY_BACKOFF_BASE', 60))
                sCfg['scan_retry_backoff_max'] = int(os.getenv('TAO_SCAN_RETRY_BACKOFF_MAX', 1800))
            except Exception as e:
                logger = logging.getLogger()
                logger.error(f"环境变量读取失败，将使用默认配置_/_ENV read error: {e}")
                logger.exception(e)
        sysConfig = {
            'db': {
                'dbname': dbname
            },
            'server': {
                'passwdStr': passwdStr,
                **sCfg
            }
        }
    return sysConfig
