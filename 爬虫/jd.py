from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import os

# 配置 Edge WebDriver
edge_options = Options()
# edge_options.add_argument('--headless')  # 无头模式（可以取消注释）
edge_options.add_argument('--disable-gpu')
edge_options.add_argument('--window-size=1920,1080')
edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# EdgeDriver 路径（根据你的安装路径修改）
edge_service = Service("E:/Program Files/edgedriver_win64/edgedriver_win64/msedgedriver.exe")

# 启动浏览器
driver = webdriver.Edge(service=edge_service, options=edge_options)

# 访问京东首页
driver.get("https://www.jd.com/")
time.sleep(5)  # 等待页面加载

print("请手动扫码登录...")
time.sleep(70)  # 等待用户扫码登录

# 设置变量
base_url = "https://search.jd.com/Search?keyword=%E6%89%8B%E6%9C%BA&pvid=8d31e3e999064fc0b94d61d48e32ae87&isList=0&page={}&s=61&click=0"

# CSV 文件路径
csv_file = "京东商品信息_多页.csv"

# # 如果 CSV 文件存在，先删除，确保每次运行都是新的
# if os.path.exists(csv_file):
#     os.remove(csv_file)

# 爬取前100页
for page in range(101, 201):
    print(f"正在爬取第 {page} 页...")

    # 访问当前页
    driver.get(base_url.format(page))
    time.sleep(10)  # 防止反爬，等待页面加载

    # 等待商品列表加载
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "gl-item")))
    except:
        print(f"第 {page} 页加载超时，跳过...")
        continue  # 跳过当前页，进入下一页

    # 获取商品信息
    products = driver.find_elements(By.CLASS_NAME, "gl-item")
    data = []

    for product in products:
        try:
            # 商品名称
            name = product.find_element(By.CSS_SELECTOR, ".p-name em").text.strip()

            # 商品价格
            price = product.find_element(By.CSS_SELECTOR, ".p-price i").text.strip()

            # 商品评价数
            reviews = product.find_element(By.CSS_SELECTOR, ".p-commit a").text.strip()

            # 商店名称
            shop = product.find_element(By.CSS_SELECTOR, ".p-shop a").text.strip()

            # 商品链接
            product_link = product.find_element(By.CSS_SELECTOR, ".p-name a").get_attribute("href")

            # 图片链接
            image_link = product.find_element(By.CSS_SELECTOR, ".p-img img").get_attribute("src")

            data.append([name, price, reviews, shop, product_link, image_link])

        except Exception as e:
            print(f"某个商品信息提取失败: {e}")

    # 将数据追加到 CSV
    df = pd.DataFrame(data, columns=["名称", "价格", "评价数", "店铺", "商品链接", "图片链接"])
    df.to_csv(csv_file, mode="a", header=not os.path.exists(csv_file), index=False, encoding="utf-8-sig")

    print(f"第 {page} 页数据已保存到 CSV。")

    # 防止过快爬取，增加随机等待时间
    time.sleep(10 + (page % 3))  # 5~7 秒随机等待，减少被反爬的概率

# 关闭浏览器
driver.quit()

print(f"爬取完成，数据已保存为 {csv_file}")