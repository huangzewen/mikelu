# -*- coding: utf-8 -*-


import ConfigParser
import hashlib
import json
import types
from datetime import datetime
import requests
from django.core.cache import cache
import time
from django.http import HttpResponse

from database.models import Device

cp = ConfigParser.SafeConfigParser()
cp.read('settings.conf')

SECRET = cp.get('wechat', 'SECRET')
APPID = cp.get('wechat', 'APPID')
ORIGINAL = cp.get('wechat', 'ORIGINAL')

FOGPATH = cp.get('FOG', 'FOGPATH')
APPKEY = cp.get('AliAI', 'APPKEY')
ALISECRET = cp.get('AliAI', 'SECRET')

FOG_USERNAME = cp.get('FOG', 'FOG_USERNAME')
FOG_PASSWORD = cp.get('FOG', 'FOG_PASSWORD')


# 获取access_token
def getaccess_token():
    re = {}
    token = ('TOKEN' + APPID).encode('utf-8')
    createtime = ('TOKENCREATETIME' + APPID).encode('utf-8')
    now = int(time.time())
    if not cache.get(token):
        url = 'https://api.weixin.qq.com/cgi-bin/token'
        headers = {
            'Accept': 'application/json, */*; charset=utf-8',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json;charset=UTF-8'
        }
        parm = {
            'grant_type': 'client_credential',
            'appid': APPID,
            'secret': SECRET
        }
        access_token = requests.get(url, headers=headers, params=parm)
        data = access_token.json()
        if data.has_key('access_token'):
            cache.set(token, data['access_token'], 3600)
            cache.set(createtime, now, 3600)
        else:
            cache.set(token, False, 3600)
            cache.set(createtime, now, 3600)
    re['access_token'] = cache.get(token)
    re['createtime'] = cache.get(createtime)
    return re


# 获取用户信息
def getuserinfo(openid):
    url = 'https://api.weixin.qq.com/cgi-bin/user/info'
    headers = {
        'Accept': 'application/json, */*; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    parm = {
        'access_token': getaccess_token()['access_token'],
        'openid': openid,
        'lang': 'zh_CN'
    }
    userinfo_data = requests.get(url, headers=headers, params=parm)
    return json.loads(userinfo_data.text)


# 获取用户openid  未使用
def getopenid(appid, secret, code):
    url = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    para = {
        'appid': appid,
        'secret': secret,
        'code': code,
        'grant_type': 'authorization_code'

    }
    headers = {
        'Accept': 'application/json, */*; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    userinfo_data = requests.get(url, headers=headers, params=para)
    data = json.loads(userinfo_data.text)
    if data.has_key('openid'):
        openid = data['openid']
    else:
        openid = False
    return openid


# 获取绑定用户
def getusergroup(wx_device_id):
    access_token = getaccess_token()['access_token']
    url = 'https://api.weixin.qq.com/device/get_openid'
    parm = {
        'access_token': access_token,
        'device_type': ORIGINAL,
        'device_id': wx_device_id
    }
    response = requests.get(url=url, params=parm)
    return json.loads(response.text)


# 获取绑定用户 fog
def getusergroupbyfog(wx_device_id):
    url = FOGPATH + '/wechat/getuserbydevice/'
    parm = {
        'wx_device_id': wx_device_id
    }
    response = requests.get(url=url, params=parm, verify=False)
    return json.loads(response.text)


# 获取绑定设备 fog
def getdevicelistbyfog(openid):
    url = FOGPATH + '/wechat/getdevicebyuser/'
    parm = {
        'open_id': openid
    }
    response = requests.get(url=url, params=parm, verify=False)
    return json.loads(response.text)


# 获取fog设备ID
def getdeviceidfromfog(wx_device_id):
    url = FOGPATH + '/wechat/getdeviceid/'
    parm = {
        'wx_device_id': wx_device_id
    }
    response = requests.get(url=url, params=parm, verify=False)
    return json.loads(response.text)


# 阿里签名算法
def sign_ali(data):
    print data
    asciilist = sorted(data.keys())
    parameters = "%s%s%s" % (ALISECRET,
                             str().join('%s%s' % (key.encode('utf-8'), data[key].encode('utf-8')) for key in asciilist),
                             ALISECRET)
    sign = hashlib.md5(parameters).hexdigest().upper()
    return sign


def getaliauthcode(fog_device_id, wx_device_id, fog_product_id):
    data = {
        'user_id': wx_device_id,
        'method': 'taobao.ailab.aicloud.device.authcode.get',
        'utd_id': fog_device_id,
        'format': 'json',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'appkey': APPKEY,
        'app_key': APPKEY,
        'schema': fog_product_id,
        'sign_method': 'md5',
        'v': '2.0',
    }
    sign = sign_ali(data)
    data['sign'] = sign
    url = 'http://gw.api.taobao.com/router/rest'
    response = requests.get(url=url, params=data, verify=False)
    return json.loads(response.text)


# 获取绑定设备
def getdevicelist(openid):
    url = 'https://api.weixin.qq.com/device/get_bind_device'
    parm = {
        'access_token': getaccess_token()['access_token'],
        'openid': openid
    }
    re = requests.get(url=url, params=parm).text
    return json.loads(re)


# 授权后token
def oauth2token(code):
    url = 'https://api.weixin.qq.com/sns/oauth2/access_token?'
    para = {
        'appid': APPID,
        'secret': SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    }
    response = requests.get(url=url, params=para)
    data = json.loads(response.text)
    print data
    return data


# 获取设备二维码
def getdeviceqcorde(access_token):
    url = 'https://api.weixin.qq.com/device/getqrcode'
    headers = {
        'Accept': 'application/json, */*; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    parm = {
        'access_token': access_token
    }
    qcorde = requests.get(url, headers=headers, params=parm)
    data = qcorde.json()
    return data


# 授权后获得用户信息(只能获取授权用户)
def web_getuserinfo(oauthaccess_token, openid):
    url = 'https://api.weixin.qq.com/sns/userinfo?'
    headers = {
        'Accept': 'application/json, */*; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    para = {
        'access_token': oauthaccess_token,
        'openid': openid,
        'lang': 'zh_CN'
    }
    response = requests.get(url=url, params=para, headers=headers)
    data = json.loads(response.text)
    i = 0
    for x in data:
        k = data.keys()[i]
        if type(data[k]) is types.UnicodeType:
            data[k] = data[k].encode('raw_unicode_escape')
        else:
            pass
        i = i + 1
    return data


# 生成jsapiticket
def getjsapi_ticket():
    re = {}
    ticket = 'JSAPITICKET' + APPID
    createtime = 'TICKETCREATETIME' + APPID
    now = int(time.time())
    if not cache.get(ticket):
        url = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket'
        headers = {
            'Accept': 'application/json, */*; charset=utf-8',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json;charset=UTF-8'
        }
        parm = {
            'access_token': getaccess_token()['access_token'],
            'type': 'jsapi'
        }
        re_ticket = requests.get(url, headers=headers, params=parm)
        data = re_ticket.json()
        if data.has_key('ticket'):
            cache.set(ticket, data['ticket'], 3600)
            cache.set(createtime, now, 3600)
        else:
            cache.set(ticket, False, 3600)
            cache.set(createtime, now, 3600)
    re['jsapi_ticket'] = cache.get(ticket)
    re['createtime'] = cache.get(createtime)
    return re


# 强制解绑
def cunbind(openid, device_id):
    data = {}
    # data['ticket'] = redata['ticket']
    data['device_id'] = device_id['wx_device_id']
    data['openid'] = openid
    data = json.dumps(data, ensure_ascii=False)
    url = 'https://api.weixin.qq.com/device/compel_unbind?access_token=' + getaccess_token()['access_token']
    response = requests.post(url, data)
    re = json.loads(response.text)
    return re


def get_access_token_device(request):
    token = getaccess_token()
    return HttpResponse(json.dumps(token), content_type='application/json;charset=UTF-8')


def getendusermqttinfo(fog_enduser_id):
    url = FOGPATH + '/wechat/getendusermqttinfo/'
    parm = {
        'username': FOG_USERNAME,
        'password': FOG_PASSWORD,
        'fog_enduser_id': fog_enduser_id,
    }
    response = requests.get(url=url, params=parm, verify=False)
    return json.loads(response.text)


def getdeviceinfo(wx_device_id):
    try:
        fog_device_id = Device.objects.get(wx_device_id=wx_device_id).fog_device_id
    except:
        return {'data': {'onlinestatus': False}}
    url = "https://v3devapi.fogcloud.io/v3/enduser/getDeviceInfo/"
    para = {'deviceid': fog_device_id}
    response = json.loads(requests.get(url=url, params=para, verify=False).text)
    return response
