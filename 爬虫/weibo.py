import os
import time
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# ------------------------------------------------
# 1) 时间解析函数：既能处理 "01月26日 22:28"，
#    也能处理 "刚刚", "5分钟前", "2小时前", "3天前", "昨天 22:28", "前天 09:15" 等
# ------------------------------------------------

def parse_time(raw_time_str, fallback_year=2025):
    """
    将各种微博显示的时间字符串，转换为 '%Y-%m-%d %H:%M:%S'。
    规则：
      - "刚刚"          -> 当前时间
      - "x分钟前"       -> 当前时间 - x 分钟
      - "x小时前"       -> 当前时间 - x 小时
      - "x天前"         -> 当前时间 - x 天
      - "昨天 HH:MM"    -> 当前时间 -1 天，并用 HH:MM
      - "前天 HH:MM"    -> 当前时间 -2 天，并用 HH:MM
      - "MM月dd日 HH:MM" -> 默认按 fallback_year 年
      - 其他无法识别的   -> 原样返回
    注意：使用的是脚本运行时的**本地系统时间**作为基准，如果脚本长时间运行，可能产生轻微偏差。
    """
    now = datetime.now()

    # 1. 刚刚
    if raw_time_str == "刚刚":
        return now.strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. x分钟前
    match = re.match(r"(\d+)分钟前", raw_time_str)
    if match:
        minutes = int(match.group(1))
        real_time = now - timedelta(minutes=minutes)
        return real_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 3. x小时前
    match = re.match(r"(\d+)小时前", raw_time_str)
    if match:
        hours = int(match.group(1))
        real_time = now - timedelta(hours=hours)
        return real_time.strftime("%Y-%m-%d %H:%M:%S")

    # 4. x天前
    match = re.match(r"(\d+)天前", raw_time_str)
    if match:
        days = int(match.group(1))
        real_time = now - timedelta(days=days)
        return real_time.strftime("%Y-%m-%d %H:%M:%S")

    # 5. 昨天 HH:MM
    match = re.match(r"昨天\s+(\d+):(\d+)", raw_time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        real_time = now - timedelta(days=1)
        real_time = real_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return real_time.strftime("%Y-%m-%d %H:%M:%S")

    # 6. 前天 HH:MM
    match = re.match(r"前天\s+(\d+):(\d+)", raw_time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        real_time = now - timedelta(days=2)
        real_time = real_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return real_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 7. MM月dd日 HH:MM
    match = re.match(r"(\d+)月(\d+)日\s+(\d+):(\d+)", raw_time_str)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        hour = int(match.group(3))
        minute = int(match.group(4))
        # 使用 fallback_year
        try:
            dt = datetime(fallback_year, month, day, hour, minute)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return raw_time_str  # 如果组装失败就原样返回

    # 如果都没匹配上，就原样返回
    return raw_time_str


# ------------------------------------------------
# 2) 生成两天一组的区间
#    例如：("2024-09-01", "2024-09-02"), ("2024-09-03", "2024-09-04")...
# ------------------------------------------------
def generate_date_pairs(start_date_str, end_date_str):
    """
    以“两天”为一个区间，生成从 start_date_str ~ end_date_str 的所有 [start, end]。
    如果最后只剩1天，也单独成一个区间。
    """
    date_format = '%Y-%m-%d'
    start_dt = datetime.strptime(start_date_str, date_format)
    end_dt = datetime.strptime(end_date_str, date_format)

    pairs = []
    current = start_dt
    while current <= end_dt:
        next_day = current + timedelta(days=1)
        if next_day > end_dt:
            next_day = end_dt
        # 记录一组
        start_str = current.strftime(date_format)
        end_str = next_day.strftime(date_format)
        pairs.append((start_str, end_str))
        # 跨过这两天
        current = next_day + timedelta(days=1)
    return pairs


# ------------------------------------------------
# 3) 核心：爬取指定关键词、时间区间、页数 -> 返回数据
# ------------------------------------------------
def crawl_weibo_once(keyword, start_date, end_date, max_page, headers):
    """
    使用 requests + BeautifulSoup 爬取给定关键词、时间范围、页数的搜索结果。
    返回 list[dict]，每个元素代表一条微博。
    """
    all_data = []

    # 从开始日期推断一个“默认年份”，给 parse_time 备用
    # （如果你想更精细，可以在 parse_time 内部判断当前月日是否已经过了当前时间等。
    #   这里仅仅示例——假设都用 start_date 里的年份来组装）
    fallback_year = datetime.strptime(start_date, "%Y-%m-%d").year

    for page in range(1, max_page + 1):
        print(f"正在爬取[{start_date} ~ {end_date}] -> 第 {page} 页...")

        base_url = "https://s.weibo.com/weibo"
        params = {
            "q": keyword,
            "typeall": "1",
            "suball": "1",
            "timescope": f"custom:{start_date}:{end_date}",
            "Refer": "g",
            "page": str(page)
        }

        try:
            resp = requests.get(base_url, headers=headers, params=params, timeout=10)
            if resp.status_code != 200:
                print(f"  - 请求失败：状态码 {resp.status_code}，跳过该页...")
                continue
        except Exception as e:
            print(f"  - 请求异常：{e}，跳过该页...")
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        # 找到所有微博卡片
        weibo_cards = soup.find_all("div", attrs={"action-type": "feed_list_item"})
        if not weibo_cards:
            print("  - 该页无微博卡片")
            continue

        for card in weibo_cards:
            mid = card.get("mid", "")

            # 作者
            name_tag = card.find("a", class_="name")
            if name_tag:
                author = name_tag.get_text(strip=True)
            else:
                author = ""

            # 微博正文：如果有“全文”，优先用
            full_content = card.find("p", attrs={"node-type": "feed_list_content_full"})
            short_content = card.find("p", attrs={"node-type": "feed_list_content"})
            if full_content:
                weibo_text = full_content.get_text(strip=True)
            else:
                weibo_text = short_content.get_text(strip=True) if short_content else ""

            # 发布时间
            from_div = card.find("div", class_="from")
            post_time = ""
            if from_div:
                time_a = from_div.find("a")
                if time_a:
                    raw_time = time_a.get_text(strip=True)
                    post_time = parse_time(raw_time, fallback_year)

            # 转评赞数
            reposts_count = "0"
            comment_count = "0"
            attitudes_count = "0"
            card_act_div = card.find("div", class_="card-act")
            if card_act_div:
                li_list = card_act_div.find_all("li")
                if len(li_list) >= 3:
                    rep_text = li_list[0].get_text(strip=True)
                    cmt_text = li_list[1].get_text(strip=True)
                    like_text = li_list[2].get_text(strip=True)

                    # 只取数字部分
                    rep_num = re.findall(r'\d+', rep_text)
                    cmt_num = re.findall(r'\d+', cmt_text)
                    lik_num = re.findall(r'\d+', like_text)
                    if rep_num:
                        reposts_count = rep_num[0]
                    if cmt_num:
                        comment_count = cmt_num[0]
                    if lik_num:
                        attitudes_count = lik_num[0]

            one_data = {
                "页码": page,
                "微博ID": mid,
                "微博作者": author,
                "发布时间": post_time,
                "微博内容": weibo_text,
                "转发数": reposts_count,
                "评论数": comment_count,
                "点赞数": attitudes_count
            }
            all_data.append(one_data)

        # 防止爬太快被限制
        time.sleep(1)

    return all_data


# ------------------------------------------------
# 4) 主程序：两天一组，一次性爬完，每两天保存一次到CSV
# ------------------------------------------------
if __name__ == "__main__":
    # 要爬的关键词
    search_keyword = "豆包ai"

    # 生成两天一组的区间：从 2024-09-01 到 2025-01-27
    date_pairs = generate_date_pairs("2024-09-01", "2025-01-27")

    # 每个区间爬多少页
    max_pages = 50

    # 最终结果存到这个文件
    output_csv = "微博搜索_豆包ai_20240901_20250127.csv"

    # 如果文件不存在，初始化文件并写入表头
    if not os.path.exists(output_csv):
        with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["页码", "微博ID", "微博作者", "发布时间", "微博内容", "转发数", "评论数", "点赞数"])
    
    # 请求头（尤其是 Cookie，需要换成你自己浏览器里的）
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/131.0.0.0 Safari/537.36",
        "Cookie": "SCF=AvSKhFc03l4Rh_j2xSX7gPrzpY_yODV2-61lZhom9tPuwknwCFkXdReRlqoKjMmde6M4GnVvZyHIOVBHBC8-wko.; SINAGLOBAL=4918828378775.037.1734511921189; SUB=_2A25Kk2WhDeRhGeFM61IQ9i3KyDyIHXVp0edprDV8PUNbmtANLVLNkW1NQOJQRG5jFCPcDktn5eZ7778ZGKfQE2QQ; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWxuIxHTcvTlbN0RPpN9Wrv5JpX5KzhUgL.FoMEeh5pSoece052dJLoIp9jIg_Li--Ni-82iKn4i--4i-20iKy8; ALF=02_1740546801; _s_tentry=-; Apache=5701906781543.342.1737968024793; ULV=1737968024794:2:1:1:5701906781543.342.1737968024793:1734511921436"
    }

    # 循环爬取每个“两天”区间
    for (start_d, end_d) in date_pairs:
        print(f"正在爬取时间区间：{start_d} ~ {end_d}")
        records = crawl_weibo_once(
            keyword=search_keyword,
            start_date=start_d,
            end_date=end_d,
            max_page=max_pages,
            headers=headers
        )

        # 如果该区间没有数据，跳过
        if not records:
            print(f"区间 {start_d} ~ {end_d} 没有数据，跳过。")
            continue

        # 将该区间的数据追加保存到 CSV 文件
        with open(output_csv, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            for record in records:
                writer.writerow([
                    record["页码"],
                    record["微博ID"],
                    record["微博作者"],
                    record["发布时间"],
                    record["微博内容"],
                    record["转发数"],
                    record["评论数"],
                    record["点赞数"]
                ])

        print(f"区间 {start_d} ~ {end_d} 爬取完成，共保存 {len(records)} 条微博。")

    print("全部区间爬取完成！")