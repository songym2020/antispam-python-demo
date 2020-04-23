#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
易盾反垃圾云服务直播音视频解决方案离线结果获取接口python示例代码
接口文档: http://dun.163.com/api.html
python版本：python3.7
运行:
    1. 修改 SECRET_ID,SECRET_KEY 为对应申请到的值
    2. $ python livevideosolution_callback.py
"""
__author__ = 'yidun-dev'
__date__ = '2019/11/27'
__version__ = '0.2-dev'

import hashlib
import time
import random
import urllib.request as urlrequest
import urllib.parse as urlparse
import json


class LiveVideoSolutionCallbackAPIDemo(object):
    """直播音视频解决方案离线结果获取接口示例代码"""

    API_URL = "https://as.dun.163yun.com/v1/livewallsolution/callback/results"
    VERSION = "v1.0"

    def __init__(self, secret_id, secret_key):
        """
        Args:
            secret_id (str) 产品密钥ID，产品标识
            secret_key (str) 产品私有密钥，服务端生成签名信息使用
        """
        self.secret_id = secret_id
        self.secret_key = secret_key

    def gen_signature(self, params=None):
        """生成签名信息
        Args:
            params (object) 请求参数
        Returns:
            参数签名md5值
        """
        buff = ""
        for k in sorted(params.keys()):
            buff += str(k) + str(params[k])
        buff += self.secret_key
        return hashlib.md5(buff.encode("utf8")).hexdigest()

    def check(self):
        """请求易盾接口
        Returns:
            请求结果，json格式
        """
        params = {}
        params["secretId"] = self.secret_id
        params["version"] = self.VERSION
        params["timestamp"] = int(time.time() * 1000)
        params["nonce"] = int(random.random() * 100000000)
        params["signature"] = self.gen_signature(params)

        try:
            params = urlparse.urlencode(params).encode("utf8")
            request = urlrequest.Request(self.API_URL, params)
            content = urlrequest.urlopen(request, timeout=10).read()
            return json.loads(content)
        except Exception as ex:
            print("调用API接口失败:", str(ex))

    def parse_audio(self, audio_evidences, taskId):
        """音频机审信息"""
        print("=== 音频机审信息 ===")
        asr_status: int = audio_evidences["asrStatus"]
        start_time: int = audio_evidences["startTime"]
        end_time: int = audio_evidences["endTime"]
        if asr_status == 4:
            asr_result: int = audio_evidences["asrResult"]
            print("检测失败: taskId=%s, asrResult=%s" % (taskId, asr_result))
        else:
            action: int = audio_evidences["action"]
            segment_array: list = audio_evidences["segments"]
            if action == 0:
                print("taskId=%s，结果：通过，时间区间【%s-%s】，证据信息如下：%s" % (taskId, segment_array, start_time, end_time))
            elif action == 1 or action == 2:
                # for segment_item in segment_array:
                #     label: int = segment_item["label"]
                #     level: int = segment_item["level"]
                #     evidence: str = segment_item["evidence"]
                print("taskId=%s，结果：%s，时间区间【%s-%s】，证据信息如下：%s" % (taskId, "不确定" if action == 1 else "不通过", start_time, end_time, segment_array))
        print("================")

    def parse_video(self, video_evidences, taskId):
        """视频机审信息"""
        print("=== 视频机审信息 ===")
        evidence: dict = video_evidences["evidence"]
        labels: list = video_evidences["labels"]

        types: int = evidence["type"]
        url: str = evidence["url"]
        begin_time: int = evidence["beginTime"]
        end_time: int = evidence["endTime"]

        for label_item in labels:
            label: int = label_item["label"]
            level: int = label_item["level"]
            rate: float = label_item["rate"]
            subLabels: list = label_item["subLabels"]
        print("Machine Evidence: %s" % evidence)
        print("Machine Labels: %s" % labels)
        print("================")

    def parse_human(self, human_evidences, taskId):
        """人审信息"""
        print("=== 人审信息 ===")
        action: int = human_evidences["action"]
        action_time: int = human_evidences["actionTime"]
        label: int = human_evidences["label"]
        detail: str = human_evidences["detail"]
        warn_count: int = human_evidences["warnCount"]
        evidence: list = human_evidences["evidence"]

        if action == 2:
            print("警告, taskId:%s, 警告次数:%s, 违规详情:%s, 证据信息:%s" % (taskId, warn_count, detail, evidence))
        elif action == 3:
            print("断流, taskId:%s, 警告次数:%s, 违规详情:%s, 证据信息:%s" % (taskId, warn_count, detail, evidence))
        else:
            print("人审信息：%s" % human_evidences)
        print("================")


if __name__ == "__main__":
    """示例代码入口"""
    SECRET_ID = "your_secret_id"  # 产品密钥ID，产品标识
    SECRET_KEY = "your_secret_key"  # 产品私有密钥，服务端生成签名信息使用，请严格保管，避免泄露
    api = LiveVideoSolutionCallbackAPIDemo(SECRET_ID, SECRET_KEY)
    
    ret = api.check()

    code: int = ret["code"]
    msg: str = ret["msg"]
    if code == 200:
        resultArray: list = ret["result"]
        if resultArray is None or len(resultArray) == 0:
            print("暂时没有结果需要获取, 请稍后重试!")
        else:
            for result in resultArray:
                taskId: str = result["taskId"]
                callback: str = result["callback"]
                dataId: str = result["dataId"]
                status: int = result["status"]
                print("taskId:%s, callback:%s, dataId:%s, status:%s" % (taskId, callback, dataId, status))

                evidences: dict = result["evidences"]
                reviewEvidences: dict = result["reviewEvidences"]
                if evidences is not None:
                    evidence: dict = evidences["evidebces"]
                    audio: dict = evidence["audio"]
                    video: dict = evidence["video"]
                    if audio is not None:
                        api.parse_audio(audio, taskId)
                    elif video is not None:
                        api.parse_video(video, taskId)
                    else:
                        print("Invalid Evidence: %s", evidence)
                elif reviewEvidences is not None:
                    api.parse_human(reviewEvidences, taskId)
                else:
                    print("Invalid Result: %s" % result)
    else:
        print("ERROR: code=%s, msg=%s" % (ret["code"], ret["msg"]))
