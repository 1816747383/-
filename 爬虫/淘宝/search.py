import time
import csv
import random
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

edge_options = Options()
# edge_options.add_argument('--headless')  # 如果需要无头模式，可以打开
edge_options.add_argument('--disable-gpu')
edge_options.add_argument('--window-size=1920,1080')
# 可自定义 User-Agent
edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

edge_service = Service("E:/Program Files/edgedriver_win64/edgedriver_win64/msedgedriver.exe")
driver = webdriver.Edge(service=edge_service, options=edge_options)

login_url = "https://www.taobao.com/"
driver.get(login_url)
print("请在 30 秒内手动登录淘宝...")
time.sleep(120)

print("登录完成，开始爬取数据...")

base_url = "https://s.taobao.com/search?q=买手机&page={}"
csv_file = "2.taobao_phones.csv"

header = ["商品名称", "价格", "图片链接", "销量", "地址", "店铺名称"]
with open(csv_file, mode='w', newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)
    writer.writerow(header)

    for page in range(26, 51):  # 例子：要爬7页
        print(f"正在爬取第 {page} 页...")
        
        driver.get(base_url.format(page))
        time.sleep(random.uniform(3, 6))  # 页面加载后，先随机等待一下

        # 等待商品列表出现
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"tbpc-col search-content-col")]'))
            )
        except:
            print(f"第 {page} 页未定位到搜索商品区域，跳过。")
            continue

        # 滚动懒加载，多滚几次
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 5))  # 每次滚动后随机等待

        # 获取商品块
        items = driver.find_elements(By.XPATH, '//div[contains(@class,"tbpc-col search-content-col")]')
        print(f"本页共找到 {len(items)} 个商品块，开始解析...")

        for idx, item in enumerate(items, start=1):
            title = "未知"
            price = "未知"
            img_url = "未知"
            sales = "未知"
            location = "未知"
            shop_name = "未知"

            try:
                # 商品名称
                try:
                    title_element = item.find_element(By.XPATH, './/div[contains(@class,"title--qJ7Xg_90")]/span')
                    title = title_element.text.strip()
                except:
                    pass

                # 价格
                try:
                    p_int = item.find_element(By.XPATH, './/span[contains(@class,"priceInt--yqqZMJ5a")]').text.strip()
                    p_float = item.find_element(By.XPATH, './/span[contains(@class,"priceFloat--XpixvyQ1")]').text.strip()
                    price = f"{p_int}.{p_float}" if p_int else "未知"
                except:
                    pass

                # 图片链接
                try:
                    img_element = item.find_element(By.XPATH, './/img[contains(@class,"mainPic--Ds3X7I8z")]')
                    img_url = img_element.get_attribute("src")
                except:
                    pass

                # 销量
                try:
                    sales_element = item.find_element(By.XPATH, './/span[contains(@class,"realSales--XZJiepmt")]')
                    sales = sales_element.text.strip()
                except:
                    pass

                # 发货地址
                try:
                    loc_elems = item.find_elements(By.XPATH, './/div[contains(@class,"procity--wlcT2xH9")]/span')
                    if loc_elems:
                        location = " ".join(e.text for e in loc_elems)
                except:
                    pass

                # 店铺名称
                try:
                    shop_element = item.find_element(By.XPATH, './/span[contains(@class,"shopNameText--DmtlsDKm")]')
                    shop_name = shop_element.text.strip()
                except:
                    pass

                # 写入 CSV
                row_data = [title, price, img_url, sales, location, shop_name]
                writer.writerow(row_data)
                print(f"第 {page} 页-第 {idx} 条商品 -> 爬取成功: {title}")

            except Exception as e:
                print(f"第 {page} 页-第 {idx} 条商品 -> 爬取失败: {e}")

        # 页与页之间再来个随机等待
        time.sleep(random.uniform(5, 10))

driver.quit()
print("数据爬取完成，已保存到", csv_file)
