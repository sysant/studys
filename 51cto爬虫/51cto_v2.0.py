from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import re
import os
from bs4 import BeautifulSoup

# 配置Chrome浏览器选项
chrome_options = Options()
chrome_options.add_argument("--headless")  # 启用无头模式
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920x1080")

# 替换为你的ChromeDriver路径 (下载地址 https://chromedriver.storage.googleapis.com/index.html，下载本机chrome对应的版本)
chromedriver_path = '/Users/sysant/PycharmProjects/API/chromedriver'
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)


def create_driver():
    # 创建Chrome浏览器驱动
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error initializing driver: {e}")
        return None


def save_file(save_file, content):
    # 保存文件
    os.makedirs('blogs', exist_ok=True)
    save_path = os.path.join('blogs', save_file)
    with open(save_path, 'a+', encoding='utf-8') as file:
        for i in content:
            scontent = i['url'] + ' -> ' + i['title'] + '\n'
            file.write(scontent)


# 访问url生成并保存为html文件
def get_pages(url, savefile):
    driver = create_driver()
    if driver is None:
        return
    try:
        # 目标文章URL
        PageUrl = url
        try:
            # 打开网页
            driver.get(PageUrl)
            try:
                # 增加等待时间
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'artical-title'))
                )
                # 提取文章标题
                title_element = driver.find_element(By.CLASS_NAME, 'artical-title')
                title = title_element.text
                # 提取文章内容
                content_element = driver.find_element(By.CLASS_NAME, 'artical-content')
                content = content_element.text

                print(f'Title: {title}\n')
                print(f'Content: {content}')

            except Exception as e:
                # 打印页面源码以调试
                save_path = os.path.join('blogs', savefile)
                with open(save_path, 'w', encoding='utf-8') as file:
                    file.write(driver.page_source)
                print(f'Exception: {e}')
                print(f'Page source saved to {savefile} for inspection.')

        finally:
            # 关闭浏览器
            driver.quit()
    except Exception as e:
        print(f"Error in get_pages: {e}")


# 获取指定页面中的url并返回列表
def get_urls(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []
    matching_data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    for h3_tag in soup.find_all('h3', class_='title'):
        a_tag = h3_tag.find('a', href=True)
        if a_tag:
            url = a_tag['href']
            title = a_tag.get_text(strip=True)
            matching_data.append((url, title))

    urls_list = [{'url': url, 'title': title} for url, title in matching_data if title]
    return urls_list


# 获取主页中所有分页的url并返回列表
def get_pages_url(file_path, pattern, main_url):
    matching_data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    for link in soup.find_all('a', href=True):
        match = pattern.search(link['href'])
        if match:
            url = match.group(0)
            title = link.get_text(strip=True)
            matching_data.append((url, title))

    urls_list = [{'url': url, 'title': title} for url, title in matching_data if title]
    # 添加首页链接
    urls_list.insert(0, {'url': f"{main_url}", 'title': '首页'})
    return urls_list


# 获取并保存主页的HTML文件为savfile
def save_main_page(url, savefile):
    # 目标文章URL
    PageUrl = url
    try:
        # 打开网页
        driver.get(PageUrl)
        try:
            # 增加等待时间
            WebDriverWait(driver, 20).until(
                 EC.presence_of_element_located((By.CLASS_NAME, 'artical-title'))
            )
            # 提取文章标题
            title_element = driver.find_element(By.CLASS_NAME, 'artical-title')
            title = title_element.text
            # 提取文章内容
            content_element = driver.find_element(By.CLASS_NAME, 'artical-content')
            content = content_element.text
            print(f'Title: {title}\n')
            print(f'Content: {content}')
        except Exception as e:
            # 打印页面源码以调试
            save_file = savefile
            save_path = os.path.join('blogs', save_file)
            with open(save_path, 'w', encoding='utf-8') as file:
                file.write(driver.page_source)
            print(f'Exception: {e}')
            print('Page source saved to debug.html for inspection.')

    finally:
        # 关闭浏览器
        driver.quit()


if __name__ == '__main__':
    page_urls_file = 'PageUrls.txt'
    url = 'https://blog.51cto.com/dyc2005'
    pages_pattern = re.compile(r'https://blog\.51cto\.com/dyc2005/p_\d+')
    article_pattern = re.compile(r'https://blog\.51cto\.com/dyc2005/\d+')
    # 保存主页的HTML内容
    save_main_page(url, 'main.html')
    # 获取所有分页的URL列表(含首页)
    url_list = get_pages_url('blogs/main.html', pages_pattern, url)
    print(url_list)
    for url_info in url_list:
        savefile = url_info["title"] + '.html'
        # print(url_info["url"], savefile)
        get_pages(url_info["url"], savefile)
        page_urls = get_urls(f"blogs/{savefile}")
        save_file(page_urls_file, page_urls)
    # 通过PageUrls.txt中的url列表获取文章内容保存为标题.html文件
    with open(f"blogs/{page_urls_file}", 'r', encoding='utf-8') as file:
        html_content = file.readlines()
        for link in html_content:
            page_url = link.split('->')[0]
            page_title = link.split('->')[1].strip()
            print(page_url, page_title)
            get_pages(page_url, f"{page_title}.html")
