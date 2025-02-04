import time
import random
import pickle
import csv
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Edge 浏览器配置
edge_options = Options()
edge_options.add_argument('--disable-gpu')
edge_options.add_argument('--window-size=1920,1080')
edge_options.add_argument('--no-sandbox')
edge_options.add_argument('--disable-dev-shm-usage')
edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

# Edge 驱动路径
edge_service = Service("E:/Program Files/edgedriver_win64/edgedriver_win64/msedgedriver.exe")

# 创建浏览器驱动对象
driver = webdriver.Edge(service=edge_service, options=edge_options)

# 打开目标网址
url = "https://www.xiaohongshu.com/explore"
driver.get(url)

# 登录提示
print("请扫码登录...")
time.sleep(30)  # 等待用户扫码并完成登录

# 保存登录后的 Cookies
cookies_file = "cookies.pkl"
with open(cookies_file, "wb") as f:
    pickle.dump(driver.get_cookies(), f)
print("Cookies 已保存！")

# 关闭浏览器
driver.quit()

# 创建新的无头模式浏览器
edge_options.add_argument('--headless')  # 启用无头模式
driver = webdriver.Edge(service=edge_service, options=edge_options)

# 加载保存的 Cookies
driver.get(url)  # 打开页面以设置 Cookies
with open(cookies_file, "rb") as f:
    cookies = pickle.load(f)
    for cookie in cookies:
        driver.add_cookie(cookie)

# 刷新页面以应用 Cookies
driver.refresh()

# 等待页面加载
time.sleep(5)

# 添加关键词搜索功能
keyword = "文心一言"  # 替换为你需要搜索的关键词
try:
    # 找到搜索框并输入关键词
    search_box = driver.find_element(By.ID, "search-input")
    search_box.send_keys(keyword)  # 输入关键词
    time.sleep(1)  # 模拟人类输入停顿
    search_box.send_keys(Keys.ENTER)  # 模拟回车触发搜索
    time.sleep(5)  # 等待搜索结果加载

    # 模拟向下滚动以加载更多内容
    scroll_times = 80  # 向下滚动的次数
    article_links = []

    for i in range(scroll_times):
        print(f"正在加载第 {i + 1} 页内容...")
        
        # 获取当前页面的文章链接
        articles = driver.find_elements(By.CSS_SELECTOR, "a.cover")
        for article in articles:
            href = article.get_attribute("href")
            if href and href not in article_links:
                article_links.append(href)

        # 模拟滚动页面
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 4))  # 随机延迟，防止反爬

    print(f"共找到 {len(article_links)} 篇文章链接！")

    # 保存评论和点赞数到 CSV 文件
    csv_file = f"小红书—{keyword}评论.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["文章链接", "评论作者", "评论内容", "评论点赞数", "评论发布时间"])

        # 遍历每篇文章
        for idx, link in enumerate(article_links):
            print(f"正在爬取第 {idx + 1} 篇文章: {link}")
            driver.get(link)
            time.sleep(5)  # 等待文章页面加载

            # 模拟向下滚动加载评论
            scroll_comment_times = 40  # 评论加载滚动次数
            for _ in range(scroll_comment_times):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))  # 随机延迟

            # 爬取一级评论
            comments = driver.find_elements(By.CLASS_NAME, "comment-item")
            for comment in comments:
                try:
                    author = comment.find_element(By.CLASS_NAME, "name").text.strip()
                    content = comment.find_element(By.CLASS_NAME, "note-text").text.strip()
                    like_count = comment.find_element(By.CLASS_NAME, "like-wrapper").find_element(By.CLASS_NAME, "count").text.strip()
                    time_posted = comment.find_element(By.CLASS_NAME, "date").text.strip()

                    writer.writerow([link, author, content, like_count, time_posted])
                except Exception as e:
                    print(f"跳过无效评论: {e}")

finally:
    # 关闭浏览器
    driver.quit()
