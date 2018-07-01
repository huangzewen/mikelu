# -*- coding: utf-8 -*-

import base64
import hashlib
import hmac
import requests
from datetime import datetime


def test():
    time_data = datetime.now().strftime("%a,%d,%b.%Y %X GMT")
    body = "你在说什么"
    hash = hashlib.md5()
    hash.update(body)
    md5 = hash.digest().encode('base64').strip()
    feature = "POST" + "\n" + "audio/wav, application/json" + "\n" + md5 + "\n" + "text/plain" + "\n" + time_data
    hmacsha1 = hmac.new("Jdg6soDUqlIhENJ3RYJz6OKTIrukqZ", feature, hashlib.sha1)
    my_sign = base64.b64encode(hmacsha1.digest())
    headers = {"Content-type": "text/plain", "Accept": "audio/wav, application/json", "Date": time_data,
               "Authorization": "Dataplus LTAI6889E7ZDn7CA:" + my_sign}
    response = requests.post(headers=headers, url="https://nlsapi.aliyun.com/speak", data=body)
    fh = open('test.wav', "a+")
    fh.write(response.text)
    fh.close()


if __name__ == "main":
    test()
