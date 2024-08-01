from bs4 import BeautifulSoup
from markdownify import markdownify as md
import os
import requests

# 切换到目标目录
os.chdir('blogs')

# 默认的Markdown文件头部内容
default_context = '''
---
layout: post
title: 
categories: [51cto老博文]
description: 
keywords: 
mermaid: false
sequence: false
flow: false
mathjax: false
mindmap: false
mindmap2: false
---
'''


# 下载url中的图片保存
def download_file(url, save_path):
    # 发送HTTP GET请求下载文件
    response = requests.get(url, stream=True)
    # 确保请求成功
    if response.status_code == 200:
        # 打开本地文件进行写入
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"文件已保存到: {save_path}")
    else:
        print(f"无法下载文件，状态码: {response.status_code}")


# 遍历当前目录中的所有文件
for f in os.listdir():
    if f.endswith('.html'):
        print(f)
        md_file_name = f.replace('.html', '.md')
        title = f.replace('.html', '').strip()

        # 写入Markdown文件头部
        with open(md_file_name, 'w', encoding='utf-8') as md_file:
            md_file.write(default_context)
            md_file.write(f"title: {title}\n")
            md_file.write("---\n")

        # 读取HTML文件内容
        with open(f, 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 自定义转换函数
        def custom_md(content, title):
            # 解析图片标签,下载图片，并去除水印
            for img in content.find_all('img'):
                img_name = img.get('alt', '')
                img_url = img['src'].split('?')[0]
                if title in img_name and "watermark" in img['src']:
                    # 确保图片保存目录存在
                    if not os.path.exists(f"images/{title}"):
                        os.makedirs(f"images/{title}")
                    print(img_name, img_url)
                    # 存放在以文章标题目录中
                    save_path = f"images/{title}/{img_name}.png"
                    download_file(img_url, save_path)
                    img_md = f"![{title}](images/{title}/{img_name}.png)"
                    img.replace_with(img_md)
            # 将所有内容转换为Markdown
            return md(str(content))

        # 转换为Markdown
        markdown_content = custom_md(soup, title)

        # 追加Markdown内容到Markdown文件
        with open(md_file_name, 'a', encoding='utf-8') as md_file:
            md_file.write(markdown_content)

        print(f"{f} 转换完成！")
