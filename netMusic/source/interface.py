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
from netMusic import *


class interface():
    def __init__(self):
        # 初始化netMusic
        self.music = netMusic()
        # 创建界面
        self.app = Tk()
        # 标题
        self.app.title('网易云音乐下载器')
        # 窗口大小
        self.app.geometry('900x600')

        # 标签控件
        self.label = Label(self.app, text='请输入歌曲名称：', font=('楷书', 18))
        # 标签定位
        self.label.grid(sticky=W)

        # 输入框
        self.entry = Entry(self.app, font=('楷书', 18), bd=5, width=50)
        self.entry.grid(row=0, column=1)

        # 搜索按钮
        self.search_but = Button(self.app, text='搜索', font=(
            '楷书', 18), command=self.search_but)
        self.search_but.grid(row=0, column=2, sticky=E)

        # 歌曲信息列表框
        self.music_text = Listbox(self.app, font=('楷书', 14), width=90, heigh=2)
        self.music_text.grid(row=1, columnspan=3)

        # 热评列表框
        self.comments_text = Listbox(
            self.app, font=('楷书', 14), width=90, heigh=20)
        self.comments_text.grid(row=2, columnspan=3)

        # 信息显示列表框
        self.meg_text = Listbox(self.app, font=('楷书', 14), width=90, heigh=3)
        self.meg_text.grid(row=3, columnspan=3)

        # 下载按钮
        self.down_but = Button(self.app, text='开始下载', font=(
            '楷书', 15), command=self.down_but)
        self.down_but.grid(row=4, column=0, sticky=W)

        # 导入评论按钮
        self.comment_but = Button(self.app, text='导出评论', font=(
            '楷书', 15), command=self.save_comments_but)
        self.comment_but.grid(row=4, column=1)

        # 退出按钮
        self.quit_but = Button(self.app, text='退出程序', font=(
            '楷书', 15), command=self.app.quit)
        self.quit_but.grid(row=4, column=2, sticky=E)

        # 显示界面
        self.app.mainloop()

    # 获取热评
    def get_hotcommnets(self, name, id):
        if self.comments_text.size() > 0:
            self.comments_text.delete(0, END)

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

            n1_len = 45 - len(user_name) - len(str(like_num)) - 8
            n1 = '评论者：' + user_name + n1_len * ' ' + '获赞数：' + str(like_num)
            self.comments_text.insert(END, n1)

            comment = '评论：' + comment
            n2 = len(comment)

            # 防止屏幕溢出屏幕
            if n2 <= 45:
                self.comments_text.insert(END, comment)
            else:
                self.comment_list = list(comment)
                times = n2 // 45
                for i in range(0, times):
                    self.comment_list.insert((times - i)*45, '|')
                comment = ''.join(self.comment_list)
                comments = comment.split('|')
                for i in comments:
                    self.comments_text.insert(END, i)

            self.comments_text.update()

    def save_comments_but(self):
        # 获取输入的歌曲名称
        name = self.entry.get()
        if name == '':
            tkinter.messagebox.showwarning(title='warning', message='请输入歌名')
        else:
            if self.meg_text.size() > 0:
                self.meg_text.delete(0, END)
            music_detail = self.music.get_music_detail(name)

            name = music_detail[0]['name']
            id = music_detail[0]['id']

            wb = openpyxl.Workbook()
            sheet = wb.active
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
                x = [name, id, user_name, comment, like_num]

                # 将上述信息连续按行写入excel
                sheet.append(x)

            if not os.path.exists('./comment'):
                os.mkdir('./comment')
                print('comment文件夹创建成功')

            # 保存热评
            wb.save(filename='./comment/' + name + '热评.xlsx')
            self.meg_text.insert(END, '热评导出成功')
            self.meg_text.update()

    # 搜索歌曲名称
    def search_but(self):
        # 获取输入的歌曲名称
        name = self.entry.get()
        if name == '':
            tkinter.messagebox.showwarning(title='warning', message='请输入歌名')
        else:
            if self.music_text.size() > 0:
                self.music_text.delete(0, END)
                self.meg_text.delete(0, END)
            music_detail = self.music.get_music_detail(name)

            name = music_detail[0]['name']
            author = music_detail[0]['ar'][0]['name']
            id = music_detail[0]['id']

            # 文本框
            self.music_text.insert(END, "歌曲：" + name)
            self.music_text.insert(END, "歌手：" + author)

            # 更新
            self.music_text.update()

            self.get_hotcommnets(name, id)

    # 下载歌曲
    def down_but(self):
        # 获取输入的歌曲名称
        name = self.entry.get()
        if name == '':
            tkinter.messagebox.showwarning(title='warning', message='请输入歌名')
        else:
            if self.meg_text.size() > 0:
                self.meg_text.delete(0, END)
            music_detail = self.music.get_music_detail(name)

            name = music_detail[0]['name']
            id = music_detail[0]['id']

            url = 'http://music.163.com/song/media/outer/url?id=%d.mp3' % id

            if not os.path.exists('./music'):
                os.mkdir('./music')
                print('music文件夹创建成功')
                
            # 文本框
            self.meg_text.insert(END, '歌曲：' + name + '正在下载...')
            # 文本框滚动
            self.meg_text.see(END)
            # 更新
            self.meg_text.update()
            # 下载
            urllib.request.urlretrieve(
                'http://music.163.com/song/media/outer/url?id=' + str(id), './music/'+name+'.mp3')
            # 文本框
            self.meg_text.insert(END, '下载完毕')
            # 文本框滚动
            self.meg_text.see(END)
            # 更新
            self.meg_text.update()


if __name__ == '__main__':
    app = interface()
