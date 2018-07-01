# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models
from django.utils import timezone


class Enduser(models.Model):
    open_id = models.CharField(max_length=36, verbose_name='微信用户id')
    fog_enduser_id = models.CharField(max_length=36, verbose_name='fog用户id')
    fog_product_id = models.CharField(max_length=36, verbose_name='fog产品名称')

    def __str__(self):
        return self.open_id


class Device(models.Model):
    wx_device_id = models.CharField(max_length=36, verbose_name='微信设备id')
    fog_device_id = models.CharField(max_length=36, verbose_name='fog设备id', primary_key=True)
    fog_product_id = models.CharField(max_length=36, verbose_name='fog产品id', blank=True)
    ai_device_id = models.CharField(max_length=36, verbose_name='ALI AI id')
    createtime = models.DateTimeField(default=timezone.now, verbose_name='注册时间')
    note = models.CharField(max_length=128, verbose_name='备注', blank=True)

    def __str__(self):
        return self.wx_device_id


class Collection(models.Model):
    device = models.ForeignKey(Device)
    name = models.CharField(max_length=128, verbose_name='收藏夹名称')
    count = models.IntegerField(verbose_name='歌曲数量', default=0)
    createtime = models.DateTimeField(default=timezone.now(), verbose_name='创建时间')

    def __str__(self):
        return self.name


class Collection_Music(models.Model):
    track_id = models.CharField(verbose_name='单曲id', max_length=1024)
    music_name = models.CharField(verbose_name='歌曲名称', max_length=1024)
    collection = models.ForeignKey(Collection)
    collectiontime = models.DateTimeField(default=timezone.now(), verbose_name='收藏时间')
