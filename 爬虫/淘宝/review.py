import time
import csv
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 设置Selenium的Edge WebDriver
edge_options = Options()
# edge_options.add_argument('--headless')  # 如果需要无头模式，可以打开
edge_options.add_argument('--disable-gpu')
edge_options.add_argument('--window-size=1920,1080')
edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# 指定Edge WebDriver的路径
edge_service = Service("E:/Program Files/edgedriver_win64/edgedriver_win64/msedgedriver.exe")
driver = webdriver.Edge(service=edge_service, options=edge_options)

# 打开淘宝首页，准备登录
login_url = "https://www.taobao.com/"
driver.get(login_url)

# 提示用户登录
print("请在 30 秒内手动登录淘宝...")
time.sleep(80)  # 等待用户登录，设置为120秒
print("登录完成，开始爬取数据...")

# 进入目标商品的评论页面
product_review_url = "https://detail.tmall.com/item.htm?id=719878428996"

def load_page_with_retry(driver, url, retries=3, delay=10):
    for attempt in range(retries):
        try:
            driver.get(url)
            return  # 如果页面加载成功，跳出循环
        except TimeoutException:
            print(f"加载页面失败，正在第 {attempt + 1} 次重试...")
            time.sleep(delay)  # 延迟后重试
    print("加载页面失败，重试次数已用完")
    return None

# 使用函数加载页面
load_page_with_retry(driver, product_review_url)
time.sleep(10) 

# 等待评论部分加载，开始向下滚动页面加载更多评论
scroll_times = 10  # 设置滚动次数
scroll_pause_time = 2  # 每次滚动后的暂停时间
last_height = driver.execute_script("return document.body.scrollHeight")  # 获取当前页面的滚动高度

# 定义CSV文件，并写入标题
csv_file = open("taobao_reviews.csv", mode='w', newline='', encoding='utf-8')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['用户名', '评论日期', '评论内容'])  # 写入CSV的表头

for _ in range(scroll_times):
    # 向页面底部滚动
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause_time)  # 暂停，确保评论加载完毕

# 获取所有评论项
reviews = driver.find_elements(By.CLASS_NAME, "Comment--KkPcz74T")

# 遍历每个评论，并将数据写入CSV
for review in reviews:
    try:
        # 提取评论的用户名、内容和日期
        user_name = review.find_element(By.CLASS_NAME, "userName--mmxkxkd0").text
        review_content = review.find_element(By.CLASS_NAME, "content--FpIOzHeP").text
        review_date = review.find_element(By.CLASS_NAME, "meta--TDfRej2n").text

        # 打印当前抓取的评论
        print(f"用户: {user_name}\n日期: {review_date}\n评论内容: {review_content}\n")

        # 实时保存每个评论到CSV
        csv_writer.writerow([user_name, review_date, review_content])

    except Exception as e:
        print(f"提取评论时出错: {e}")

# 关闭CSV文件
csv_file.close()

# 关闭WebDriver
driver.quit()
