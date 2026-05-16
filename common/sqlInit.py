from common import commonUtils
from common import sqlBase


def _table_exists(cursor, table_name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None


def _column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())


def _create_openlist_table(cursor):
    cursor.execute(
        "create table openlist_list("
        "id integer primary key autoincrement,"
        "remark text,"
        "url text,"
        "userName text,"
        "token text,"
        "createTime integer DEFAULT (strftime('%s', 'now')),"
        " unique (url, userName))"
    )


def _normalize_openlist_schema(cursor):
    # 老版本数据库迁移到 OpenList 命名
    if _table_exists(cursor, 'alist_list'):
        if not _table_exists(cursor, 'openlist_list'):
            cursor.execute("alter table alist_list rename to openlist_list")
        else:
            cursor.execute(
                "insert or ignore into openlist_list(id, remark, url, userName, token, createTime) "
                "select id, remark, url, userName, token, createTime from alist_list"
            )
            cursor.execute("drop table alist_list")

    if not _table_exists(cursor, 'openlist_list'):
        _create_openlist_table(cursor)

    if _table_exists(cursor, 'job') and _column_exists(cursor, 'job', 'alistId') and not _column_exists(cursor, 'job', 'openlistId'):
        cursor.execute("alter table job rename column alistId to openlistId")


@sqlBase.connect_sql
def init_sql(conn):
    cuVersion = 260510
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE name='user_list'")
    passwd = None
    if cursor.fetchone() is None:
        passwd = commonUtils.generatePasswd()
        cursor.execute(
            "create table user_list("
            "id integer primary key autoincrement,"
            "userName text,"
            "passwd text,"
            f"sqlVersion integer DEFAULT {cuVersion},"
            "createTime integer DEFAULT (strftime('%s', 'now'))"
            ")"
        )
        cursor.execute("insert into user_list(userName, passwd) values ('admin', ?)",
                       (commonUtils.passwd2md5(passwd),))
        _create_openlist_table(cursor)
        cursor.execute(
            "create table job("
            "id integer primary key autoincrement,"
            "enable integer DEFAULT 1,"
            "remark text,"
            "srcPath text,"
            "dstPath text,"
            "openlistId integer,"
            "useCacheT integer DEFAULT 0,"
            "scanIntervalT integer DEFAULT 0,"
            "useCacheS integer DEFAULT 0,"
            "scanIntervalS integer DEFAULT 0,"
            "method integer,"
            "interval integer,"
            "isCron integer DEFAULT 0,"
            "year text DEFAULT NULL,"
            "month text DEFAULT NULL,"
            "day text DEFAULT NULL,"
            "week text DEFAULT NULL,"
            "day_of_week text DEFAULT NULL,"
            "hour text DEFAULT NULL,"
            "minute text DEFAULT NULL,"
            "second text DEFAULT NULL,"
            "start_date text DEFAULT NULL,"
            "end_date text DEFAULT NULL,"
            "exclude text DEFAULT NULL,"
            "timeWindow text DEFAULT NULL,"
            "createTime integer DEFAULT (strftime('%s', 'now')),"
            " unique (srcPath, dstPath, openlistId))"
        )
        cursor.execute(
            "create table job_task("
            "id integer primary key autoincrement,"
            "jobId integer,"
            "status integer DEFAULT 1,"
            "errMsg text,"
            "runTime integer,"
            "taskNum text,"
            "createTime integer DEFAULT (strftime('%s', 'now'))"
            ")"
        )
        cursor.execute(
            "create table job_task_item("
            "id integer primary key autoincrement,"
            "taskId integer,"
            "srcPath text,"
            "dstPath text,"
            "isPath integer DEFAULT 0,"
            "fileName text,"
            "fileSize integer,"
            "type integer,"
            "openlistTaskId text,"
            "status integer DEFAULT 0,"
            "progress real,"
            "errMsg text,"
            "createTime integer DEFAULT (strftime('%s', 'now'))"
            ")"
        )
        cursor.execute(
            "create table notify("
            "id integer primary key autoincrement,"
            "enable integer DEFAULT 1,"
            "method integer,"
            "params text,"
            "createTime integer DEFAULT (strftime('%s', 'now'))"
            ")"
        )
        conn.commit()
    else:
        _normalize_openlist_schema(cursor)
        try:
            cursor.execute("SELECT sqlVersion FROM user_list limit 1")
            sqlVersion = cursor.fetchone()[0]
        except Exception as e:
            sqlVersion = 0
            if 'sqlVersion' not in str(e):
                import logging
                logger = logging.getLogger()
                logger.exception(e)
        if sqlVersion < cuVersion:
            if sqlVersion < 240731:
                cursor.execute(f"alter table user_list add column sqlVersion integer default {cuVersion}")
                cursor.execute("alter table job_task add column errMsg text")
            if sqlVersion < 240813:
                cursor.execute("alter table job drop column cron")
                cursor.execute("alter table job add column isCron integer DEFAULT 0")
                cursor.execute("alter table job add column year text DEFAULT NULL")
                cursor.execute("alter table job add column month text DEFAULT NULL")
                cursor.execute("alter table job add column day text DEFAULT NULL")
                cursor.execute("alter table job add column week text DEFAULT NULL")
                cursor.execute("alter table job add column day_of_week text DEFAULT NULL")
                cursor.execute("alter table job add column hour text DEFAULT NULL")
                cursor.execute("alter table job add column minute text DEFAULT NULL")
                cursor.execute("alter table job add column second text DEFAULT NULL")
                cursor.execute("alter table job add column start_date text DEFAULT NULL")
                cursor.execute("alter table job add column end_date text DEFAULT NULL")
            if sqlVersion < 240905:
                cursor.execute("alter table job add column exclude text DEFAULT NULL")
            if sqlVersion < 241014:
                cursor.execute(
                    "create table notify("
                    "id integer primary key autoincrement,"
                    "enable integer DEFAULT 1,"
                    "method integer,"
                    "params text,"
                    "createTime integer DEFAULT (strftime('%s', 'now'))"
                    ")"
                )
            if sqlVersion < 250307:
                cursor.execute("alter table job_task add column taskNum text")
            if sqlVersion < 250416:
                cursor.execute("alter table job add column remark text")
            if sqlVersion < 250520:
                cursor.execute("alter table job_task_item add column isPath integer DEFAULT 0")
            if sqlVersion < 250608:
                cursor.execute("alter table job rename column speed to useCacheT")
                cursor.execute("alter table job add column scanIntervalT integer DEFAULT 0")
                cursor.execute("alter table job add column useCacheS integer DEFAULT 0")
                cursor.execute("alter table job add column scanIntervalS integer DEFAULT 0")
                cursor.execute("update job set scanIntervalT = 10, useCacheT = 0 where useCacheT = 2")
            if sqlVersion < 260430:
                cursor.execute("alter table job add column timeWindow text DEFAULT NULL")
            if sqlVersion < 260510:
                _normalize_openlist_schema(cursor)
            cursor.execute(f"update user_list set sqlVersion={cuVersion}")
            conn.commit()
    cursor.close()
    return passwd
