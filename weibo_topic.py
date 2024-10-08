"""
根据主题获取微博帖子
修改的地方主要是下方获取微博列表的xpath和转发、评论、点赞三个字段的xpath
cookie需要更换成自己微博账号的cookie
"""
import os
import csv
import requests
from lxml import etree
from urllib.parse import quote
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create output directory if it doesn't exist
output_dir = "Data"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Simulate browser headers
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "referer": "https://s.weibo.com/weibo?q=%23%E5%A4%A7%E5%AD%A6%E7%94%9F%23&Refer=index&page=2",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "cookie": "SINAGLOBAL=6647866669866.506.1684830519307; ULV=1726991318233:43:14:1:7467914107442.33.1726991317819:1726798876622; SCF=AoXRlyG2Baua8Z7Tfqx0IKvygtZsyaFSvxNKAEEDcFoDitd9yCDiZKP9apST780xPOb4sTWgEhghWDYI2iedeRA.; UOR=,,mail.qq.com; SUB=_2A25L7qrQDeRhGeFG71YR8yfOzzSIHXVohaIYrDV8PUJbkNB-LWnMkW1NeZSKeZLrFvjDvA90C008HQFqSYbcHFgu; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WhbpjOKTTT--6Aox7_W00yo5JpX5KMhUgL.FoMRShB7e0.EShn2dJLoIEBLxKqL1-eLBKnLxKnL1K5LB.BLxKnL1hnL1-qLxK-LBonL1hqt; ALF=1729259392; _s_tentry=weibo.com; Apache=7467914107442.33.1726991317819"
}

topic = "#大学生#"  # Input topic
fileName = topic.replace('#', '')
start_time = "2024-03-15"
end_time = "2024-03-15"

weibo_count = 0

# Write to CSV file
header = ["用户名称", "帖子内容", "发布时间", "发表方式", "转发数量", "评论数量", "点赞数量"]
with open(f"{output_dir}/{fileName}_{start_time}_{end_time}.csv", "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, header)
    writer.writeheader()

    timescope = f"custom:{start_time}:{end_time}"
    # timescope = f"custom:2024-09-10:2024-09-10"
    page = 0

    while True:
        page += 1
        baseUrl = 'https://s.weibo.com/weibo'
        params = {
            'q': topic,
            'typeall': 1,
            'suball': 1,
            'timescope': timescope,
            'Refer': 'g',
            'page': page
        }
        logging.info(f"Fetching page {page}: {baseUrl}")

        try:
            response = requests.get(baseUrl, headers=headers, params=params)
            response.raise_for_status()
            html = etree.HTML(response.text)

            if html.xpath('//img[@class="no-result"]'):
                logging.info("No results found. Ending scraping.")
                break

            articles = html.xpath('//div[@action-type="feed_list_item"]')
            if not articles:
                logging.info("No articles found. Ending scraping.")
                break

            for article in articles:
                try:
                    user_name = article.xpath('div//div[@class="content"]/div/div/a/@nick-name') or ["无用户名"]
                    publication_time = article.xpath('div//div[@class="from"]/a/text()')[0].strip()
                    article_content = "".join(article.xpath('div/div/div/p[@class="txt"]/text()')).replace(' ', "").strip()
                    publication_model = article.xpath('div//div[@class="from"]/a/text()')[1].strip() if len(article.xpath('div//div[@class="from"]/a/text()')) > 1 else None

                    # 转发
                    forward_count_l = article.xpath('string(.//div[@class="card-act"]/ul/li[1]/a)')
                    forward_count = ''.join(forward_count_l).strip()
                    if str(forward_count) == '转发' or not forward_count.isdigit():
                        forward_count = 0
                    else:
                        forward_count = int(forward_count)

                    # 评论
                    comment_count_l = article.xpath('string(.//div[@class="card-act"]/ul/li[2]/a)')
                    comment_count = ''.join(comment_count_l).strip()
                    if str(comment_count) == '评论' or not comment_count.isdigit():
                        comment_count = 0
                    else:
                        comment_count = int(comment_count)

                    # 点赞
                    like_count_l = article.xpath('string(.//div[@class="card-act"]/ul/li[3]/a)')
                    like_count = ''.join(like_count_l).strip()
                    if str(like_count) == '点赞' or not like_count.isdigit():
                        like_count = 0
                    else:
                        like_count = int(like_count)

                    data_dict = {
                        "用户名称": user_name[0],
                        "发布时间": publication_time,
                        '帖子内容': article_content,
                        '发表方式': publication_model,
                        '转发数量': forward_count,
                        '评论数量': comment_count,
                        '点赞数量': like_count
                    }
                    writer.writerow(data_dict)

                    logging.info(f"Current Weibo count: {weibo_count}, User: {user_name[0]}, Time: {publication_time}, Content: {article_content}")

                except Exception as e:
                    logging.error(f"Error processing article: {e}")
                    continue

            time.sleep(0.6)

        except requests.RequestException as e:
            logging.error(f"Request error: {e}")
            break

logging.info("Data scraping completed successfully!")

