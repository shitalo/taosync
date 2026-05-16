from common import sqlBase
from common.LNG import G

# 鐢ㄦ埛鍒楄〃锛宬ey涓簎Id-{user_list.id}锛寁alue涓虹敤鎴峰瓧鍏?
users = {}


def getUserByName(name):
    global users
    for item in users.keys():
        if users[item]['userName'] == name:
            return users[item]
    userList = sqlBase.fetchall_to_table("select * from user_list where userName = ?", (name,))
    if userList:
        user = userList[0]
        users[f"uId-{user['id']}"] = user
        return user
    else:
        raise Exception(G('user_not_found'))


def getUserById(userId):
    userKey = f"uId-{userId}"
    global users
    if userKey in users:
        return users[userKey]
    userList = sqlBase.fetchall_to_table("select * from user_list where id = ?", (userId,))
    if userList:
        user = userList[0]
        users[f"uId-{user['id']}"] = user
        return user
    else:
        raise Exception(G('user_not_found'))


def resetPasswd(userId, passwd):
    userKey = f"uId-{userId}"
    global users
    if userKey in users:
        users[userKey]['passwd'] = passwd
    sqlBase.execute_update("update user_list set passwd = ? where id = ?", (passwd, userId))

