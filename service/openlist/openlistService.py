import logging

from common.LNG import G
from mapper.openlistMapper import getOpenListById, addOpenList, removeOpenList, getOpenListList, updateOpenList
from service.openlist.openlistClient import OpenListClient


openlistClientList = {}


def _remove_token_field(items):
    for item in items:
        if 'token' in item:
            del item['token']


def getClientList(req=None):
    clientList = getOpenListList(req)
    if isinstance(clientList, dict):
        dataList = clientList.get('dataList', [])
        _remove_token_field(dataList)
        return clientList
    _remove_token_field(clientList)
    return clientList


def getClientById(openlistId):
    global openlistClientList
    if openlistId not in openlistClientList:
        openlist = getOpenListById(openlistId)
        openlistClientList[openlistId] = OpenListClient(openlist['url'], openlist['token'], openlistId)
    return openlistClientList[openlistId]


def updateClient(openlist):
    openlistId = openlist['id']
    if openlist['remark'] is not None and openlist['remark'].strip() == '':
        openlist['remark'] = None
    if 'token' in openlist:
        if openlist['token'] is None:
            del openlist['token']
        else:
            openlist['token'] = openlist['token'].strip()
            if openlist['token'] == '':
                del openlist['token']
    if openlist['url'].endswith('/'):
        openlist['url'] = openlist['url'][:-1]

    openlistOld = getOpenListById(openlistId)
    if openlistOld['url'] != openlist['url'] or 'token' in openlist:
        if 'token' not in openlist:
            raise Exception(G('without_token'))
        client = OpenListClient(openlist['url'], openlist['token'], openlistId)
        openlistClientList[openlistId] = client

    updateOpenList(openlist)


def addClient(openlist):
    if openlist['remark'] is not None and openlist['remark'].strip() == '':
        openlist['remark'] = None
    if openlist['url'].endswith('/'):
        openlist['url'] = openlist['url'][:-1]
    try:
        client = OpenListClient(openlist['url'], openlist['token'])
        openlistId = addOpenList({
            'remark': openlist['remark'],
            'url': openlist['url'],
            'userName': client.user,
            'token': openlist['token']
        })
        client.updateOpenListId(openlistId)
    except Exception as e:
        logger = logging.getLogger()
        logger.error(G('add_openlist_client_fail').format(str(e)))
        raise Exception(e)
    else:
        global openlistClientList
        openlistClientList[openlistId] = client


def removeClient(openlistId):
    global openlistClientList
    if openlistId in openlistClientList:
        del openlistClientList[openlistId]
    removeOpenList(openlistId)


def getChildPath(openlistId, path):
    client = getClientById(openlistId)
    return client.filePathList(path)
