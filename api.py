# -*- coding: UTF-8 -*-
"""
API调用模块
负责与晋江Android API通信、章节内容获取和解密
"""
import requests
import json
import re
import time

import DESCBC


def get_headers():
    """获取请求头"""
    return {"User-Agent": "Mobile " + time.asctime()}


def _get(url, **kwargs):
    """只对连接异常、限流和服务端错误重试，所有请求都设置超时。"""
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=(10, 30), **kwargs)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == 2:
                raise
        else:
            if response.status_code != 429 and response.status_code < 500:
                try:
                    response.raise_for_status()
                except requests.HTTPError:
                    response.close()
                    raise
                return response
            if attempt == 2:
                try:
                    response.raise_for_status()
                finally:
                    response.close()
            response.close()
        time.sleep(0.5 * (2 ** attempt))


def fetch_novel_info(novel_id, include_web=False):
    """
    获取小说基本信息和章节列表
    :param novel_id: 小说ID
    :param include_web: 是否额外请求网页文案
    :return: (apicont, cdic, ress) 小说信息dict、章节列表list、网页解析结果
    """
    from lxml import etree

    req_url = f'https://www.jjwxc.net/onebook.php?novelid={novel_id}'
    apireq = f'https://app.jjwxc.net/androidapi/novelbasicinfo?novelId={novel_id}'
    apivol = f'https://app.jjwxc.net/androidapi/chapterList?novelId={novel_id}&more=0&whole=1'

    # 获取API信息
    ress = None
    with _get(apireq, headers=get_headers()) as apires:
        apicont = apires.json()

    if "message" in apicont and "novelIntro" not in apicont:
        return apicont, None, ress

    # 获取章节列表
    with _get(apivol, headers=get_headers()) as rc:
        cdic = rc.json()['chapterlist']
    if include_web:
        with _get(req_url, headers=get_headers()) as res:
            ress = etree.HTML(res.content.decode('GB18030', 'ignore'))

    return apicont, cdic, ress


def fetch_chapter_content(chapter_url, token):
    """
    获取并解密单个章节的原始内容
    :param chapter_url: 章节API URL
    :param token: 用户token
    :return: dict with keys: content, sayBody, upDown, message, chapterSize, chapterDate
             content已解密，如果获取失败则content为空字符串
    """
    full_url = chapter_url + '&versionCode=349&token=' + token

    result = {
        'content': '',
        'sayBody': '',
        'upDown': '',
        'message': '',
        'chapterSize': '',
        'chapterDate': '',
    }

    with _get(full_url, headers=get_headers()) as chcot:
        try:
            chcont = json.loads(chcot.text)
        except json.JSONDecodeError:
            chcont = json.loads(DESCBC.decrypt_content(chcot))

        if 'message' not in chcont.keys():
            tex = chcont['content']
            tex = DESCBC.decrypt_str(tex).decode('utf-8')
            tex = re.sub('&lt;br&gt;', '\n', tex)

            result['content'] = tex
            result['sayBody'] = chcont.get('sayBody', '')
            result['upDown'] = chcont.get('upDown', '')
            result['chapterSize'] = chcont.get('chapterSize', '')
            result['chapterDate'] = chcont.get('chapterDate', '')
        else:
            result['message'] = chcont["message"]

    return result


def download_cover(cover_url):
    """
    下载封面图片
    :param cover_url: 封面URL
    :return: 图片二进制数据或None
    """
    if not cover_url:
        return None

    if re.findall(r'i9-static.jjwxc.net', cover_url):
        return None

    try:
        with _get(cover_url) as pres:
            return pres.content
    except Exception:
        return None
