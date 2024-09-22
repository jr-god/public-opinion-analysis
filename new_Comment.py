"""
抓取指定微博下的评论，递归找出一级评论、二级评论、三级评论等多级
cookie需要更换成自己微博账号的cookie
"""
# -*- coding: utf-8 -*-
import re
import requests
import pandas as pd
import os


def parseJson(jsonObj):
    data = jsonObj["data"]
    max_id = jsonObj["max_id"]
    # total_numberr = jsonObj["total_number"]

    commentData = []
    for item in data:
        try:
            comment_Id = item["id"]
            created_at = item["created_at"]
            # content = BeautifulSoup(item["text"], "html.parser").text
            content = re.sub(r'<.*?>', '', item["text"])
            like_counts = item["like_counts"]
            IP = item["source"]
            total_number = item.get("total_number", None)

            user = item["user"]
            userID = user["id"]
            userName = user["screen_name"]
            userCity = user["location"]
            userGender = user["gender"]
            userDescription = user["description"]
            userFollowers_count = user["followers_count"]
            userFriends_count = user["friends_count"]
            statuses_count = user["statuses_count"]

            verified = user.get("verified", None)
            if verified is not None:
                verified_reason = user.get("verified_reason", None)
            else:
                verified_reason = None

            icon_list = user.get("icon_list", None)
            if icon_list is not None and icon_list:
                icon_type = user["icon_list"][0]["type"]
            else:
                icon_type = None

            dataItem = [
                comment_Id, created_at, userID, userName, userGender,
                userDescription, userCity, IP, userFollowers_count,
                userFriends_count, statuses_count, like_counts, total_number,
                content, verified_reason, icon_type
            ]

            commentData.append(dataItem)
            # time.sleep(2)
            # print(dataItem)

        except Exception as e:
            print("Error:", e)

        except KeyError as e:
            # 处理缺失项
            print("Missing key:", e)
    return commentData, max_id


def fetchUrl(id, uid, max_id, fetch_level):
    """
    获取某一微博下的评论
    Args:
        id: 该微博的ID
        uid: 用户ID
        max_id: 游标，第一层评论，无max_id
        fetch_level: 第几层评论

    Returns:

    """
    url = "https://weibo.com/ajax/statuses/buildComments"
    # 第一层评论
    if max_id is None:
        # 第一层评论的第一页
        params = {
            "flow": 0,
            "is_reload": "1",
            "id": id,
            "is_show_bulletin": "2",
            "is_mix": 0,
            "count": 10,
            "uid": uid,
            "fetch_level": fetch_level,
            "locale": "zh - CN",
        }
    else:
        # 第一层评论的后续页
        params = {
            "flow": 0,
            "is_reload": "1",
            "id": id,
            "is_show_bulletin": "2",
            "is_mix": 0,
            "max_id": max_id,
            "count": 20,
            "uid": uid,
            "fetch_level": fetch_level,
            "locale": "zh - CN",
        }

    # 第二层及后续评论
    if fetch_level > 0:
        params = {
            "is_reload": "1",
            "id": id,
            "is_show_bulletin": "2",
            "is_mix": 1,
            "fetch_level": fetch_level,
            "max_id": max_id,
            "count": "20",
            "uid": uid,
            "locale": "zh - CN",
        }

    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "referer": "https://weibo.com/newlogin?tabtype=weibo&gid=102803&openLoginLayer=0&url=https%3A%2F%2Fweibo.com%2F",
        # 需要cookie
        "cookie": "SUB=_2AkMRE4MDf8NxqwFRmfwUxG7mb4xwwwzEieKnT3LYJRMxHRl-yT9vqm9StRB6OpOt7Q-_NXZo_xl2ud2DOddN1qGKzCwy; SUBP=0033WrSXqPxfM72-Ws9jqgMF55529P9D9WhFbfqUfbHh_xqEEdBVP_r0; XSRF-TOKEN=Du0XTBgr0o9VVBmyhUBUegsX; WBPSESS=Wk6CxkYDejV3DDBcnx2LOW7i28QwWF45VjxUlhWWNhMjhNV7mEhphwqNByH-OBabx9KXb8NvDFnVUtqYYfVxvooBOMYjiwIwHDBRg7dTe1GqotkpYc11TvORahUSX5e18kpmMakjKywhlD2fFkYtcbjDbZyeIJs54YJE2BPkuf0=",
    }

    r = requests.get(url, headers=headers, params=params)
    res = r.json()
    comments, max_id = parseJson(res)
    return comments, max_id


# 标记一下已经处理过的max_id
max_id_pool = []


def fetch_comment(id, uid, max_id, fetch_level):
    """
    递归获取某一微博下的评论
    Args:
        id: 该微博的ID
        uid: 用户ID
        max_id: 游标
        fetch_level: 第几层评论

    Returns:

    """
    global max_id_pool
    result = []
    comments, return_max_id = fetchUrl(id, uid, max_id, fetch_level)

    print(f'===> 层级：{fetch_level}, 父ID：{id}, max_id：{max_id}, 评论数量：{len(comments)}')

    if return_max_id == 0:
        result.extend(comments)
        return result
    if return_max_id in max_id_pool:
        return result
    result.extend(comments)
    max_id_pool.append(return_max_id)

    for comment in comments:
        child_id = comment[0]
        child_max_id = 0
        child_result = fetch_comment(child_id, uid, child_max_id, fetch_level + 1)
        result.extend(child_result)

    # 第一层往下翻
    next_result = fetch_comment(id, uid, return_max_id, fetch_level)
    result.extend(next_result)

    return result


# 保存
def save_data(data, path, filename):
    if not os.path.exists(path):
        os.makedirs(path)

    dataframe = pd.DataFrame(data)
    dataframe.to_csv(r'国足.csv', encoding='utf-8', mode='a', index=False, sep=',', header=False)


if __name__ == "__main__":
    # pid = 5074896665444884  # 微博id，固定
    # uid = 7711753752  # 用户id，固定
    # max_id = 0

    id = 5074896665444884
    uid = 7711753752
    max_id = None
    fetch_level = 0

    print('start fetch comment')
    data = fetch_comment(id, uid, max_id, fetch_level)
    print(f'该微博（id：{id}）下获取到的总评论数为：{len(data)}')

    csvHeader = [["评论id", "发布时间", "用户id", "用户昵称", "用户性别", "用户介绍", "用户城市", "用户IP", "粉丝数",
                  "好友数", "用户微博数", "点赞数", "回复数", "评论内容", "用户认证情况", "用户会员情况"]
                 ]
    data = pd.DataFrame(data)
    data = pd.concat([pd.DataFrame(csvHeader), data])
    data.to_excel(r'国足4.xlsx', index=False)
