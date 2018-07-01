# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class SendMessage(models.Model):
    id = models.AutoField(primary_key=True)
    open_id = models.CharField(max_length=128, verbose_name="微信用户ID")
    device_id = models.CharField(max_length=128, verbose_name="微信设备ID")
    media_id = models.CharField(max_length=128, verbose_name="微信多媒体ID")
    is_readed = models.BooleanField(default=False)
    sendtime = models.DateTimeField(auto_now_add=True, verbose_name=u'发送时间')
    readedtime = models.DateTimeField(blank=True, null=True, verbose_name=u'读取时间')

    class Meta:
        verbose_name_plural = "发送消息"

    def __str__(self):
        return self.id
