from wechatpy.enterprise import WeChatClient
import urllib.request
import json


def get_record(url):
    resp = urllib.request.urlopen(url)
    ele_json = json.loads(resp.read())
    return ele_json


def weather_check(weather_json_1, weather_json_2):
    # 0:晴 1:多云 2:阴
    if int(weather_json_1[1]['WP']) >= 3 or int(weather_json_2[2]['WP']) >= 3:
        return True
    else:
        return False


def weather_to_text(weather_json_1, weather_json_2):
    # generate report text
    title = '明日天气预报'
    if weather_json_1[1]['WP_NAME'] == weather_json_1[2]['WP_NAME']:
        weather_1 = weather_json_1[1]['WP_NAME']
    else:
        weather_1 = weather_json_1[1]['WP_NAME'] + '转' + weather_json_1[2]['WP_NAME']

    if weather_json_2[1]['WP_NAME'] == weather_json_2[2]['WP_NAME']:
        weather_2 = weather_json_2[1]['WP_NAME']
    else:
        weather_2 = weather_json_2[1]['WP_NAME'] + '转' + weather_json_2[2]['WP_NAME']

    text = weather_json_1[1]['STATION_NAME'] + ' 天气:' + weather_1 + \
                   ' 气温:' + str(weather_json_1[1]['T_MIN']) + '-' + str(weather_json_1[1]['T_MAX']) + \
                   ' 风力:' + weather_json_1[1]['WS_LEVEL'] + '\n' + \
                   weather_json_2[1]['STATION_NAME'] + ' 天气:' + weather_2 + \
                   ' 气温:' + str(weather_json_2[1]['T_MIN']) + '-' + str(weather_json_2[1]['T_MAX']) + \
                   ' 风力:' + weather_json_2[1]['WS_LEVEL']
    url = 'http://www.wz121.com/shortTermForecast/show'
    return title, text, url


if __name__ == '__main__':

    # wechat client
    client = WeChatClient('', '')

    # get weather
    wz121_weather_chashan_url = 'http://www.wz121.com/villageFroecast/townclick?areaCode=33030405'
    weather_json_chashan = get_record(wz121_weather_chashan_url)
    weather_json_chashan[1]['STATION_NAME'] = '茶山'
    weather_json_chashan[2]['STATION_NAME'] = '茶山'


    # 南白象
    if weather_check(weather_json_chashan):
        weather_title, weather_text, weather_url = weather_to_text(weather_json_chashan, weather_json_chashan)
        client.message.send_text_card(agent_id='1000003', user_ids='ChenYiGe', title=weather_title, description=weather_text, btntxt='详情', url=weather_url)


