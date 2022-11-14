from wechatpy.enterprise import WeChatClient
import urllib.request
import json
import os

# 天气提醒 企业微信
client = WeChatClient('', '')


def get_record(url):
    resp = urllib.request.urlopen(url)
    ele_json = json.loads(resp.read())
    return ele_json


def read_history(file_name):
    if os.path.exists(file_name):
        with open(file_name) as fp:
            file_lines = fp.readlines()
            warn_history = [line.strip() for line in file_lines]
    else:
        warn_history = []

    return warn_history


if __name__ == '__main__':
    history_file_path = 'weather_warn_history.txt'
    warn_history = read_history(history_file_path)

    wz121_weather_shuangyu_url = 'http://www.wz121.com/villageFroecast/townclick?areaCode=33030207'
    wz121_weather_panqiao_url = 'http://www.wz121.com/villageFroecast/townclick?areaCode=33030411'
    wz121_weather_nanbaixiang_url = 'http://www.wz121.com/villageFroecast/townclick?areaCode=33030405'

    wz121_warn_url = 'http://www.wz121.com/map/getWeatherWarn'
    warn_json = get_record(wz121_warn_url)
    for warn_item in warn_json:
        if '温州市气象台' in warn_item['WARN_CONTENT']:
            publish_date = warn_item['publishDate']
            warn_code = warn_item['WARN_CODE']
            warn_title = warn_item['title']
            warn_content = warn_item['WARN_CONTENT']
            warn_type = warn_item['WARN_TYPE']
            warn_level = warn_item['WARN_LEVEL']
            warn_id = warn_item['PID']

            message_title = warn_title + publish_date
            message_descroption = warn_content
            message_url = 'http://www.wz121.com/warningsignal/warningInfoDetail?id=' + warn_id

            if warn_id not in warn_history:
                # send message
                client.message.send_text_card(agent_id='', user_ids='', title=message_title, description=message_descroption, btntxt='详情', url=message_url)

                # save history
                warn_history.append(warn_id)
                with open(history_file_path, 'a+') as fp_a:
                    fp_a.write(warn_id + '\n')

