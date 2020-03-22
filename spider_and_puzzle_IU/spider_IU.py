import re
from selenium import webdriver
from bs4 import BeautifulSoup
import time
from urllib.request import urlretrieve

# 创建chrome浏览器驱动
driver = webdriver.Chrome()

# 加载界面
driver.get("https://image.baidu.com/search/index?tn=baiduimage&ipn=r&ct=201326592&cl=2&lm=-1&st=-1&fm=result&fr=&sf=1&fmq=1584776128523_R&pv=&ic=&nc=1&z=&hd=&latest=&copyright=&se=1&showtab=0&fb=0&width=&height=&face=0&istype=2&ie=utf-8&hs=2&sid=&word=IU")
time.sleep(3)

# 获取页面初始高度
js = "return action=document.body.scrollHeight"
height = driver.execute_script(js)

# 将滚动条调整至页面底部
driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
time.sleep(5)

# 定义初始时间戳（秒）
t1 = int(time.time())

# 定义循环标识，用于终止while循环
status = True

# 重试次数
num = 0

while status:
    # 获取当前时间戳（秒）
    t2 = int(time.time())
    # 判断时间初始时间戳和当前时间戳相差是否大于30秒，小于30秒则下拉滚动条
    if t2 - t1 < 30:
        new_height = driver.execute_script(js)
        if new_height > height:
            time.sleep(1)
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            # 重置初始页面高度
            height = new_height
            # 重置初始时间戳，重新计时
            t1 = int(time.time())
    elif num < 3:  # 当超过30秒页面高度仍然没有更新时，进入重试逻辑，重试3次，每次等待30秒
        time.sleep(3)
        num = num + 1
    else:  # 超时并超过重试次数，程序结束跳出循环，并认为页面已经加载完毕！
        print("滚动条已经处于页面最下方！")
        status = False
        # 滚动条调整至页面顶部
        driver.execute_script('window.scrollTo(0, 0)')
        break

# 获取所有图片链接
content = driver.page_source
soup = BeautifulSoup(content, 'html.parser')
urls = soup.find_all('img', attrs={"class": re.compile('main_img img-hover')})

# 把图片链接插进列表
img_list = []
for url in urls:
    try:
        url_child = url.get('data-imgurl')
        img_list.append(url_child)
    except Exception as e:
        print(e)

# 循环下载图片并依次命名
img_num = 0
for img in img_list:
    time.sleep(0.2)
    img_num += 1
    file_name = 'IU_' + str(img_num) + '.jpg'
    try:
        urlretrieve(img, './IU/'+file_name)
    except Exception as e:
        print(e)
