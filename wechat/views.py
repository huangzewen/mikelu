# -*- coding: utf-8 -*-
import ConfigParser
import json
from collections import namedtuple
from datetime import datetime
from re import sub
import time
import requests
from django.http import HttpResponse
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from wechatpy import parse_message
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.replies import TextReply, ArticlesReply, ImageReply
from wechatpy.utils import check_signature

from MQTTClient.mqttclent import publisher
from asynctasks.tasks.commands import send_voice_asyn
from database.models import Device, Enduser, Collection, Collection_Music
from wechat.models import SendMessage
from wechat.serializers import DeviceVoiceSerializer, GetUnreadmessageSerializer, NotificationreadSerializer, \
    GetAliAuthcodeSerializer, DeviceRegisterSerializer, Collection_MusicSerializer, CollectionModelSerializer, \
    Collection_MusicModelSerializer
from wxclient import getuserinfo, getaccess_token, getusergroupbyfog, \
    getdevicelistbyfog, getdeviceidfromfog, getaliauthcode, sign_ali, cunbind

cp = ConfigParser.SafeConfigParser()
cp.read('settings.conf')

TOKEN = cp.get('wechat', 'TOKEN')

FOGPATH = cp.get('FOG', 'FOGPATH')
VERSION = cp.get('VERSION', 'version')
ENDPOINT = cp.get("MQTTINFO", "ENDPOINT")

APPKEY = cp.get('AliAI', 'APPKEY')

PRODUCT_BULB = cp.get('FOG', 'PRODUCT_BULB')
PRODUCT_STORY = cp.get('FOG', 'PRODUCT_STORY')
VERSION = cp.get('VERSION', 'version')


def is_json(data):
    try:
        json.loads(data)
        return True
    except ValueError:
        return False


def sendusermessage(devicelist, commands):
    for fog_device_id in devicelist:
        publisher.MQTT_PublishMessage(
            ENDPOINT + "/" + fog_device_id['fog_product_id'] + "/%s/command/json" % fog_device_id['fog_device_id'],
            commands)


# 发送文本消息
def send_text(openid, msg):
    url = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=' + getaccess_token()['access_token']
    data = {
        "msgtype": "text",
        "touser": openid,
        "text": {
            "content": 'replacement'
        }
    }
    data = json.dumps(data)
    headers = {
        'Accept': 'application/json, */*; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    data = sub('replacement', msg.encode('utf-8'), data)
    re = requests.post(url=url, data=data, headers=headers)
    return re.text


# 发送语音给设备
def send_user_message(openid, devicelist, media_id):
    commands = {"commands": {"media_id": media_id, "message_type": "wechat_voice"}, "open_id": "openid"}
    commands = json.dumps(commands)
    sendusermessage(devicelist, commands)
    for device in devicelist:
        s = SendMessage()
        s.device_id = device['wx_device_id']
        s.open_id = openid
        s.media_id = media_id
        s.save()
    return 'ok'


# 发送语音给用户
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


def getqrcode(deviceid):
    url = FOGPATH + '/wechat/qrcode/'
    para = {
        'wx_device_id': deviceid
    }
    response = requests.get(url=url, params=para, verify=False)
    data = json.loads(response.text)
    return data


# fog绑定
def bind(msg):
    wx_device_id = msg.device_id
    open_id = msg.open_id
    wx_wechatoriginalid = msg.device_type
    userinfo = getuserinfo(open_id)
    userinfo = json.dumps(userinfo)
    url = FOGPATH + '/wechat/bind/'
    data = {"wx_device_id": wx_device_id, "originalid": wx_wechatoriginalid, "open_id": open_id, "userinfo": userinfo}
    response = requests.post(url, data=data, verify=False)
    fog_response = json.loads(response.text)
    if not Enduser.objects.filter(open_id=open_id):
        en = Enduser()
        en.fog_enduser_id = fog_response['data']['fog_enduser_id']
        en.open_id = open_id
        en.fog_product_id = fog_response['data']['fog_product_id']
        en.save()
    try:
        device = Device.objects.get(wx_device_id=wx_device_id)
        device.note = fog_response['data']['devicename']
        device.fog_product_id = fog_response['data']['fog_product_id']
        device.save()
    except Device.DoesNotExist:
        device = Device()
        device.note = fog_response['data']['devicename']
        device.fog_product_id = fog_response['data']['fog_product_id']
        device.fog_device_id = fog_response['data']['fog_device_id']
        device.wx_device_id = wx_device_id
        device.save()
    return json.loads(response.text)


# fog解绑
def unbind(msg):
    wx_device_id = msg.device_id
    open_id = msg.open_id
    wx_wechatoriginalid = msg.device_type
    url = FOGPATH + '/wechat/unbind/'
    data = {"wx_device_id": wx_device_id, "originalid": wx_wechatoriginalid, "open_id": open_id}
    response = requests.put(url, data=data, verify=False)
    return json.loads(response.text)


# 关注回复
def subscribe(msg):
    reply = ArticlesReply(message=msg)
    reply.add_article({
        'title': '米客鹿 - 欢迎您',
        'description': '米客鹿 - 欢迎您',
        'image': 'https://mmbiz.qlogo.cn/mmbiz_png/yPLjxp6uDp30bajsBE2nR9nV5WUaI80NJ6s315CHBP0s3KvruP5pT2TesSNNTpKUiawRqdjNJpvicW1mJtS3RTnw/0?wx_fmt=png',
        'url': 'http://wxclientdev.fogcloud.io/welcome/'
    })
    reply.add_article({
        'title': '配置玩具wifi',
        'description': '配置玩具wifi',
        'image': 'https://mmbiz.qlogo.cn/mmbiz_png/yPLjxp6uDp30bajsBE2nR9nV5WUaI80NMucDbFsLF0FceUIRISpWrsnibRtfPEyEdZdEoibEP5J1gVwTQbk4vI5A/0?wx_fmt=png',
        'url': 'http://wxclientdev.fogcloud.io/wifi/'
    })
    reply.add_article({
        'title': '如何使用',
        'description': '如何使用',
        'image': 'https://mmbiz.qlogo.cn/mmbiz_png/yPLjxp6uDp30bajsBE2nR9nV5WUaI80NBLkJgCOa3lq4udulLw1F8fQhKQic2PvIlMtqQ8E8hRiaDw6MAvvrOJDw/0?wx_fmt=png',
        'url': 'http://wxclientdev.fogcloud.io/instructions/'
    })
    return reply


# 查询用户与设备是否绑定故事机
def querybind(open_id):
    dl = []
    devicelist = getdevicelistbyfog(open_id)['data']['devicelist']
    for device in devicelist:
        if device['fog_product_id'] == PRODUCT_STORY:
            dl.append(device)
        else:
            continue
    return dl


# 接收微信消息
class Wechat(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        signature = request.GET.get('signature', '')
        timestamp = request.GET.get('timestamp', '')
        nonce = request.GET.get('nonce', '')
        encrypt_type = request.GET.get('encrypt_type', 'raw')
        msg_signature = request.GET.get('msg_signature', '')
        try:
            check_signature(TOKEN, signature, timestamp, nonce)
        except InvalidSignatureException:
            # return HttpResponse({}, content_type="application/json")
            pass
        echo_str = request.GET.get('echostr', '')
        return HttpResponse(echo_str)

    def post(self, request):
        msg = parse_message(request.body)
        if hasattr(msg, 'event'):
            if msg.event == "device_subscribe_status":
                a = '<xml>\
                <ToUserName>%s</ToUserName>\
                <FromUserName>%s</FromUserName>\
                <CreateTime>%u</CreateTime>\
                <MsgType>device_status</MsgType>\
                <DeviceType>%s</DeviceType>\
                <DeviceID>%s</DeviceID>\
                <DeviceStatus>%u</DeviceStatus>\
                </xml>' % (msg.open_id, msg.target, int(time.time()), msg.target, msg.device_id, 1)
                fh = open('status.txt', 'a+')
                fh.write(a)
                fh.close()
                return HttpResponse(a)
            if msg.event == 'device_unsubscribe_status':
                a = '<xml>\
                    <ToUserName>%s</ToUserName>\
                    <FromUserName>%s</FromUserName>\
                    <CreateTime>%u</CreateTime>\
                    <MsgType>device_status</MsgType>\
                    <DeviceType>%s</DeviceType>\
                    <DeviceID>%s</DeviceID>\
                    <DeviceStatus>%u</DeviceStatus>\
                    </xml>' % (msg.open_id, msg.target, int(time.time()), msg.target, msg.device_id, 0)
                return HttpResponse(a)
            if msg.event == 'device_bind':
                # 查询用户是否绑定设备
                qbind = querybind(msg.open_id)
                if qbind:
                    for binded in qbind:
                        unbind_wx_device_id = binded['wx_device_id']
                        # 强制解绑
                        cunbind(msg.open_id, binded)
                        # fog解绑
                        data_u = namedtuple("device_id", "open_id", "device_type")
                        data_u.device_id = unbind_wx_device_id
                        data_u.open_id = msg.open_id
                        data_u.device_type = msg.device_type
                        res = unbind(data_u)
                        send_text(msg.open_id, res['meta']['message'])
                res = bind(msg)
                send_text(msg.open_id, res['meta']['message'])
                return HttpResponse()
            if msg.event == 'device_unbind':
                res = unbind(msg)
                send_text(msg.open_id, res['meta']['message'])
                return HttpResponse()
            # # 人工客服
            else:
                return HttpResponse('success')
        if msg.type == 'text':
            if msg.content == u'版本':
                reply = TextReply(content=VERSION, message=msg)
            else:
                reply = TextReply(content=u'实在抱歉，尚不支持文字交流，感谢您的关注！', message=msg)
            xml = reply.render()
            return HttpResponse(xml)
        elif msg.type == 'voice':
            openid = msg.source
            media_id = msg.media_id
            devicelist = getdevicelistbyfog(openid)['data']['devicelist']
            if devicelist:
                send_user_message(openid, devicelist, media_id)
                for device in devicelist:
                    usergroup = getusergroupbyfog(device['wx_device_id'])['data']['usergroup']
                    usergroup.remove(openid)
                    if usergroup:
                        for user in usergroup:
                            msg.source = user
                            send_voice_asyn.delay(openid=user, mediaid=media_id)
                    else:
                        continue
                return HttpResponse('success')
            else:
                reply = TextReply(content=u'您还没有绑定设备!', message=msg)
            xml = reply.render()
            return HttpResponse(xml)
        else:
            return HttpResponse('success')


# 设备通知微信服务器给用户发消息接口
class SendDeviceVoice(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = DeviceVoiceSerializer

    def post(self, request):
        ser = self.serializer_class(data=request.data)
        if ser.is_valid():
            wx_device_id = request.data['wx_device_id']
            usergroup = getusergroupbyfog(wx_device_id)['data']['usergroup']
            for open_id in usergroup:
                # 异步
                # send_voice_asyn.delay(openid=open_id, mediaid=request.data['media_id'])
                send_device_voice(openid=open_id, media_id=request.data['media_id'])
            data = request.data
            meta = {'code': 0, 'message': 'Send Voice Successful.'}
            return Response({'meta': meta, 'data': data}, status=status.HTTP_200_OK)
        else:
            data = request.data
            meta = {'code': 27077, 'message': 'Request parameter error.'}
            return Response({'meta': meta, 'data': data}, status=status.HTTP_400_BAD_REQUEST)


# 通知消息已读
class Notificationread(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = NotificationreadSerializer

    def put(self, request):
        ser = self.serializer_class(data=request.data)
        if ser.is_valid():
            wx_device_id = request.data['wx_device_id']
            media_id = request.data['media_id']
            try:
                message = SendMessage.objects.get(device_id=wx_device_id, media_id=media_id, is_readed=False)
                message.is_readed = True
                message.readedtime = datetime.now()
                message.save()
            except SendMessage.DoesNotExist:
                data = request.data
                meta = {'code': 25689, 'message': 'MediaId does not exist'}
                return Response({'meta': meta, 'data': data}, status=status.HTTP_200_OK)
            data = request.data
            meta = {'code': 0, 'message': 'Notivication read Successful'}
            return Response({'meta': meta, 'data': data}, status=status.HTTP_200_OK)
        else:
            data = request.data
            meta = {'code': 27078, 'message': 'Request parameter error.'}
            return Response({'meta': meta, 'data': data}, status=status.HTTP_200_OK)


# 获取历史消息
class GetUnreadmessage(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = GetUnreadmessageSerializer

    def get(self, request):
        try:
            wx_device_id = request.GET.get('wx_device_id')
        except:
            data = request.data
            meta = {'code': 27078, 'message': 'Request parameter error.'}
            return Response({'meta': meta, 'data': data}, status=status.HTTP_200_OK)
        message = SendMessage.objects.filter(device_id=wx_device_id, is_readed=False).order_by('-sendtime')[0:5]
        idlist = [x.id for x in message]
        SendMessage.objects.filter(device_id=wx_device_id, is_readed=False).exclude(id__in=idlist).update(
            is_readed=True, readedtime=datetime.now())
        m = []
        for x in message:
            m.append(x.media_id)
        # 反转列表 对消息排序
        data = {'media_list': m[::-1]}
        meta = {'code': 0, 'message': 'Get unread message Successful'}
        return Response({'meta': meta, 'data': data}, status=status.HTTP_200_OK)


class GetAliAuthcode(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = GetAliAuthcodeSerializer

    def get(self, request):
        ser = self.serializer_class(data=request.query_params)
        if ser.is_valid():
            wx_device_id = request.GET.get('wx_device_id')
            fog = getdeviceidfromfog(wx_device_id)
            if fog['meta']['code'] == 0:
                fog_device_id = fog['data']['fog_device_id']
                fog_product_id = fog['data']['fog_product_id']
                wx_device_id = fog['data']['wx_device_id']
                re = getaliauthcode(fog_device_id, wx_device_id, fog_product_id)
                data = {'schema': fog_product_id, 'user_id': wx_device_id,
                        'authcode': re['ailab_aicloud_device_authcode_get_response']['result']['model']}
                meta = {'code': 0, 'message': 'get authcode successful'}
                return Response({'meta': meta, 'data': data}, status=status.HTTP_200_OK)
            else:
                return Response(fog, status=status.HTTP_200_OK)
        else:
            data = request.data
            meta = {'code': 27080, 'message': ser.errors}
            return Response({'meta': meta, 'data': data}, status=status.HTTP_200_OK)


# 设备注册
class DeviceRegister(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = DeviceRegisterSerializer

    def post(self, request):
        try:
            de = Device.objects.get(fog_device_id=request.data['fog_device_id'])
            de.wx_device_id = request.data['wx_device_id']
            de.ai_device_id = request.data['ai_device_id']
            note = getdeviceidfromfog(request.data['wx_device_id'])
            if note['meta']['code'] == 0:
                de.note = note['data']['wx_device_alias']
                de.fog_product_id = note['data']['fog_product_id']
                de.save()
            else:
                data = requests.query_params
                meta = {'code': 27081, 'message': note['meta']['message']}
                return Response({'meta': meta, 'data': data}, status=status.HTTP_200_OK)
        except Device.DoesNotExist:
            de = Device()
            de.wx_device_id = request.data['wx_device_id']
            de.ai_device_id = request.data['ai_device_id']
            note = getdeviceidfromfog(requests.data['wx_device_id'])
            if note['meta']['code'] == 0:
                de.note = note['data']['wx_device_alias']
                de.fog_product_id = note['data']['fog_product_id']
                de.save()
            else:
                data = requests.query_params
                meta = {'code': 27081, 'message': note['meta']['message']}
                return Response({'meta': meta, 'data': data}, status=status.HTTP_200_OK)
        data = self.serializer_class(de).data
        meta = {'code': 0, 'message': 'successful'}
        return Response({'meta': meta, 'data': data}, status=status.HTTP_200_OK)


# 收藏相关
class Collection_MusicView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = Collection_MusicSerializer
    collectionmodel_serializer_class = CollectionModelSerializer
    collection_musicmodel_serializer_class = Collection_MusicModelSerializer

    def play(self, **kwargs):
        try:
            device = Device.objects.get(fog_device_id=kwargs['device'])
        except Device.DoesNotExist:
            return False
        url = "https://eco.taobao.com/router/rest"
        para = {
            'format': 'json',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'appkey': APPKEY,
            'app_key': APPKEY,
            'sign_method': 'md5',
            'v': '2.0',
            "method": "taobao.ailab.aicloud.open.audio.play",
            "schema": device.fog_product_id,
            "user_id": device.fog_device_id,
            "utd_id": device.fog_device_id,
            "track_id": str(kwargs['track_id']),
            "device_id": device.ai_device_id
        }
        sign = sign_ali(para)
        para['sign'] = sign
        response = requests.get(url, para, verify=False).text
        aliresponse = json.loads(response)
        return aliresponse

    def get(self, request):
        serializer = self.serializer_class(data=request.query_params)
        if serializer.is_valid():
            device = request.query_params['device']
            flag = int(request.query_params['flag'])
            collection = int(request.query_params['collection'])
            track_id = request.query_params['track_id']
            collection_count = Collection.objects.filter(device=device).count()
            if flag == 0:  # 上一首
                try:
                    collection_db = Collection.objects.get(id=collection)
                    music = Collection_Music.objects.get(collection=collection_db, track_id=track_id)
                    music = Collection_Music.objects.filter(id__lt=music.id, collection=collection_db).order_by('-id')
                    if not music:
                        music = Collection_Music.objects.filter(collection=collection_db).order_by('-id')
                except Collection.DoesNotExist:
                    data = request.query_params
                    meta = {'code': 27092, 'message': 'collection error'}
                    return Response({'data': data, 'meta': meta})
                except Collection_Music.DoesNotExist:
                    data = request.data
                    meta = {'code': 27097, 'message': 'track_id error'}
                    return Response({'data': data, 'meta': meta})
                if music:
                    music = music[0]
                    data_music = self.collection_musicmodel_serializer_class(music).data
                else:
                    data_music = 'null'
                data = self.collectionmodel_serializer_class(collection_db).data
                aliplay = self.play(device=request.query_params['device'], track_id=music.track_id)
                if not aliplay:  # todo
                    data = request.query_params
                    meta = {'code': 27098, 'message': 'play error'}
                    return Response({"data": data, 'meta': meta})
                data['music'] = data_music
                meta = {'code': 0, 'message': 'successful'}
            elif flag == 1:  # 下一首
                try:
                    collection_db = Collection.objects.get(id=collection)
                    music = Collection_Music.objects.get(collection=collection_db, track_id=track_id)
                    music = Collection_Music.objects.filter(id__gt=music.id, collection=collection_db).order_by('id')
                    if not music:
                        music = Collection_Music.objects.filter(collection=collection_db).order_by('id')
                except Collection.DoesNotExist:
                    data = request.query_params
                    meta = {'code': 27092, 'message': 'collection error'}
                    return Response({'data': data, 'meta': meta})
                except Collection_Music.DoesNotExist:
                    data = request.query_params
                    meta = {'code': 27092, 'message': 'track_id error'}
                    return Response({'data': data, 'meta': meta})
                if music:
                    music = music[0]
                    data_music = self.collection_musicmodel_serializer_class(music).data
                else:
                    data_music = 'null'
                data = self.collectionmodel_serializer_class(collection_db).data
                aliplay = self.play(device=request.query_params['device'], track_id=music.track_id)
                if not aliplay:  # todo
                    data = request.query_params
                    meta = {'code': 27098, 'message': 'play error'}
                    return Response({"data": data, 'meta': meta})
                data['music'] = data_music
                meta = {'code': 0, 'message': 'successful'}
            elif flag == 2:
                if collection == -1:  # 播放第一个收藏夹的第一首歌
                    collection_db = Collection.objects.filter(device=device).order_by('id')
                    if collection_db:
                        collection_db = collection_db[0]
                        data = self.collectionmodel_serializer_class(collection_db).data
                    else:
                        data = {'id': "null"}
                    music = Collection_Music.objects.filter(collection=collection_db).order_by('id')
                    if music:
                        music = music[0]
                        data_music = self.collection_musicmodel_serializer_class(music).data
                    else:
                        data_music = 'null'
                        data['music'] = data_music
                        data['collection_count'] = collection_count
                        meta = {'code': 27100, 'message': 'music does not exit'}
                        return Response({"data": data, 'meta': meta})
                    aliplay = self.play(device=request.query_params['device'], track_id=music.track_id)
                    if not aliplay:  # todo
                        data = request.query_params
                        meta = {'code': 27098, 'message': 'play error'}
                        return Response({"data": data, 'meta': meta})
                    data['music'] = data_music
                    meta = {'code': 0, 'message': 'successful'}
                else:
                    collection_db = Collection.objects.filter(device=device, id__gt=collection).order_by('id')
                    if collection_db:
                        collection_db = collection_db[0]
                        data = self.collectionmodel_serializer_class(collection_db).data
                    else:
                        collection_db = Collection.objects.filter(device=device).order_by('id')
                        if collection_db:
                            collection_db = collection_db[0]
                            data = self.collectionmodel_serializer_class(collection_db).data
                        else:
                            data = {'id': "null"}
                    music = Collection_Music.objects.filter(collection=collection_db).order_by('id')
                    if music:
                        music = music[0]
                        data_music = self.collection_musicmodel_serializer_class(music).data
                    else:
                        data_music = 'null'
                        data['music'] = data_music
                        data['collection_count'] = collection_count
                        meta = {'code': 27100, 'message': 'music does not exit'}
                        return Response({"data": data, 'meta': meta})
                    aliplay = self.play(device=request.query_params['device'], track_id=music.track_id)
                    if not aliplay:  # todo
                        data = request.query_params
                        meta = {'code': 27098, 'message': 'play error'}
                        return Response({"data": data, 'meta': meta})
                    data['music'] = data_music
                    meta = {'code': 0, 'message': 'successful'}
            else:
                data = request.query_params
                collection_count = -1
                meta = {'code': 27096, 'message': 'flag error'}
        else:
            data = request.query_params
            collection_count = -1
            meta = {'code': 27091, 'message': serializer.errors}
        data['collection_count'] = collection_count
        return Response({'data': data, 'meta': meta})
