import requests
from tkinter import *
import tkinter.messagebox
import random
import base64
from Crypto.Cipher import AES
import json
import binascii
import os
import urllib.request
import openpyxl


class netMusic():
    # 设置从JS文件提取的RSA的模数、AES对称密钥、RSA的公钥等信息;初始化抓包网站，以及头部伪装
    def __init__(self):
        self.modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
        self.nonce = '0CoJUm6Qyw8W8jud'
        self.pubKey = '010001'
        self.url = 'https://music.163.com/weapi/cloudsearch/get/web?csrf_token='
        self.headers = {}
        self.setHeaders()
        self.data = {}
        self.secKey = self.getSecKey()

    # 设置header
    def setHeaders(self):
        self.headers = {
            'authority': 'music.163.com',
            'method': 'POST',
            'path': '/weapi/cloudsearch/get/web?csrf_token=',
            'scheme': 'https',
            'accept': '*/*',
            'accept-encoding': 'gzip,deflate,sdch',
            'accept-language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'content-Type': 'application/x-www-form-urlencoded',
            'origin': 'https://music.163.com',
            'referer': 'https://music.163.com/search/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.116 Safari/537.36'
        }

    # 生成16字节即256位的随机数
    def getSecKey(self):
        string = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        secKey = ''
        for i in range(16):
            secKey += string[int(random.random()*len(string))]
        return secKey

    # AES加密，用seckey对text加密CBC模式
    def aesEncrypt(self, text, secKey):
        # 对text进行padding处理
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)

        encryptor = AES.new(secKey.encode('utf-8'), 2,
                            '0102030405060708'.encode('utf-8'))
        # 对text进行加密，密钥为seckey，生成向量为：0102030405060708
        ciphertext = encryptor.encrypt(text.encode('utf-8'))
        ciphertext = base64.b64encode(ciphertext).decode('utf-8')
        return ciphertext

    # 快速模幂运算，求 x^y mod mo;用于RSA加密
    def quickPow(self, x, y, mo):
        res = 1
        while y:
            if y & 1:
                res = res * x % mo
            y = y // 2
            x = x * x % mo
        return res

    # RSA加密
    def rsaEncrypt(self, text, pubKey, modulus):
        text = text[::-1]
        # 加密内容
        a = int(binascii.hexlify(str.encode(text)), 16)
        # 公钥
        b = int(pubKey, 16)
        # 模数
        c = int(modulus, 16)
        rs = self.quickPow(a, b, c)
        return format(rs, 'x').zfill(256)

    # 获取特定data
    def get_data(self, s, offset):
        # 构造text文本
        text = {'hlpretag': '<span class=\"s-fc7\">',
                'hlposttag': '</span>',
                '#/discover': '',
                's': s,
                'type': '1',
                'offset': offset,
                'total': 'true',
                'limit': '30',
                'csrf_token': ''
                }
        text = json.dumps(text)
        # text经过俩次AES加密，密钥分别为nonce，seckey
        params = self.aesEncrypt(
            self.aesEncrypt(text, self.nonce), self.secKey)
        # 对seckey，pubkey，modulus进行RSA加密得到enSeckey
        encSecKey = self.rsaEncrypt(self.secKey, self.pubKey, self.modulus)
        data = {
            'params': params,
            'encSecKey': encSecKey
        }
        return data

    # 获取指定音乐detail
    def get_music_detail(self, name):
        music_detail = []
        for offset in range(1):
            self.data = self.get_data(name, str(offset))

            try:
                response = requests.post(url=self.url,
                                         data=self.data,
                                         headers=self.headers).json()
                result = response['result']['songs']
            except:
                print('爬取失败')

            for music in result:
                '''
                # 判断歌曲的有效性
                if (music['privilege']['fee'] == 0 or music['privilege']['payed']) and music['privilege']['pl'] > 0 and music['privilege']['dl'] == 0:
                    continue
                if music['privilege']['dl'] == 0 and music['privilege']['pl'] == 0:
                    continue
                '''
                music_detail.append(music)

        return music_detail

    # 提供id下载歌曲
    def down(self, name, id):

        # 创建music文件夹
        if not os.path.exists('./music'):
            os.mkdir('./music')
            print('music文件夹创建成功,在当前目录下')

        try:
            print('正在下载', name)
            # 下载歌曲
            urllib.request.urlretrieve(
                'http://music.163.com/song/media/outer/url?id=' + str(id), './music/'+name+'.mp3')
            print(name+'下载完成')
        except:
            print('下载失败')

    # 获取热评
    def get_hotcommnets(self, name, id):
        # 评论请求url
        url = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_' + \
            str(id) + '?csrf_token='

        response = requests.post(
            url, data=self.music.data, headers=self.music.headers)

        hotcomments = json.loads(response.text)['hotComments']

        for i in range(len(hotcomments)):
            # 获取用户昵称
            user_name = hotcomments[i]['user']['nickname']
            # 获取热评内容
            comment = hotcomments[i]['content']
            # 获取点赞数
            like_num = hotcomments[i]['likedCount']
