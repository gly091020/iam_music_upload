# -*- coding: utf-8 -*-
import json
import os.path
import random
import time
import shutil
from tinytag import TinyTag
import nbtlib
from pydub import AudioSegment
music_d = {}
ip = ""

def get_duration_pydub(file_path):
    if file_path in music_d.keys():
        return music_d[file_path]
    else:
        audio_file = AudioSegment.from_file(file_path)
        duration = audio_file.duration_seconds
        music_d.update({file_path: duration})
        return duration


def music_to_nbt(owner:nbtlib.IntArray, music_name: str, music_link: str, music_path:str):
    try:
        tag = TinyTag.get(music_path)
        author, name = tag.artist, tag.title
    except:
        try:
            author, name = music_name.split(" - ", 1)
        except ValueError:
            author = ""
            name = music_name
    data = nbtlib.parse_nbt(
        """{m:{Owner:[I;0,0,0,0],Author:"",UUID:[I;0,0,0,0],Image:{Identifier:"",ImageType:"empty"},CreateDate:0L,Source:{Identifier:"",Duration:0L,LoaderType:"http"},Name:""}}""")
    data["m"]["Owner"] = owner
    data["m"]["Author"] = nbtlib.String(author)
    data["m"]["Name"] = nbtlib.String(name)
    data["m"]["Source"]["Identifier"] = nbtlib.String(music_link)
    data["m"]["Source"]["Duration"] = nbtlib.Long(get_duration_pydub(music_path) * 1000)
    data["m"]["CreateDate"] = nbtlib.Long(time.time() * 1000)
    data["m"]["UUID"] = nbtlib.IntArray([random.randint(-99999999, 99999999), random.randint(-99999999, 99999999), random.randint(-99999999, 99999999), random.randint(-99999999, 99999999)])
    with open("files/image/image.json") as file:
        d = json.loads(file.read())  # type:dict[str]
    if music_path in d.keys():
        data["m"]["Image"]["ImageType"] = nbtlib.String("url")
        data["m"]["Image"]["Identifier"] = nbtlib.String(music_link.split("path=")[0] + "path=image/" + d[music_path])
    return data


def new_music_playlist(owner: nbtlib.IntArray, owner_name: str, music_list:nbtlib.List):
    data = nbtlib.parse_nbt("""{m:{Authority:{Owner:[I;0,0,0,0],OwnerName:"",InitialAuthority:"read_only",Authority:{v:[],k:[]},Public:0b},UUID:[I;-933743310,1235108061,-1488196181,1452006443],Image:{Identifier:"",ImageType:"empty"},MusicList:[],CreateDate:1743760446877L,Name:"1"}}""")
    data["m"]["Authority"]["Owner"] = owner
    data["m"]["Authority"]["OwnerName"] = nbtlib.String(owner_name)
    data["m"]["CreateDate"] = nbtlib.Long(time.time() * 1000)
    data["m"]["Name"] = nbtlib.String(f"导入歌单{time.localtime(time.time()).tm_min}")
    data["m"]["UUID"] = nbtlib.IntArray(
        [random.randint(-99999999, 99999999), random.randint(-99999999, 99999999), random.randint(-99999999, 99999999),
         random.randint(-99999999, 99999999)])
    data["m"]["MusicList"] = music_list
    return data

def chu_li(u1, u2, u3, u4):
    global music_d
    with open("music_duration.json", "r+") as file:
        music_d = json.loads(file.read())
    o = nbtlib.IntArray((u1, u2, u3, u4))
    on = "python"
    musics = []
    shutil.copy("static/imp_music_data_clear.dat", "bin/imp_music_data.dat")
    dat = nbtlib.load("bin/imp_music_data.dat")
    with open("data.json") as f:
        data = json.loads(f.read())
    if len(dat["data"]["Musics"]) == 0:
        music_nbt = []
        for k, v in data.items():
            if not os.path.isfile(os.path.join("files", v + ".wav")):
                continue
            m = music_to_nbt(o, k, 'http://' + ip + '/download_file?path=' + v + ".wav", "files/" + v + ".wav")
            musics.append(m["m"]["UUID"])
            music_nbt.append(m)
        dat["data"]["Musics"] = nbtlib.List(music_nbt)
    else:
        for k, v in data.items():
            if not os.path.isfile(os.path.join("files", v + ".wav")):
                continue
            m = music_to_nbt(o, k, 'http://' + ip + '/download_file?path=' + v + ".wav", "files/" + v + ".wav")
            musics.append(m["m"]["UUID"])
            dat["data"]["Musics"].append(m)
    if len(dat["data"]["PlayLists"]) == 0:
        dat["data"]["PlayLists"] = nbtlib.List([new_music_playlist(o, on, nbtlib.List(musics))])
    else:
        dat["data"]["PlayLists"].append(new_music_playlist(o, on, nbtlib.List(musics)))
    dat.save()
    with open("music_duration.json", "w+") as file:
        file.write(json.dumps(music_d))