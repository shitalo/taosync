"""
@Author: dr34m
@Date: 2024/7/8 16:52
"""
from common import sqlBase
from common.LNG import G


def getOpenListList(params=None):
    query = "select * from openlist_list order by createTime desc"
    if params is not None and ('pageNum' in params or 'pageSize' in params):
        return sqlBase.fetchall_to_page(query, params)
    return sqlBase.fetchall_to_table(query)


def getOpenListById(openlistId):
    rst = sqlBase.fetchall_to_table("select * from openlist_list where id=?", (openlistId,))
    if rst:
        return rst[0]
    raise Exception(G('openlist_not_found'))


def addOpenList(openlist):
    return sqlBase.execute_insert("insert into openlist_list (remark, url, userName, token) "
                                  "values (:remark, :url, :userName, :token)", openlist)


def updateOpenList(openlist):
    sqlBase.execute_update(f"update openlist_list set remark=:remark, url=:url"
                           f"{', token=:token' if 'token' in openlist else ''}"
                           f" where id=:id", openlist)


def removeOpenList(openlistId):
    sqlBase.execute_update("delete from openlist_list where id=?", (openlistId,))
