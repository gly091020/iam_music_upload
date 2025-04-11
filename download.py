# -*- coding: utf-8 -*-
import os
import subprocess
import re
import ffmpy
ok_video_list = []


def download_bilibili(url: str):
    u = re.sub(r"\?spm_id_from.*", "", url)
    s = subprocess.Popen(args=[r"downloader/bilibili/BBDown", u, "--work-dir", "downloader/bilibili", '--audio-only'])
    s.communicate()
    for f in os.listdir("downloader/bilibili"):
        if os.path.splitext(f)[1] in [".m4a"]:
            to_wav(os.path.join("downloader/bilibili", f))
            ok_video_list.append(f"downloader/temporary/{os.path.splitext(os.path.split(os.path.join('downloader/bilibili', f))[1])[0]}.wav")
            os.remove(os.path.join("downloader/bilibili", f))


def update_local(path: str):
    to_wav(path)
    ok_video_list.append(f"downloader/temporary/{os.path.splitext(os.path.split(path)[1])[0]}.wav")
    os.remove(path)


def to_wav(path: str):
    print("转换：%s" % path)
    ffmpy.FFmpeg(
        inputs={os.path.abspath(path): None},
        outputs={f"downloader/temporary/{os.path.splitext(os.path.split(path)[1])[0]}.wav": None}
    ).run(stderr=subprocess.DEVNULL)

