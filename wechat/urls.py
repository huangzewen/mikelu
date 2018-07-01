# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wechat import views

urlpatterns = [
    url(regex=r'^wechat/$', view=views.Wechat.as_view(), name='wechat'),
    url(regex=r'^senddevicevoice/$', view=views.SendDeviceVoice.as_view(), name='senddevicevoice'),
    url(regex=r'^notificationread/$', view=views.Notificationread.as_view(), name='notificationread'),
    url(regex=r'^getunreadmessage/$', view=views.GetUnreadmessage.as_view(), name='getunreadmessage'),
    url(regex=r'^ali_authcode/$', view=views.GetAliAuthcode.as_view(), name='ali_authcode'),
    url(regex=r'^deviceregister/$', view=views.DeviceRegister.as_view(), name='deviceregister'),
    url(regex=r'^favorites_play/$', view=views.Collection_MusicView.as_view(), name='favorites_play')

]
