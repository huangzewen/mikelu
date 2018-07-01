# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from web import views

urlpatterns = [
    url(regex=r'^transition/$', view=views.transition, name='transition'),
    url(regex=r'^fogapi/$', view=views.FogApi.as_view(), name='fogapi'),
    url(regex=r'^aliaudioapi/$', view=views.AliAudioApi.as_view(), name='aliaudioapi'),
    url(regex=r'^fogapi/$', view=views.FogApi.as_view(), name='fogapi'),
    url(regex=r'^wifi/$', view=views.wifi, name='wifi'),
    url(regex=r'^collectionlist/$', view=views.CollectionView.as_view(), name='collectionlist'),
    url(regex=r'^collection/$', view=views.Collection_MusicView.as_view(), name='collection'),
    url(regex=r'^getalideviceid/$', view=views.GetAlideviceid.as_view(), name='getalideviceid'),
    url(regex=r'^getenduserid/$', view=views.GetFogEnduserid.as_view(), name='getenduserid')

]
