# -*- coding: utf-8 -*-
import os
import subprocess
import re
import time
import traceback

import yt_dlp
import ffmpy
import requests
from mutagen import File

ok_video_list = []
proxy = None

def download_bilibili(url: str):
    u = re.sub(r"\?spm_id_from.*", "", url)
    s = subprocess.Popen(args=[r"downloader/bilibili/BBDown", u, "--work-dir", "downloader/bilibili", '--audio-only'], stdout=subprocess.DEVNULL)
    s.communicate()
    for f in os.listdir("downloader/bilibili"):
        if os.path.splitext(f)[1] in [".m4a"]:
            get_music_picture(os.path.join("downloader/bilibili", f))
            to_wav(os.path.join("downloader/bilibili", f))
            ok_video_list.append(f"downloader/temporary/{os.path.splitext(os.path.split(os.path.join('downloader/bilibili', f))[1])[0]}.wav")
            os.remove(os.path.join("downloader/bilibili", f))


def download_youtube(url: str):
    cookie = None
    output_path = "downloader/youtube/out.m4a"
    for f in os.listdir("downloader/youtube/"):
        f = os.path.join("downloader/youtube/", f)
        if os.path.splitext(f)[1] == ".txt" and "cookie" in f:
            cookie = f
    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'proxy': proxy,
    }
    if cookie:
        common_opts.update({"cookiefile": cookie})
    else:
        print("警告：未找到cookie文件，这可能导致下载失败")
    if proxy is None:
        common_opts.pop("proxy")
    audio_opts = {
        **common_opts,
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'outtmpl': output_path,
    }

    with yt_dlp.YoutubeDL(common_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info['title']
        channel = info["channel"]
        thumbnail = info['thumbnail']
    with yt_dlp.YoutubeDL(audio_opts) as ydl:
        ydl.download([url])
    new_name = os.path.join("downloader/youtube/", "%s-%s.m4a"
                                                         % (channel, title))
    os.rename(output_path, new_name)
    to_wav(new_name)
    ok_video_list.append(
        f"downloader/temporary/{os.path.splitext(os.path.split(new_name)[1])[0]}.wav")
    os.remove(new_name)
    with requests.get(thumbnail) as r:
        if r.status_code == 200:
            with open(os.path.join("files/image/", os.path.splitext(os.path.split(new_name)[1])[0] + '.jpg'), "wb+") as file:
                file.write(r.content)



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

def get_music_picture(path: str):
    m = File(path)
    if 'APIC:' in m.tags:
        d = m.tags['APIC:'].data
    elif "covr" in m.tags:
        d = m.tags["covr"][0]
    else:
        return False
    with open(f"files/image/{os.path.splitext(os.path.split(path)[1])[0]}.jpg", "wb+") as file:
        file.write(d)
    return True