from wechatpy.enterprise import WeChatClient
import requests
import json
import os
import datetime
import time
import re

# SMZDM 1000006
client = WeChatClient('', '')


def get_record(url):
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers)
        res_json = json.loads(res.content)
        return res_json
    except:
        return []


def read_history(file_name):
    if os.path.exists(file_name):
        with open(file_name, encoding='utf-8') as fp:
            file_lines = fp.readlines()
            item_history = [line.strip() for line in file_lines]
    else:
        item_history = []

    item_set = set()
    for item in item_history:
        item_split = item.split('\t')
        item_id = int(item_split[1])
        item_set.add(item_id)

    return item_history, item_set


def save_history(file_history, new_items):
    with open('smzdm_history.txt', 'w') as fp:
        # filter old items
        for item in file_history:
            item_split = item.split('\t')
            item_date = item_split[0]

            if len(item_date) == 5:
                item_date = time.strftime("%m-%d ") + item_date

            item_date_format = time.strptime(time.strftime("%Y-") + item_date, "%Y-%m-%d %H:%M")
            days_ago_date = datetime.datetime.now() - datetime.timedelta(days=10)

            if item_date_format > days_ago_date.timetuple():
                fp.write(item + '\n')
        # save new items
        for item in new_items:
            item_id = item['article_id']
            item_date = item['article_date']
            if len(item_date) == 5:
                item_date = time.strftime("%m-%d ") + item_date
            fp.write(item_date + '\t' + str(item_id) + '\n')


def important_date():
    today = datetime.date.today()

    # 618
    start_1 = datetime.date(today.year, 6, 1)
    end_1 = datetime.date(today.year, 6, 20)

    # 1111
    start_2 = datetime.date(today.year, 10, 31)
    end_2 = datetime.date(today.year, 11, 13)

    # 1212
    start_3 = datetime.date(today.year, 12, 1)
    end_3 = datetime.date(today.year, 12, 14)

    if start_1 < today < end_1 or start_2 < today < end_2 or start_3 < today < end_3:
        return True
    else:
        return False


def smzdm_filter_hot(smzdm_items):
    smzdm_important_items = []
    smzdm_hot_items = []
    error_item = 0
    for item in smzdm_items:
        if 'article_rating' in item and 'article_collection' in item and 'article_comment' in item:
            article_rating = item['article_rating']
            article_comment = item['article_comment']
            # article_collection = int(item['article_collection'])
            if isinstance(article_rating, int) and isinstance(article_comment, int):
                if article_rating >= 200 and article_comment >= 100:
                    smzdm_hot_items.append(item)
                elif article_rating >= 30 and article_comment >= 20:
                    smzdm_important_items.append(item)
            else:
                smzdm_hot_items.append(item)
        else:
            error_item += 1

    return smzdm_important_items, smzdm_hot_items, error_item


def smzdm_filter_keyword(smzdm_items):
    # read key words
    focus_key_words = []
    with open('smzdm_focus_key_word.txt', encoding='utf-8') as fp:
        filelines = fp.readlines()
        for line in filelines:
            line = line.strip()
            if '#' in line or line == '':
                continue
            else:
                line_split = line.split(' ')
                focus_key_words.append(line_split)

    # filter
    smzdm_important_items = []
    for item in smzdm_items:
        filter_flag = False
        item_title_lower_case = item['article_title'].lower()

        for fkw in focus_key_words:
            fkw_flag = True
            for sub_word in fkw:
                if sub_word.lower() not in item_title_lower_case:
                    fkw_flag = False
                    break

            if fkw_flag:
                filter_flag = True
                break

        if filter_flag:
            smzdm_important_items.append(item)

    return smzdm_important_items


if __name__ == '__main__':
    history_file_path = 'smzdm_history.txt'
    item_history, item_set = read_history(history_file_path)

    # check if today is 618, 1111, or 1212
    if important_date():
        range_max = 250
    else:
        range_max = 10

    # fetch SMZDM items
    smzdm_items = []
    for i in range(1, range_max + 1):
        time.sleep(1)
        smzdm_url = 'https://faxian.smzdm.com/json_more?filter=h4s0t0f0c0&page=' + str(i)
        smzdm_json = get_record(smzdm_url)
        smzdm_items.extend(smzdm_json)
        print(smzdm_url, ' page_item:', len(smzdm_json))

    # filter SMZDM item according to item hot index
    smzdm_items_filter1, smzdm_hot_items, error_item = smzdm_filter_hot(smzdm_items)

    # filter SMZDM item according to key words
    smzdm_items_filter2 = smzdm_filter_keyword(smzdm_items_filter1)

    # filter SMZDM hot item according to forbidden words
    smzdm_items_filter3 = smzdm_filter_keyword(smzdm_items_filter1)

    # filter items in history
    new_items = []
    for item in smzdm_items_filter2 + smzdm_hot_items:
        item_id = item['article_id']
        if item_id not in item_set:
            new_items.append(item)

    print('crawled_item:', len(smzdm_items), ' important_item', len(smzdm_items_filter2), ' hot_item:', len(smzdm_hot_items), ' new_item:', len(new_items), ' error_item:', error_item)

    # push the item information
    for item in new_items:
        article_title = item['article_title']
        article_price = item['article_price']
        article_content = item['article_content']
        article_content = re.sub('<.+?>', '', article_content)
        article_rating = str(item['article_rating'])
        article_collection = str(item['article_collection'])
        article_comment = str(item['article_comment'])
        article_url = item['article_url']

        client.message.send_text_card(agent_id='', user_ids='', title=article_title + ' ' + article_price,
                                      description=article_price + '\n' +
                                                  '点值：' + article_rating +
                                                  ' 收藏：' + article_collection +
                                                  ' 评论：' + article_comment + '\n' +
                                                  article_title + '\n' +
                                                  article_content, btntxt='详情', url=article_url)

    save_history(item_history, new_items)

