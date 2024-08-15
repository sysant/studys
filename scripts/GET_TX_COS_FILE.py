# -*- coding=utf-8
# 从腾讯COS拉取文件url
# by yuehui.wang 2023.9.21
# eg. python3 wings-ww-refresh-cdn-only_small_file_v1.py 17  1.17.10

# install python3.6+
# pip3  install -U pip
# pip install
"""
aliyun-python-sdk-cdn==3.8.8
aliyun-python-sdk-core==2.13.36
aliyun-python-sdk-kms==2.16.2
certifi==2023.7.22
cffi==1.15.1
charset-normalizer==2.0.12
cos-python-sdk-v5==1.9.26
crcmod==1.7
cryptography==40.0.2
distlib==0.3.7
filelock==3.4.1
idna==3.4
importlib-metadata==4.8.3
importlib-resources==5.4.0
jmespath==0.10.0
oss2==2.18.1
platformdirs==2.4.0
pycparser==2.21
pycryptodome==3.18.0
requests==2.27.1
six==1.16.0
tencentcloud-sdk-python==3.0.980
typing_extensions==4.1.1
urllib3==1.26.16
virtualenv==20.17.1
xmltodict==0.13.0
zipp==3.6.0

"""


import json
import uuid
import os
import string
import sys
import logging
################## Add Tencent Cloud #########################
## 注：Python2需安装qcloud_cos，而Python3不需要pip3 install qcloud_cos，只需安装cos-python-sdk-v5，
## 在Python3版本中cos-python-sdk-v5包含qcloud_cos，如果安装了则pip3 uninstall qcloud_cos
# pip3 install tencentcloud-sdk-python; pip3 install -U cos-python-sdk-v5
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from urllib.parse import urlparse
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cdn.v20180606 import cdn_client, models

# 获取cos中的文件并拼接成url
def cos_urls(REGION,BUCKET,PREFIX):
    urls_tx = []
    urls_ali = []
    marker = ""
    region = REGION      # 替换为用户的 Region
    token = None                # 使用临时密钥需要传入 Token，默认为空，可不填
    scheme = 'https'            # 指定使用 http/https 协议来访问 COS，默���为 https，可不填
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token,Scheme=scheme)
    client = CosS3Client(config)
    while True:
        response = client.list_objects(
            Bucket=bucket,
            Prefix=prefix,
            Marker=marker
        )
        for file_info in response['Contents']:
            full_url_tx = "%s%s" % (cdn_tx,file_info['Key'])
            full_url_ali = "%s%s" % (cdn_ali,file_info['Key'])
            #if full_url.endswith("fileList.zip"):
            #if full_url.endswith(".zip"):
            urls_tx.append(full_url_tx)
            urls_ali.append(full_url_ali)
        if response['IsTruncated'] == 'false':
            break
        marker = response['NextMarker']

    return(urls_tx)


if __name__ == "__main__":
    # 版本号
    os_type = sys.argv[1]
    version = sys.argv[2]

    # 基础常量
    cdn_tx = "https://XXXXX-tx.YYYYY.ZZ/"
    cdn_ali = "https://XXXXXali.YYYYY.ZZ/"
    bucket = "COS-NAME"
    prefix = f"bg/{os_type}/{version}"

    # 定义腾讯AccessKEY （按实际项目情况修改）
    secret_id = 'AKID52XXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    secret_key = 'rVAg3YYYYYYYYYYYYYYYYYYYYYYYYYYYY'
    region = 'ap-shanghai'
    # 获取cos中列表(调用函数)
    urls = cos_urls(region,bucket,prefix)
    print(len(urls),type(urls))
    for url in urls:
        with open('urls.txt', 'a',encoding='utf-8') as file:
            if url.endswith('/'):
                continue
            else:
                file.write(url + '\n')
