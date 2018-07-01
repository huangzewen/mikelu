# -*- coding: utf-8 -*-
import ConfigParser
import time
from threading import Thread

import paho.mqtt.client as mqtt

cp = ConfigParser.SafeConfigParser()
cp.read('settings.conf')

USERNAME = cp.get('MQTTINFO', 'LOGINNAME')
PASSWORD = cp.get('MQTTINFO', 'PASSWORD')
PORT = cp.get('MQTTINFO', 'MQTTPORT')
HOST = cp.get('MQTTINFO', 'MQTTHOST')
# TOPIC = cp.get('MQTTINFO', 'TOPIC')
CLIENTID = cp.get('MQTTINFO', 'CLIENTID')


# 订阅线程，每次调用将创建一个线程，不间断接收上面的信息
class SubscriberThreading(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.topicName = TOPIC

    def run(self):
        subscriberManager = SubscriberManager()
        subscriberManager.subscribe(self.topicName)


class SubscriberManager():
    def subscribe(self, TOPIC):
        self.topicName = TOPIC

        # 连接成功后
        def on_connect(client, userdata, flags, rc):
            print(u"[INFO] 连接MQTT服务器:" + self.topicName + u"通道，返回码 " + str(rc))

            # 订阅在on_connect，断开连接后将重新进行订阅.
            client.subscribe(str(self.topicName))

        # 接受发布消息.
        def on_message(client, userdata, msg):
            print(u"[INFO] 在 %s 接收到来自 %s 通道的消息,内容为: %s" % (
                time.asctime(time.localtime(time.time())), msg.topic, str(msg.payload)))

        client = mqtt.Client()
        client.username_pw_set(USERNAME, PASSWORD)
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(HOST, PORT, 60)

        print(u"[INFO] 成功订阅主题:" + self.topicName)
        client.loop_forever()


# 发布类，将需要传的数据发布到指定主题
class PublisherManager(object):
    def __init__(self):
        self.ip = HOST
        self.port = PORT

    def MQTT_PublishMessage(self, topicName, message):
        # print u"[INFO] 发布消息至 %s 主题, 消息为: %s" % (topicName, message)
        mqttc = mqtt.Client(CLIENTID)
        mqttc.username_pw_set(USERNAME, PASSWORD)
        mqttc.connect(self.ip, self.port)
        mqttc.publish(topicName, message)
        mqttc.loop(2)  # 定义超时2秒


try:
    publisher = PublisherManager()
except Exception, e:
    print u"错误:{0} ".format(str(e))
