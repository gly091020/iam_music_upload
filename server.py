# -*- coding: utf-8 -*-
import json
import os
import shutil
import time
import threading
import traceback

from flask import *
import download
import nbt_import
import filetype
import uuid
from tinytag import TinyTag

app = Flask(__name__)
config = {"port": 9090, "ip": "127.0.0.1", "debug": False}
port = config["port"]
ip = config["ip"]
debug = config["debug"]

output_port = f"{ip}:{port}"
nbt_thread = None #type:threading.Thread

def read_config():
    global config, port, ip, debug
    if os.path.isfile("config.json"):
        with open("config.json") as file:
            config = json.loads(file.read())
    else:
        with open("config.json", "w+") as file:
            file.write(json.dumps(config))
    port = config["port"]
    ip = config["ip"]
    debug = config["debug"]


def create_dir():
    for d in ["bin", "downloader", "files", "bin/upload", "downloader/bilibili", "downloader/temporary", "files/image"]:
        if not os.path.isdir(d):
            os.mkdir(d)
    for f in ["data.json", "downloader/bilibili/请将BBDown.exe放在这里"]:
        if os.path.isfile(f):
            continue
        if os.path.splitext(f)[1] == ".json":
            with open(f, "w+") as file:
                file.write("{}")
        else:
            with open(f, "w+"):
                pass



def get_random_id(music_file):
    music_file = os.path.splitext(music_file)[0]
    s = str(uuid.uuid4())
    with open("data.json") as file:
        d = json.loads(file.read())  # type:dict
    d.update({music_file: s})
    with open("data.json", "w+") as file:
        file.write(json.dumps(d))
    return s


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/')
def main_html():
    if download.ok_video_list:
        for v in download.ok_video_list:
            shutil.copy(v, f"files/{get_random_id(os.path.splitext(os.path.split(v)[1])[0])}.wav")
            os.remove(v)
        download.ok_video_list.clear()
    with open("data.json") as file:
        d = json.loads(file.read())  # type:dict
    text = ""
    file_list = [x for x in os.listdir("files/") if os.path.splitext(x)[1] == ".wav"]
    for i, t in enumerate([os.path.splitext(x)[0] + "————" + list(d.keys())[list(d.values()).index(os.path.splitext(x)[0])] for x in file_list]):
        text += f"""<li><a onclick="handleCopy('{'http://' + output_port + '/download_file?path=' + file_list[i]}')" href="">{t}
        </a><a href="{'http://' + output_port + '/file_delete?file=' + file_list[i]}">删除</a></li>"""
    with open("templates/主页.html", "r", encoding="utf-8") as file:
        return file.read().replace(r"{[|花里胡哨的占位符来避免冲突|]}", text, 1)


@app.route('/file_upload', methods=['POST', "GET"])
def file_upload():
    file = request.files.get('file')
    if file:
        if os.path.splitext(file.filename)[1] in [".mp3", ".ogg"]:
            path = 'downloader/temporary/' + file.filename
            file.save(path)
            threading.Thread(target=download.update_local, args=(path,), daemon=False).start()
            return redirect(url_for("ti_shi", string='上传成功，正在转换'))
        elif os.path.splitext(file.filename)[1] == ".wav":
            file.save('files/' + file.filename)
            os.rename('files/' + file.filename, 'files/' + get_random_id(file.filename) + ".wav")
            return redirect(url_for("main_html"))
        return redirect(url_for("ti_shi", string='上传失败，格式不支持'))
    else:
        return redirect(url_for("ti_shi", string='上传失败，未选择文件'))


@app.route('/file_delete', methods=['POST', "GET"])
def file_delete():
    file = request.args.get("file")
    if file:
        if os.path.isfile(os.path.join("files/" + file)):
            os.remove(os.path.join("files/" + file))
            # with open("data.json") as file1:
            #     d = json.loads(file1.read())  # type:dict
            # if os.path.splitext(file)[0] in d.values():
            #     d.pop(d)
            # with open("data.json", "w+") as file1:
            #     file1.write(json.dumps(d))
        return redirect(url_for("ti_shi", string='删除成功'))
    else:
        return redirect(url_for("ti_shi", string='请求格式错误'))


def file_import(file: str):
    if file:
        if os.path.splitext(file)[1] in [".mp3", ".ogg"]:
            path = 'downloader/temporary/' + os.path.split(file)[1]
            shutil.copy(file, path)
            download.update_local(path)
            name = None
            if download.ok_video_list:
                for v in download.ok_video_list:
                    name = get_random_id(os.path.splitext(os.path.split(v)[1])[0])
                    shutil.copy(v, f"files/{name}.wav")
                    os.remove(v)
                download.ok_video_list.clear()
            else:
                print("错误：转换失败")
                return None
            return 'http://' + output_port + '/download_file?path=' + name + ".wav"
        elif os.path.splitext(file)[1] == ".wav":
            name = get_random_id(file) + ".wav"
            shutil.copy(file, "files/" + name)
            return 'http://' + output_port + '/download_file?path=' + name
    print("错误：文件无效")
    return None


@app.route('/_url_upload', methods=['POST', "GET"])
def _url_upload():
    url = request.args.get("url")
    if url:
        if "bilibili" in url or "b23" in url:
            if not os.path.isfile("downloader/bilibili/BBDown.exe"):
                return redirect(url_for(
                    "ti_shi", string='上传失败，请先下载BBDown.exe并放在 downloader/bilibili 文件夹'
                                                         '\nBBDown链接：https://github.com/nilaoda/BBDown/releases'))
            print("上传：" + url)
            threading.Thread(target=download.download_bilibili, args=[url], daemon=True).start()
        else:
            return redirect(url_for("ti_shi", string='上传失败，未知的链接'))
    else:
        return redirect(url_for("ti_shi", string='上传失败，参数错误'))
    return redirect(url_for("main_html"))


@app.route('/url_upload')
def url_upload():
    return render_template("上传视频链接.html")


@app.route('/nbt_download')
def nbt_download():
    return render_template("下载nbt.html",
                           is_on=("disabled=\"disabled\"" if nbt_thread and nbt_thread.is_alive() else ""),
                           is_on1=("" if os.path.isfile("bin/imp_music_data.dat") else "disabled=\"disabled\""),
                           running="运行中" if nbt_thread and nbt_thread.is_alive() else "空闲")

@app.route('/_nbt_download', methods=['GET'])
def _nbt_download():
    global nbt_thread
    nbt_thread = threading.Thread(target=nbt_import.chu_li, args=[request.args.get(f"uuid{i}") for i in range(1, 5)], daemon=True)
    nbt_thread.start()
    return redirect(url_for("ti_shi", string='上传成功，正在处理'))

@app.route("/get_music_name")
def get_music_name():
    with open("data.json") as file:
        d = json.loads(file.read())  # type:dict
    text = ""
    for i in d.items():
        text += i[0] + "————" + 'http://' + output_port + '/' + i[1] + ".wav"
    return text


@app.route('/ti_shi', methods=['GET'])
def ti_shi():
    string = request.args.get("string")
    if string:
        print("提示：%s" % string)
        return render_template("提示.html", data=string)
    else:
        return redirect(url_for("main_html"))


@app.route('/download_file', methods=['GET'])
def download_file():
    path = request.args.get("path")
    if not path or not os.path.isfile(os.path.join("files", path)):
        return redirect(url_for("ti_shi", string='找不到文件……'))
    if os.path.splitext(path)[1] not in [".wav", ".dat", ".json", ".jpg", ".png"]:
        return redirect(url_for("ti_shi", string='拒绝操作'))
    if os.path.isdir(os.path.join("files", path)):
        return redirect(url_for("ti_shi", string='暂不支持下载文件夹'))
    if os.path.isfile(os.path.join("files", path)):
        print("文件下载：" + path)
        return send_file(os.path.join("files", path))
    else:
        return redirect(url_for("ti_shi", string='没有找到文件'))



@app.route('/favicon.ico')
def favicon():
    return send_file('static/favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/relay_server_json')
def relay_server_json():
    return send_file("static/relay_server.json")

@app.route('/relay_server')
def relay_server():
    j = json.loads("""{"Status":"Ok","MaxFileSize":10485760,"Version":"2.0.0","Name":"MG Oracle Tokyo","PlayListCont":0,"MusicCont":0,"UserCont":0,"Time":{"CurrentTime":1744095956453,"ResponseSpeed":0},"ServerHardware":{"Memory":{"Total":0,"Available":0},"CPU":{"Name":"Unsupported","PhysicalProcessorCount":0,"LogicalProcessorCount":0,"MaxFreq":0,"Temperature":0}}}""")
    j["MaxFileSize"] = 1145141919810
    j["Version"] = "11.45.14"
    j["Name"] = "IAM 文件上传中继服务器"
    j["CurrentTime"] = time.time() * 1000
    return j


@app.route('/relay_servermusic-upload', methods=['GET', "POST"])
def relay_server_music_upload():
    # todo:这里的链接名称（servermusic）是错的，但换成正确的又没法用
    if not request.data:
        return """{"Error":"请求错误","Message":"无效的请求"}"""
    for f in os.listdir("bin/upload/"):
        os.remove(os.path.join("bin/upload/", f))
    with open("bin/upload/upload_file", "wb+") as file:
        file.write(request.get_data())
    t = filetype.guess("bin/upload/upload_file")
    if t and t.EXTENSION in ["mp3", "wav", "ogg"]:
        os.rename("bin/upload/upload_file", "bin/upload/upload_file." + t.EXTENSION)
        try:
            tag = TinyTag.get("bin/upload/upload_file." + t.EXTENSION)
            music_name = "%s - %s" % (tag.artist, tag.title)
        except Exception:
            print("出现错误，将使用默认名称")
            traceback.print_exc()
            music_name = "上传音乐"
        name = "bin/upload/%s.%s" % (music_name, t.EXTENSION)
        os.rename("bin/upload/upload_file." + t.EXTENSION, name)
        r = file_import(name)
        if r:
            print("模组上传文件：%s" % r)
            return """{"url":"%s"}""" % r
        else:
            return """{"Error":"未知错误","Message":"请查看服务器后台"}"""
    else:
        return """{"Error":"文件错误","Message":"无效的文件格式"}"""


@app.route('/upload_image', methods=['GET', "POST"])
def upload_image():
    # 请修改Otyacraft Engine的配置文件（urlRegex）允许图片读取
    # 1:请求错误 2：文件格式不支持
    if not request.get_data():
        return """{"status":1}"""
    t = filetype.guess(request.get_data())
    if t and t.EXTENSION in ["jpg", "png"]:
        u = str(uuid.uuid4())
        with open("files/image/%s.%s" % (u, t.EXTENSION), "wb+") as file:
            file.write(request.get_data())
        print("图片上传：" + "%s.%s" % (u, t.EXTENSION))
        return ("""{"data":{"link":"http://127.0.0.1:9090/download_file?path=image/%s.%s"}}"""
                % (u, t.EXTENSION))
    else:
        return """{"status":2}"""


if __name__ == '__main__':
    read_config()
    create_dir()
    print("将在http://%s上运行" % output_port)
    app.run(debug=debug, host="0.0.0.0", port=port)
