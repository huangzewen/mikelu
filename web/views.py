# -*- coding: utf-8 -*-

import ConfigParser
import hashlib
import json
import random
import string

import time

import requests
from django.shortcuts import render
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from database.models import Collection_Music, Collection, Device, Enduser
from web.serializers import Collection_MusicModelSerializer, CollectionModelSerializer, CollectionDeleteSerializer, \
    DevcieModelSerializer, CollectionUpdateSerializer
from wxclient import getjsapi_ticket, getaccess_token, sign_ali, oauth2token
from datetime import datetime

cp = ConfigParser.SafeConfigParser()
cp.read('settings.conf')
PATH = cp.get('wechat', 'PATH')
APPID = cp.get('wechat', 'APPID')

APPKEY = cp.get('AliAI', 'APPKEY')


# 微信jssdk签名算法
# --------------------------------
class Sign:
    def __init__(self, url):
        jsapi_ticket = getjsapi_ticket()[
            'jsapi_ticket']
        self.ret = {
            'nonceStr': self.__create_nonce_str(),
            'jsapi_ticket': jsapi_ticket,
            'timestamp': self.__create_timestamp(),
            'url': url
        }

    def __create_nonce_str(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))

    def __create_timestamp(self):
        return int(time.time())

    def sign(self):
        string = '&'.join(['%s=%s' % (key.lower(), self.ret[key]) for key in sorted(self.ret)])
        self.ret['signature'] = hashlib.sha1(string).hexdigest()
        self.ret['access_token'] = getaccess_token()['access_token']
        # self.ret['access_token'] = ''
        return self.ret


if __name__ == '__main__':
    # 注意 URL 一定要动态获取，不能 hardcode
    sign = Sign('jsapi_ticket', 'http://fogcloud.io/')
    sign.sign()


def transition(request):
    code = request.GET.get('code')
    oauth = oauth2token(code)
    openid = oauth['openid']
    return render(request, 'transition.html', {'open_id': openid})


def wifi(request):
    product_type = request.GET.get('type', None)
    if product_type:
        if product_type == '1':
            return render(request, 'qrcode.html', {'qrcode': "images/qrcode-blub.jpg"})
        if product_type == '2':
            return render(request, 'qrcode.html', {'qrcode': "images/qrcode-story.jpg"})
    else:
        return Response({'error': -1})


class FogApi(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        data = request.data
        para = json.loads(data["para"])
        method = data["method"]
        api = data["api"]
        url = "https://api.fogcloud.io/v3/wechat/" + api + "/"
        if method == "get":
            response = requests.get(url, para, verify=False).text
        if method == "post":
            response = request.post(url=url, json=para, verify=False).text
        if method == "put":
            response = requests.put(url=url, json=para, verify=False).text
        fogresponse = json.loads(response)
        return Response(fogresponse)


class AliAudioApi(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        data = request.data
        para = {
            'format': 'json',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'appkey': APPKEY,
            'app_key': APPKEY,
            'sign_method': 'md5',
            'v': '2.0',
        }
        for re_para in data['para'].keys():
            para[re_para] = data['para'][re_para]
        sign = sign_ali(para)
        para['sign'] = sign
        method = data["method"]
        url = "https://eco.taobao.com/router/rest"
        if method == "get":
            response = requests.get(url, para, verify=False).text
        if method == "post":
            response = requests.post(url=url, json=para, verify=False).text
        if method == "put":
            response = requests.put(url=url, json=para, verify=False).text
        aliresponse = json.loads(response)
        return Response(aliresponse)


class CollectionView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    CollectionModelserializer_class = CollectionModelSerializer
    CollectionUpdeteserializer_class = CollectionUpdateSerializer
    Collection_MusicModelserializer_class = Collection_MusicModelSerializer

    def post(self, request):
        serializer = self.CollectionModelserializer_class(data=request.data)
        if serializer.is_valid():
            device = request.data['device']
            collection_count = Collection.objects.filter(device=device).count()
            if collection_count >= 3:
                data = request.data
                meta = {"code": 27086, 'message': 'There are already three collection list'}
                return Response({'data': data, 'meta': meta})
            serializer.save()
            data = serializer.data
            meta = {'code': 0, 'message': 'successful'}
        else:
            data = request.data
            meta = {'code': 27082, 'meta': serializer.errors}
        return Response({'data': data, 'meta': meta})

    def get(self, request):
        deviceid = request.query_params.get('device', None)
        if deviceid:
            collections = self.CollectionModelserializer_class(Collection.objects.filter(device=deviceid),
                                                               many=True).data
            i = 0
            for collection in collections:
                musiclist = self.Collection_MusicModelserializer_class(
                    Collection_Music.objects.filter(collection=collection['id']), many=True).data
                collections[i]['music_list'] = musiclist
                i = i + 1
            data = collections
            meta = {'code': 0, 'message': 'successful'}
        else:
            data = request.query_params
            meta = {'code': 27087, 'message': "There is none collection of this device"}
        return Response({'data': data, 'meta': meta})

    def put(self, request):
        serializer = self.CollectionUpdeteserializer_class(data=request.data)
        if serializer.is_valid():
            id = request.data['id']
            name = request.data['name']
            device = request.data['device']
            try:
                de = Collection.objects.get(device=device, id=id)
                de.name = name
                de.save()
                data = self.CollectionUpdeteserializer_class(de).data
                meta = {"code": 0, 'message': "successfi;"}
            except Collection.DoesNotExist:
                data = request.data
                meta = {'code': 28103, 'message': 'collection does not exit'}
        else:
            data = request.data
            meta = {'code': 28102, 'message': serializer.errors}
        return Response({'data': data, 'meta': meta})

    def delete(self, request):
        device = request.query_params.get('device', None)
        collection_id = request.query_params.get('id', None)
        if device and id:
            try:
                cl = Collection.objects.get(device=device, id=collection_id)
                cl.delete()
                data = request.query_params
                meta = {'code': 0, 'message': "successful"}
            except Collection.DoesNotExist:
                data = request.data
                meta = {'code': 28103, 'message': 'collection does not exit'}
        else:
            data = request.query_params
            meta = {'code': 28104, 'message': 'params error'}
        return Response({'data': data, 'meta': meta})


class Collection_MusicView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    serializer_class = Collection_MusicModelSerializer
    delete_serializer_class = CollectionDeleteSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            collection = Collection.objects.get(id=request.data['collection'])
            collection.count = collection.count + 1
            try:
                Collection_Music.objects.get(track_id=request.data['track_id'], collection=request.data['collection'])
                data = request.data
                meta = {'code': 27088, 'message': 'This music was collected'}
                return Response({'data': data, 'meta': meta})
            except Collection_Music.MultipleObjectsReturned:
                data = request.data
                meta = {'code': 27089, 'message': 'database error'}
                return Response({'data': data, 'meta': meta})
            except Collection_Music.DoesNotExist:
                pass
            collection.save()
            serializer.save()
            data = serializer.data
            meta = {'code': 0, 'message': 'successful'}
        else:
            data = request.data
            meta = {'code': 27083, 'message': serializer.errors}
        return Response({'data': data, 'meta': meta})

    def delete(self, request):
        serializer = self.delete_serializer_class(data=request.query_params)
        if serializer.is_valid():
            collection_id = request.query_params['collection']
            track_id = request.query_params['track_id']
            try:
                collection_music = Collection_Music.objects.get(collection=collection_id, track_id=track_id)
                collection_music.delete()
                collect = Collection.objects.get(id=collection_id)
                collect.count = collect.count - 1
                collect.save()
                data = request.query_params
                meta = {'code': 0, 'message': 'successful'}
            except Collection_Music.DoesNotExist:
                data = request.query_params
                meta = {'code': 27084, 'message': 'music does not be collected'}
        else:
            data = request.query_params
            meta = {'code': 27085, 'message': serializer.errors}
        return Response({'data': data, 'meta': meta})


class GetAlideviceid(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    serializer_class = DevcieModelSerializer

    def get(self, request):
        fog_device_id = request.query_params.get('fog_device_id', None)
        if fog_device_id:
            try:
                device = Device.objects.get(fog_device_id=fog_device_id)
                data = self.serializer_class(device).data
                meta = {'code': 0, 'message': 'successful'}
            except Exception, e:
                data = request.query_params
                meta = {'code': 28099, 'message': 'params error'}
        else:
            data = request.query_params
            meta = {'code': 28099, 'message': 'params error'}
        return Response({'data': data, 'meta': meta})


class GetFogEnduserid(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        open_id = request.GET.get("open_id", None)
        fog_product_id = request.GET.get("fog_product_id", None)
        if open_id and fog_product_id:
            try:
                enduser = Enduser.objects.get(fog_product_id=fog_product_id, open_id=open_id)
                enduser_id = enduser.fog_enduser_id
                data = {"fog_enduser_id": enduser_id}
                meta = {"code": 0, "message": "successful"}
            except Enduser.DoesNotExist:
                data = request.query_params
                meta = {"code": 28200, "message": "enduser does not exit"}
            except Enduser.MultipleObjectsReturned:
                data = request.query_params
                meta = {"code": 28201, "message": "enduser more than one"}
            return Response({'data': data, 'meta': meta})
