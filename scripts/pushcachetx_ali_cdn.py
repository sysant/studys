# -*- coding=utf-8
'''
1.从腾讯COS拉取文件url
2.腾讯云cdn和阿里云cdn手动预热
3.通过调整main区域的位置进行cdn预热顺序调整
4. 基于线上国内某项目进行测试编写
5. 使用方式  python3 tx_ali_cdn_pushcache.py andriod 1.0.2
6. python版本依赖 pinstall python3.6.8   pip3  install -U pip
7. 腾讯云sdk安装
   1).Python2需安装qcloud_cos，而Python3不需要pip3 install qcloud_cos，只需安装cos-python-sdk-v5，
   2).在Python3版本中cos-python-sdk-v5包含qcloud_cos，如果安装了则pip3 uninstall qcloud_cos
       pip3 install tencentcloud-sdk-python; pip3 install -U cos-python-sdk-v5

8. 阿里云sdk安装
    pip3 install oss2  ;  pip3 install aliyun-python-sdk-cdn
'''

import json
import uuid
import os
import string
import sys
import logging
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from urllib.parse import urlparse
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cdn.v20180606 import cdn_client, models
import oss2
from itertools import islice
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcdn.request.v20180510.RefreshObjectCachesRequest import RefreshObjectCachesRequest
from aliyunsdkcdn.request.v20180510.PushObjectCacheRequest import PushObjectCacheRequest


# 循环取url（每次取1000）
def GetUrlsList(region, secret_id, secret_key, bucket, prefix):
    urls = []
    urls_ali = []
    marker = ""
    token = None  # 使用临时密钥需要传入 Token，默认为空，可不填
    scheme = 'https'  # 指定使用 http/https 协议来访问 COS，默认为 https，可不填
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
    client = CosS3Client(config)
    while True:
        response = client.list_objects(
            Bucket=bucket,
            Prefix=prefix,
            Marker=marker
        )
        for file_info in response['Contents']:
            full_url1 = "%s%s" % (cdn_tx, file_info['Key'])
            full_url2 = "%s%s" % (cdn_ali, file_info['Key'])
            urls.append(full_url1)
            urls_ali.append(full_url2)
        if response['IsTruncated'] == 'false':
            break
        marker = response['NextMarker']
        # 加入固定json入口文件
        # urls.append(refresh_json_tx)
        # urls.append(refresh_json_ali)
    return urls, urls_ali


# 列表逐步取一定值
def split_list_to_sub_lists(lst, sublist_size):
    sub_lists = []
    for i in range(0, len(lst), sublist_size):
        sublist = lst[i:i + sublist_size]
        result_dict = {"Urls": sublist}
        sub_lists.append(result_dict)
    return sub_lists


# 调用腾讯CDN接口预热URL
def PushTXCdnCache(sub_list):
    batches = 1
    for params in sub_list:
        if len(params["Urls"]) == 0:
            print('', end='')
        else:
            try:
                cred = credential.Credential(secret_id, secret_key)
                httpProfile = HttpProfile()
                httpProfile.endpoint = "cdn.tencentcloudapi.com"
                # httpProfile.endpoint = "cdn.global.tencentcloudapi.com" # global

                clientProfile = ClientProfile()
                clientProfile.httpProfile = httpProfile
                client = cdn_client.CdnClient(cred, "", clientProfile)

                # req = models.PurgeUrlsCacheRequest()   # 如果刷新url使用该方法
                req = models.PushUrlsCacheRequest()  # 如果预热url使用该方法
                # req.from_json_string(paramstr)
                # mainland：预热至境内节点 overseas：预热至境外节点 global：预热全球节点，默认为 mainland
                params["Area"] = "mainland"  # 字典插入元素
                req.from_json_string(json.dumps(params))

                # resp = client.PurgeUrlsCache(req)      # 如果刷新url使用该方法
                resp = client.PushUrlsCache(req)

                # 输出RequestId和TaskId
                print(resp.to_json_string())
                batch_num = len(params["Urls"])
                print("第 %s 批[腾讯云CDN]预热的URL共计\033[32m %s \033[0m个." % (batches, batch_num))
                batches += 1
                print('\n')
            except TencentCloudSDKException as err:
                print(err)

    print(f"本次[腾讯云CDN]预热的目录为：\033[32m {prefix} \033[0m")
    print(f"本次[腾讯云CDN]预热的域名为：\033[32m {cdn_tx} \033[0m")
    # print(f"本次[腾讯云CDN]预热的项目客户端版本控制文件为：\033[32m {refresh_json_tx} \033[0m")
    print(f"本次[腾讯云CDN]预热的URL共计\033[32m {url_num} \033[0m个.")
    print('\n')


"""
阿里云CDN，
 1、预热：每次最多可以提交 100 条 URL 预热；
 2、刷新：每次请求最多支持提交 1000 条 URL 刷新或者 100 个目录刷新或者 1 个正则刷新；单个域名每分钟最多支持提交 10000 条 URL 刷新。
"""


# 调用阿里CDN 接口刷新URL
def split_list_into_strings(lst, size):
    strings = []
    for i in range(0, len(lst), size):
        chunk = lst[i:i + size]
        str_chunk = '\n'.join(chunk)
        strings.append(str_chunk)
    return strings


# 定义阿里云CDN接口刷新函数
def PushALICdnCache(result_strings):
    # 刷新是RefreshObjectCachesRequest，预热是PushObjectCacheRequest
    # request = RefreshObjectCachesRequest()
    # 刷新是RefreshObjectCachesRequest，预热是PushObjectCacheRequest
    request = PushObjectCacheRequest()
    request.set_accept_format('json')
    for refresh_url_ali in result_strings:
        request.set_ObjectPath(refresh_url_ali)
        response = client_ali.do_action_with_exception(request)
        print("阿里云：" + f'{response}')
    print('\n')
    print(f"本次[阿里云CDN]预热的目录为：\033[32m {prefix} \033[0m")
    print(f"本次[阿里云CDN]预热的域名为：\033[32m {cdn_ali} \033[0m")
    # print(f"本次[阿里云CDN]预热的项目客户端版本控制文件为：\033[32m {refresh_json_ali}\033[0m")
    print(f"本次[阿里云CDN]预热的URL共计：\033[32m {url_num} \033[0m个.")


if __name__ == '__main__':
    # 获取系统类型android or ios
    os_type = sys.argv[1]
    # 获取对应子目录版本号
    version = sys.argv[2]

    # 基础常量(按环境需要实际修改)
    cdn_tx = "https://XXXXX-tx.YYYYY.ZZ/"
    cdn_ali = "https://XXXXX-ali.YYYYY.ZZ/"
    bucket = "COS-NAME"   #腾讯云cos桶名
    base_url = f"bg/{os_type}/{version}/"
    base_url2 = f"bg/{os_type}/{version}/"
    prefix = f"bg/{os_type}/{version}"

    # 定义阿里AccessKEY(按环境需要实际修改)
    client_ali = AcsClient('LTAIXXXXXXXXX', 'CLF1YYYYYYYYYYYYYYYYYY', 'cn-hangzhou')

    # 定义腾讯AccessKEY(按环境需要实际修改)
    secret_id = 'AKID52XXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    secret_key = 'rVAg3YYYYYYYYYYYYYYYYYYYYYYYYYY'
    region = 'ap-shanghai'  # 替换为用户的 Region

    # 获取腾讯云COS中文件列表
    CosUrls = GetUrlsList(region, secret_id, secret_key, bucket, prefix)
    urls = CosUrls[0]
    urls_ali = CosUrls[1]
    url_num = len(urls)
    print(f"cos存储桶中的文件数有: {url_num}")
    # 腾讯云cdn拆分列表成多个子列��，每个子列表包含2000个元素
    list_size = 2000
    sub_list = split_list_to_sub_lists(urls, list_size)
    # 阿里云cdn拆分列表成多个子列��，每个子列表包含100个元素
    chunk_size = 100
    result_strings = split_list_into_strings(urls_ali, chunk_size)
    # print(len(result_strings))
    # 调用腾讯云CDN接口刷新URL
    PushTXCdnCache(sub_list)
    # 调用阿里云CDN接口刷新URL
    PushALICdnCache(result_strings)
