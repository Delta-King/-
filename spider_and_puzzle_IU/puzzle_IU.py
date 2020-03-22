import os
import re
import math
from PIL import Image, ImageOps
from colorsys import rgb_to_hsv
from concurrent.futures import ProcessPoolExecutor

# 原图路径
PIC = 'IU.jpg'

# 生成图片路径
PIC_OUT = 'IU_puzzle.jpg'

# 图库目录
IMGS_DIR = "IU/"

# 生成马赛克图片输出目录
OUT_DIR = "mosaic/"

# 定义拼接后的图片的宽高
PIC_WIDTH = 18000
PIC_HEIGHT = 12000

# 定义每个小图片的宽高
SLICE_WIDTH = 180
SLICE_HEIGHT = 120

# 差值
ALLOWED_DIFF = 10000

# 透明值
BLEND = 0.6

# 允许一张图片的重复使用次数
REPEAT = 8


def get_avg_hsv(img):
    """获取一张图片的平均hsv值"""
    # 获取图片的宽高
    width, height = img.size
    pixels = img.load()

    h, s, v = 0, 0, 0
    count = 0
    for x in range(width):
        for y in range(height):
            # 获取rgb值，返回的是一个元组（r, g, b）
            pixel = pixels[x, y]
            # 将rgb转hsv值
            hsv = rgb_to_hsv(*[i / 255 for i in pixel])
            h += hsv[0]
            s += hsv[1]
            v += hsv[2]
            count += 1
    if count > 0:
        # 计算hsv的均值
        hAvg = round(h / count, 3)
        sAvg = round(s / count, 3)
        vAvg = round(v / count, 3)
        return hAvg, sAvg, vAvg
    else:
        raise IOError("读取图片数据失败")


def resize_pic(imgName, imgWidth, imgHeight):
    """重定义图片的大小"""
    # 打开图片
    img = Image.open(imgName)
    # 裁剪图片
    # ANTIALIAS 平滑滤波: 对所有可以影响输出像素的输入像素进行高质量的重采样滤波，以计算输出像素值。
    img = ImageOps.fit(img, (imgWidth, imgHeight), Image.ANTIALIAS)
    return img


def get_image_paths():
    """获取所有图片路径"""
    imgs = os.listdir(IMGS_DIR)
    print("一共有{}张图片参与此次成像".format(len(imgs)))
    paths = ["{imgs_dir}/{filename}".format(imgs_dir=IMGS_DIR, filename=filename) for filename in imgs]
    return paths


def convert_image(path):
    """转换图片"""
    img = resize_pic(path, SLICE_WIDTH, SLICE_HEIGHT)
    # 获取平均颜色值
    color = get_avg_hsv(img)  # 这一部分返回的是元组
    try:
        # 按规定格式保存
        img.save(
            "{dir_name}/{filename}.jpg".format(dir_name=OUT_DIR, filename=str(color)))
    except:
        return False


def convert_all_images(paths):
    """生成马赛克块"""
    print("开始生成马赛克块...")
    with ProcessPoolExecutor() as pool:
        pool.map(convert_image, paths)
    print("马赛克块生成已完成")


def find_closest_hsv(hsv, hsv_list):
    """寻找最相近的hsv"""
    similarColor = None
    allowedDiff = ALLOWED_DIFF
    for curColor in hsv_list:
        # 计算两个hsv的差值
        diffValue = math.sqrt(sum([(curColor[i] - hsv[i]) ** 2 for i in range(3)]))
        # 如果满足一定的要求
        if diffValue < allowedDiff and curColor[3] < REPEAT:
            allowedDiff = diffValue
            similarColor = curColor
    # 如果不存在颜色最近，抛出异常
    if similarColor is None:
        raise ValueError("没有足够的近似图片，建议添加更多图源，或是增加图片重复使用次数")

    similarColor[3] += 1
    return "({}, {}, {})".format(similarColor[0], similarColor[1], similarColor[2])


def get_hsv_list():
    """获取全部图源值，返回一个列表"""
    hsvList = list()
    # 遍历输出目录
    for filename in os.listdir(OUT_DIR):
        # 获取文件名，不要后缀
        file_hsv = re.match(r"\((.+)\)\.jpg", filename)
        hvsValue = file_hsv.group(1).split(",")
        # 全部浮点
        hvs = list(map(float, hvsValue))
        # 末尾+0，标记重复次数
        hvs.append(0)
        # 追加
        hsvList.append(hvs)
    return hsvList


def make_pic_by_imgs(pic, hsv_list):
    """利用小图片制作大图片"""
    # 获取大图片的宽高
    width, height = pic.size

    # 创建一张画布
    background = Image.new('RGB', pic.size, (255, 255, 255))
    # 需要小图片的总数
    totalImgs = math.floor((width * height) / (SLICE_WIDTH * SLICE_HEIGHT))
    # 已经使用小图片的数量
    usedImgs = 0
    print("开始生成大图...")
    for top in range(0, height, SLICE_HEIGHT):
        for left in range(0, width, SLICE_WIDTH):
            bottom = top + SLICE_HEIGHT
            right = left + SLICE_WIDTH
            # 截取大图片的一个“块”
            curImg = pic.crop((left, top, right, bottom))
            # 得到这个图片的hsv值
            hsv = get_avg_hsv(curImg)
            # 找到与“块”hsv值最相近的小图片名
            similarImgName = find_closest_hsv(hsv, hsv_list)
            # 找到这个图片的路径
            similarImgPath = "{dir}/{img_name}.jpg".format(dir=OUT_DIR, img_name=similarImgName)
            try:
                pasteImg = Image.open(similarImgPath)
            except IOError:
                print('未找到小图片路径')
                raise

            # 打印进度条
            usedImgs += 1
            done = math.floor((usedImgs / totalImgs) * 100)
            r = "\r[{}{}]{}%".format("▇" * done, " " * (100 - done), done)
            print(r, end="")

            # 将小图片粘贴到画布上
            background.paste(pasteImg, (left, top))

    background.save("未透明化图片.jpg")
    return background


def init():
    print("1. 已经生成马赛克图片")
    print("2. 还未生成马赛克图片")
    choice = input("请选择:")
    if choice == "1":
        pass
    elif choice == "2":
        paths = get_image_paths()
        convert_all_images(paths)
    else:
        print("输的什么玩意儿")
        return False

    dir_name = "{0}/{1}".format(os.path.abspath(os.path.dirname(__file__)), OUT_DIR)
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    return True


if __name__ == "__main__":
    result = init()

    if result:
        img = resize_pic(PIC, PIC_WIDTH, PIC_HEIGHT)
        hsv_list = get_hsv_list()
        out = make_pic_by_imgs(img, hsv_list)
        img = Image.blend(out, img, BLEND)
        img.save(PIC_OUT)
