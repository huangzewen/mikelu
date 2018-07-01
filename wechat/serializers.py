# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework.serializers import Serializer

from database.models import Device, Enduser, Collection, Collection_Music


class DeviceVoiceSerializer(Serializer):
    wx_device_id = serializers.CharField(max_length=256)
    media_id = serializers.CharField(max_length=256)


class NotificationreadSerializer(Serializer):
    wx_device_id = serializers.CharField(max_length=128, required=True)
    media_id = serializers.CharField(max_length=128, required=True)


class GetUnreadmessageSerializer(Serializer):
    wx_device_id = serializers.CharField(max_length=128, required=True)


class GetAliAuthcodeSerializer(Serializer):
    wx_device_id = serializers.CharField(max_length=128, required=True)


class AliluoApiSerializer(Serializer):
    url = serializers.CharField(max_length=128, required=True)
    para = serializers.CharField(max_length=128, required=True)
    method = serializers.CharField(max_length=128, required=True)


class DeviceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device


class EnduserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enduser


class StartDownloadQueueResponseSerializer(serializers.Serializer):
    musicid = serializers.CharField(max_length=36)
    deviceid = serializers.CharField(max_length=128)
    open_id = serializers.CharField(max_length=128)


class OnlineSheetSerializer(serializers.Serializer):
    TYPE = (
        ('m', '单曲'),
        ('s', '专辑'),
    )
    type = serializers.ChoiceField(choices=TYPE)
    id = serializers.IntegerField()
    device_id = serializers.CharField(max_length=128)
    open_id = serializers.CharField(max_length=128)
    note = serializers.CharField(max_length=128, allow_blank=True)


class DeviceRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device


class Collection_MusicSerializer(serializers.Serializer):
    device = serializers.CharField(max_length=36)
    collection = serializers.IntegerField()
    flag = serializers.IntegerField()
    track_id = serializers.CharField(max_length=1024)


class CollectionModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection


class Collection_MusicModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection_Music
