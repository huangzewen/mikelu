# -*- coding: utf-8 -*-

import json
from re import sub
import requests
from celery.task import task
from wxclient import getaccess_token



# 异步发消息给用户
def send_device_voice(openid, media_id):
    url = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=' + getaccess_token()['access_token']
    data = {
        "msgtype": "voice",
        "touser": openid,
        "voice": {
            "media_id": 'replacement'
        }
    }
    data = json.dumps(data)
    headers = {
        'Accept': 'application/json, */*; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    data = sub('replacement', media_id.encode('utf-8'), data)
    re = requests.post(url=url, data=data, headers=headers)
    return json.dumps(re.text)


@task
def send_voice_asyn(openid, mediaid):
    send_device_voice(openid, mediaid)
