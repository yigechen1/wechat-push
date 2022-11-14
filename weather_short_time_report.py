# encoding:utf-8
from wechatpy.enterprise import WeChatClient
import requests
import os
import re
import hashlib
from PIL import Image
import numpy as np


def rgb_to_hsv(r, g, b):
    # R, G, B values are divided by 255
    # to change the range from 0..255 to 0..1:
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    # h, s, v = hue, saturation, value
    cmax = max(r, g, b)  # maximum of r, g, b
    cmin = min(r, g, b)  # minimum of r, g, b
    diff = cmax-cmin   # diff of cmax and cmin.
    # if cmax and cmax are equal then h = 0
    if cmax == cmin:
        h = 0
    # if cmax equal r then compute h
    elif cmax == r:
        h = (60 * ((g - b) / diff) + 360) % 360
    # if cmax equal g then compute h
    elif cmax == g:
        h = (60 * ((b - r) / diff) + 120) % 360
    # if cmax equal b then compute h
    elif cmax == b:
        h = (60 * ((r - g) / diff) + 240) % 360
    # if cmax equal zero
    if cmax == 0:
        s = 0
    else:
        s = (diff / cmax) * 100
    # compute v
    v = cmax * 100
    return h, s, v


def graph_crop_match():
    img = Image.open('nowcasting.png')

    # find the upper line of the graph
    # line pos 357
    img_array = np.array(img)
    img_array_r = img_array[:,:,0]
    img_array_r_y = img_array_r.mean(axis=1)
    for y_index, value in enumerate(img_array_r_y):
        if value < 150:
            break

    img_array_r_x = img_array_r.mean(axis=0)
    for x_index, value in enumerate(img_array_r_x):
        if value < 165:
            break

    # crop the downtown piece
    #focused = img.crop((440, 550, 476, 586))  # downtown, including shuangyu, louqiao, chashan
    focused = img.crop((x_index + 286, y_index + 193, x_index + 322, y_index + 229))  # downtown, including shuangyu, louqiao, chashan
    focused.save('croped.jpg', quality=95)

    focused_np = np.array(focused)

    # calc h value
    h_array = []
    for row in focused_np:
        h_row = []
        for rgb in row:
            h, _, _ = rgb_to_hsv(rgb[0], rgb[1], rgb[2])
            h_row.append(h)
        h_array.append(h_row)

    h_array = np.array(h_array)
    h_array_t = h_array.T[::-1]

    # chashan
    h_array_chashan = np.triu(h_array_t)

    # num n*(n+1)/2
    h_array_item_num = (h_array.shape[0])*(h_array.shape[1]+1)/2

    # calc h average
    h_average_chashan = h_array_chashan.sum()/h_array_item_num

    return h_average_chashan > 15


def get_file_md5(url):

    file_response = requests.get(url)
    file_response_byte = file_response.content
    with open('nowcasting.png', 'wb') as fp_w:
        fp_w.write(file_response_byte)
    h = hashlib.new('md5')
    h.update(file_response_byte)
    file_response_md5 = h.hexdigest()

    return file_response_md5


def read_history(file_name):
    if os.path.exists(file_name):
        with open(file_name) as fp:
            file_lines = fp.readlines()
            warn_history = [line.strip() for line in file_lines]
    else:
        warn_history = []

    return warn_history


def get_report_baidu():
    # get access_token
    client_id = 'mglyrwNswh69BB2SVPmdjYeF'
    client_secret = 'iygxEGPxQmfQLH9ylaHj39RNDGBNpg0E'
    token_host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + client_id + '&client_secret=' + client_secret
    token_response = requests.get(token_host)
    token_response_json = token_response.json()
    access_token = token_response_json['access_token']

    # use api to get text
    api_request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/webimage"
    api_params = {"url":'http://www.wz121.com/dsyb/nowcasting.jpg'}
    api_request_url = api_request_url + "?access_token=" + access_token
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(api_request_url, data=api_params, headers=headers)
    report_json = response.json()

    report_text = ''
    for words in report_json['words_result'][1:]:
        report_text += words['words']
        if '鹿城区' in report_text and '瓯海区' in report_text and '龙湾区' in report_text:
            break

    report_text = re.sub(r'洞头区[0-9\-]+', '', report_text, flags=re.I )
    report_text = re.sub(r'永嘉县[0-9\-]+', '', report_text, flags=re.I )
    report_text = re.sub(r'乐清市[0-9\-]+', '', report_text, flags=re.I )
    report_text = re.sub(r'瑞安市[0-9\-]+', '', report_text, flags=re.I )
    report_text = re.sub(r'平阳县[0-9\-]+', '', report_text, flags=re.I )
    report_text = re.sub(r'泰顺县[0-9\-]+', '', report_text, flags=re.I )
    report_text = re.sub(r'文成县[0-9\-]+', '', report_text, flags=re.I )
    report_text = re.sub(r'苍南县[0-9\-]+', '', report_text, flags=re.I )
    report_text = re.sub(r'龙港市[0-9\-]+', '', report_text, flags=re.I )

    line_0_index = report_text.index('发布预计')
    line_1_index = report_text.index('1.预计未来')
    line_2_index = report_text.index('2.预计雨量')

    report_text = report_text[:line_0_index + 2] + '\n' + \
                  report_text[line_0_index + 2:line_1_index] + '\n' + \
                  report_text[line_1_index:line_2_index] + '\n' + \
                  report_text[line_2_index:]
    return report_text


if __name__ == '__main__':

    # check new report
    history_file_path = 'weather_short_time_history.txt'
    short_time_history = read_history(history_file_path)

    report_url = 'http://www.wz121.com/dsyb/nowcasting.jpg'
    report_md5 = get_file_md5(report_url)
    if report_md5 not in short_time_history:
        # save report md5
        with open(history_file_path, 'a+') as fp_a:
            fp_a.write(report_md5 + '\n')

        # get report text
        report_title = '短时降雨预报'
        report_text = get_report_baidu()

        graph_match_chashan = graph_crop_match()

        # send report
        client = WeChatClient('', '')
        if graph_match_chashan:
            client.message.send_text_card(agent_id='', user_ids='', title=report_title, description=report_text, btntxt='详情', url=report_url)
