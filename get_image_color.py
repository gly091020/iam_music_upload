# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import json
import os

from PIL import Image
import numpy as np

command = "%s%s%s%s%s%s"

def median_cut(pixels, depth=0, max_depth=2):
    """递归中位切分算法"""
    if depth == max_depth:
        return [np.mean(pixels, axis=0).astype(int)]

    # 按最大颜色范围维度切分
    channel = np.argmax([pixels[:, c].max() - pixels[:, c].min() for c in range(3)])
    sorted_pixels = pixels[pixels[:, channel].argsort()]
    median = len(sorted_pixels) // 2

    # 递归处理子集
    return median_cut(sorted_pixels[:median], depth + 1, max_depth) + \
        median_cut(sorted_pixels[median:], depth + 1, max_depth)


def get_dominant_colors_median_cut(image_path, num_colors=4, sample_size=10000):
    """手动中位切分实现"""
    img = Image.open(image_path).convert("RGB")
    pixels = np.array(img.resize((200, 200)))  # 缩小提升性能
    pixels = pixels.reshape(-1, 3)

    # 随机采样
    if len(pixels) > sample_size:
        pixels = pixels[np.random.choice(len(pixels), sample_size, replace=False)]

    # 执行中位切分
    colors = median_cut(pixels, max_depth=int(np.log2(num_colors)))
    return [int("{:02x}{:02x}{:02x}".format(*c), 16) for c in colors]


def chu_li(output_port):
    with open("files/image/image_color.json", "r+") as file:
        color_d = json.loads(file.read())
    with open("data.json") as file:
        d = json.loads(file.read())
    with open("files/image/image.json") as image_file:
        image_data = json.loads(image_file.read())
    with open("bin/command.mcfunction", "w+") as command_file:
        for k, v in d.items():
            colors = []
            if f"files/{v}.wav" in image_data.keys():
                if v in color_d.keys():
                    colors = color_d[v]
                else:
                    colors = get_dominant_colors_median_cut(
                        os.path.join("files/image/", image_data[f"files/{v}.wav"]))
                    color_d.update({v: colors})
            url = 'http://' + output_port + '/download_file?path=' + v + ".wav"
            if colors:
                if "-" in k:
                    a, t = k.split(" - ")
                    command = command % (a, t, url, colors[2], colors[0], colors[1])
                else:
                    command = command % ("", k, url, colors[2], colors[0], colors[1])
            else:
                if "-" in k:
                    a, t = k.split(" - ")
                    command = command % (a, t, url, -1, -11447983, -1)
                else:
                    command = command % ("", k, url, -1, -11447983, -1)
            command_file.write(command + "\n")
        with open("files/image/image_color.json", "w+") as file:
            file.write(json.dumps(color_d))