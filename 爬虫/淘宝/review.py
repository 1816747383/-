import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --------------------------------------------------------------------------
# 1. 设置 WebDriver (Setup WebDriver)
# --------------------------------------------------------------------------
# 确保这个路径是正确的
chromedriver_path = r"E:\\Program Files\\edgedriver_win64\\chromedriver-win64\\chromedriver.exe"
service = Service(chromedriver_path)

# 创建浏览器选项
chrome_options = Options()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
# chrome_options.add_argument("--headless")  # 无头模式，如果不需要看浏览器操作过程可以取消注释
chrome_options.add_argument('--log-level=3') # 减少控制台不必要的日志输出
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation']) # 减少被检测为机器人的风险
chrome_options.add_experimental_option('useAutomationExtension', False)

# 启动浏览器
driver = webdriver.Chrome(service=service, options=chrome_options)
# 添加反检测脚本
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
  "source": """
    Object.defineProperty(navigator, 'webdriver', {
      get: () => undefined
    })
  """
})

# --------------------------------------------------------------------------
# 2. 登录淘宝 (Login to Taobao)
# --------------------------------------------------------------------------
login_url = "https://www.taobao.com/"
print(f"正在打开: {login_url}")
driver.get(login_url)

# 提示用户登录 - 时间可以根据需要调整
login_wait_time = 60
print(f"请在 {login_wait_time} 秒内手动登录淘宝...")
# 这里可以加一个简单的检查，比如等待首页某个登录后才出现的元素
try:
    WebDriverWait(driver, login_wait_time).until(
        # 等待 '我的淘宝' 链接出现，表示登录成功
        EC.presence_of_element_located((By.LINK_TEXT, "我的淘宝"))
    )
    print("检测到登录成功，继续操作...")
except TimeoutException:
    print(f"警告：{login_wait_time}秒内未检测到登录状态，脚本将继续运行，但可能因未登录失败。")

# --------------------------------------------------------------------------
# 3. 导航到商品页面并准备爬取评论 (Navigate to Product Page)
# --------------------------------------------------------------------------
product_review_url = "https://detail.tmall.com/item.htm?id=719878428996"
print(f"正在导航到商品页面: {product_review_url}")

def load_page_with_retry(driver, url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            driver.get(url)
            print("商品页面加载成功。")
            return True
        except TimeoutException:
            print(f"页面加载超时，正在进行第 {attempt + 1}/{retries} 次重试...")
            time.sleep(delay)
        except Exception as e:
            print(f"加载页面时发生错误: {e}")
            time.sleep(delay) # 其他错误也重试
    print("页面加载失败，已达最大重试次数。")
    return False

# 使用函数加载页面
if not load_page_with_retry(driver, product_review_url):
    print("无法加载商品页面，脚本退出。")
    driver.quit()
    exit()

# --------------------------------------------------------------------------
# 4. 点击评论标签并滚动加载 (Click Reviews Tab and Scroll)
# --------------------------------------------------------------------------
try:
    # 等待并点击 "累计评价" 标签
    # 注意: 这个 XPath 可能也需要根据实际页面微调
    # 通常它在 id='detail' 的 div 下的某个 li 元素里
    print("等待 '累计评价' 标签出现并点击...")
    review_tab_xpath = "//div[@id='detail']//li[contains(text(), '累计评价') or contains(@aria-controls, 'review')]"
    review_tab = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, review_tab_xpath))
    )
    # 使用 JavaScript 点击，有时更稳定
    driver.execute_script("arguments[0].click();", review_tab)
    print("'累计评价' 标签已点击。")
    time.sleep(3) # 等待评论区初步加载

except TimeoutException:
    print("错误：未能找到或点击 '累计评价' 标签，请检查 XPath 是否正确或页面结构是否有变。")
    # 即使找不到tab，也尝试继续滚动，有些页面可能默认显示评论
    # driver.quit()
    # exit()
except Exception as e:
    print(f"点击评论标签时出错: {e}")
    # 继续尝试，以防万一

# --- 向下滚动页面加载更多评论 ---
scroll_times = 10  # 设置滚动次数 (可以根据需要调整)
scroll_pause_time = 3  # 每次滚动后的暂停时间 (适当增加时间给页面加载)
print(f"开始向下滚动页面 {scroll_times} 次以加载评论...")

# 获取初始滚动高度
# last_height = driver.execute_script("return document.body.scrollHeight")

for i in range(scroll_times):
    # 执行滚动
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    print(f"滚动 {i+1}/{scroll_times}...")
    # 等待页面加载
    time.sleep(scroll_pause_time)

    # (可选) 检查滚动高度是否变化，如果不再变化可以提前停止
    # new_height = driver.execute_script("return document.body.scrollHeight")
    # if new_height == last_height:
    #     print("页面高度未变，可能已加载完所有评论，停止滚动。")
    #     break
    # last_height = new_height

print("滚动完成。")
time.sleep(2) # 滚动结束后再等一下

# --------------------------------------------------------------------------
# 5. 提取评论数据并保存 (Extract Reviews and Save)
# --------------------------------------------------------------------------
# --- 定义 CSV 文件 ---
csv_filename = "taobao_tmall_reviews_updated.csv"
print(f"准备将评论写入文件: {csv_filename}")
try:
    with open(csv_filename, mode='w', newline='', encoding='utf-8-sig') as csv_file: # 使用 utf-8-sig 防止 Excel 打开乱码
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['用户名', '评论信息', '评论内容'])  # 写入表头 (日期现在包含在信息里)

        # --- 获取所有评论项 (使用更新后的 Class Name) ---
        # 新的评论容器 class name
        review_container_class = "QJEEHAN8H5--Comment--_0b4e753"
        print(f"正在查找所有 class 为 '{review_container_class}' 的评论元素...")
        reviews = driver.find_elements(By.CLASS_NAME, review_container_class)
        print(f"找到 {len(reviews)} 条评论。开始提取...")

        if not reviews:
            print("警告：未能找到任何评论元素。请检查：")
            print("1. 是否已成功登录淘宝/天猫。")
            print("2. 商品页面是否正确加载。")
            print("3. '累计评价' 标签是否被正确点击（如果需要）。")
            print(f"4. 评论容器的 Class Name '{review_container_class}' 是否仍然有效。")

        # --- 遍历每个评论并提取数据 ---
        count = 0
        for review in reviews:
            user_name = "N/A"
            review_meta = "N/A"
            review_content = "N/A"
            try:
                # 提取用户名 (新的 Class Name)
                user_name_class = "QJEEHAN8H5--userName--f0a85ded"
                user_name_element = review.find_element(By.CLASS_NAME, user_name_class)
                # 用户名在 span 标签里
                user_name = user_name_element.find_element(By.TAG_NAME, "span").text

                # 提取评论元信息 (日期和规格等，新的 Class Name)
                meta_class = "QJEEHAN8H5--meta--_8725fde"
                review_meta = review.find_element(By.CLASS_NAME, meta_class).text

                # 提取评论内容 (新的 Class Name)
                content_class = "QJEEHAN8H5--content--_8e6708c"
                review_content = review.find_element(By.CLASS_NAME, content_class).text

                # 打印当前抓取的评论
                print("-" * 20)
                print(f"用户: {user_name}")
                print(f"信息: {review_meta}")
                print(f"内容: {review_content}")

                # 写入CSV
                csv_writer.writerow([user_name, review_meta, review_content])
                count += 1

            except NoSuchElementException as e:
                print(f"提取评论部分内容时出错 (元素未找到): {e} - 可能这条评论结构略有不同，已跳过部分信息。")
                # 即使部分信息出错，也尝试写入已获取的信息
                csv_writer.writerow([user_name, review_meta, review_content])
            except Exception as e:
                print(f"处理单条评论时发生未知错误: {e}")
                # 同样尝试写入，避免丢失整条记录
                csv_writer.writerow([user_name, review_meta, review_content])

        print(f"\n成功提取并写入 {count} 条评论到 {csv_filename}")

except IOError as e:
    print(f"写入 CSV 文件时出错: {e}")
except Exception as e:
    print(f"在提取和保存评论过程中发生意外错误: {e}")

# --------------------------------------------------------------------------
# 6. 关闭浏览器 (Close WebDriver)
# --------------------------------------------------------------------------
print("任务完成，关闭浏览器...")
driver.quit()
print("浏览器已关闭。")