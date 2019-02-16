from flask import Flask
import requests
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from wordcloud import WordCloud, ImageColorGenerator
import jieba.analyse
from html2text import html2text
from time import sleep
from collections import OrderedDict
from flask import render_template, request
from scipy.misc import imread  # 这是一个处理图像的函数
# 创建一个Flask应用
app = Flask(__name__)

##################################
# 微博相关函数 #

# 定义获取博主信息的函数
# 参数uid为博主的id
def get_user_info(uid):
    # 发送请求
    result = requests.get('https://m.weibo.cn/api/container/getIndex?type=uid&value={}'.format(uid))
    json_data = result.json()  # 获取繁华信息中json内容
    # 获取性别，微博中m表示男性，f表示女性
    print("json_data:",json_data)
    if json_data['data']['userInfo']['gender'] == 'm':
        gender = '男'
    elif json_data['data']['userInfo']['gender'] == 'f':
        gender = '女'
    else:
        gender = '未知'

    userinfo = OrderedDict()
    userinfo['昵称'] = json_data['data']['userInfo']['screen_name']           # 获取用户头像
    userinfo['性别'] = gender                                         # 性别
    userinfo['关注数'] = json_data['data']['userInfo']['follow_count']        # 获取关注数
    userinfo['粉丝数'] = json_data['data']['userInfo']['followers_count']     # 获取粉丝数
    userinfo['认证信息'] = json_data['data']['userInfo']['verified_reason']   # 获取粉丝数
    userinfo['描述'] = json_data['data']['userInfo']['description']           # 获取粉丝数
    data = {
        'profile_image_url': json_data['data']['userInfo']['profile_image_url'], # 获取头像
        'containerid': json_data['data']['tabsInfo']['tabs'][1]['containerid'],  # 此字段在获取博文中需要
        'userinfo': '\n'.join(['{}:{}'.format(k, v) for (k,v) in userinfo.items()])
    }
    return data

# 循环获取所有博文
def get_all_post(uid, containerid):
    # 从第一页开始
    page = 0
    # 这个用来存放博文列表
    posts = []
    while page < 5:
        # 请求博文列表
        result = requests.get('https://m.weibo.cn/api/container/getIndex?is_hot=1&type=uid&value={}&containerid={}&page={}'.format(uid, containerid, page))
        json_data = result.json()
        # 当博文获取完毕，退出循环
        if not json_data['data']['cards']:
            break

        # 循环将新的博文加入列表
        for i in json_data['data']['cards']:
            if 'mblog' in i:
                posts.append(i['mblog']['text'])

        # 停顿半秒，避免被反爬虫
        sleep(0.5)

        # 跳转至下一页
        page += 1
    #print(posts)
    # 返回所有博文
    return posts
##############################
## 云图相关函数

# 生成云图
def generate_personas(uid, data_list):
    content = '<br>'.join([html2text(i) for i in data_list])

    # 这里使用jieba的textrank提取出1000个关键词及其比重
    result = jieba.analyse.textrank(content, topK=1000, withWeight=True)

    # 生成关键词比重字典
    keywords = dict()
    for i in result:
        keywords[i[0]] = i[1]

    # 初始化图片
    image = Image.open('./static/images/images.png')
    graph = np.array(image)
    back_color = imread('./static/images/images.png')  # 解析该图片
    # 生成云图，这里需要注意的是WordCloud默认不支持中文，所以这里需要加载中文黑体字库
    wc = WordCloud(font_path='./static/fonts/simhei.ttf', background_color='white', max_words=300, mask=graph)
    wc.generate_from_frequencies(keywords)
    # 基于彩色图像生成相应彩色
    image_color = ImageColorGenerator(back_color)
    # 显示图片
    plt.imshow(wc)
    plt.imshow(wc.recolor(color_func=image_color))
    plt.axis("off") # 关闭图像坐标系
    dest_img = './static/images/{}.png'.format(uid)
    # plt.savefig(dest_img)
    wc.to_file(dest_img)
    return dest_img

@app.route('/', methods=['GET', 'POST'])
def index():
    # 初始化模版数据为空
    userinfo = {}
    # 如果是一个Post请求,并且有微博用户id,则获取微博数据并生成相应云图
    # request.method的值为请求方法
    # request.form既为提交的表单
    if request.method == 'POST' and request.form.get('uid'):
        uid = request.form.get('uid')
        print("UID:",uid)
        userinfo = get_user_info(uid)
        posts = get_all_post(uid, userinfo['containerid'])
        dest_img = generate_personas(uid, posts)
        userinfo['personas'] = dest_img
        print("UserInfo",userinfo)
    return render_template('index.html', userinfo=userinfo)

if __name__ == '__main__':
    app.run()
