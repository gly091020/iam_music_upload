# -*- coding: utf-8 -*-
import os
import subprocess
import re
import time
import traceback

import ffmpy
import requests

ok_video_list = []


def download_bilibili(url: str):
    u = re.sub(r"\?spm_id_from.*", "", url)
    s = subprocess.Popen(args=[r"downloader/bilibili/BBDown", u, "--work-dir", "downloader/bilibili", '--audio-only'], stdout=subprocess.DEVNULL)
    s.communicate()
    for f in os.listdir("downloader/bilibili"):
        if os.path.splitext(f)[1] in [".m4a"]:
            to_wav(os.path.join("downloader/bilibili", f))
            ok_video_list.append(f"downloader/temporary/{os.path.splitext(os.path.split(os.path.join('downloader/bilibili', f))[1])[0]}.wav")
            os.remove(os.path.join("downloader/bilibili", f))


def upload_local(path: str):
    if not to_wav(path):
        print("上传失败")
        return
    ok_video_list.append(f"downloader/temporary/{os.path.splitext(os.path.split(path)[1])[0]}.wav")
    os.remove(path)


def to_wav(path: str):
    print("转换：%s" % path)
    try:
        ffmpy.FFmpeg(
            inputs={os.path.abspath(path): "-y"},
            outputs={f"downloader/temporary/{os.path.splitext(os.path.split(path)[1])[0]}.wav": None}
        ).run()
        return True
    except ffmpy.FFRuntimeError:
        print("处理错误：")
        traceback.print_exc()
        return False
    except ffmpy.FFExecutableNotFoundError:
        print("你没装ffmpeg，请安装")
        return False


def auto_upload(url: str, upload_file_count: int, time_sleep: float):
    num = 0
    d = "auto_upload/"
    while 1:
        for f in os.listdir(d):
            if os.path.splitext(f)[1] != ".mp3":
                continue
            file = {'file': open(os.path.join(d, f), 'rb')}
            requests.post(url, files=file)
            num += 1
            os.remove(os.path.join(d, f))
            if num == upload_file_count:
                num = 0
                time.sleep(time_sleep)
        time.sleep(time_sleep)