import os
import requests
import re
from datetime import datetime, timedelta
from pyquery import PyQuery as pq

COOKIE = os.getenv('cookie')


def local_time(str):
    parsed = datetime.strptime(str, '%d-%m, %H:%M')
    converted = parsed + timedelta(hours=8)
    return converted.strftime('%d-%m, %H:%M')


def get_latest_posts():
    url = 'https://www.unknowncheats.me/forum/'
    response = requests.get(url + 'infopanels.php?do=ajax&action=stats&isdetached=0&blocks[1]=1', headers={'Cookie': COOKIE})
    response.raise_for_status()
    start_index = response.text.find('<![CDATA[')
    end_index = response.text.find(']]>')
    if start_index == -1 or end_index == -1:
        return []
    block = response.text[start_index + 9 : end_index]
    doc = pq(block)
    posts = []
    for tr in doc('tr').items():
        td = tr('td')
        posts.append(
            (
                td.eq(0).text().replace('|', '\|').replace('[', '\[').replace(']', '\]'),
                url + td.eq(1)('a').eq(1).attr('href').replace('-new-post.html', '.html'),
                local_time(td.eq(2).text()),
                td.eq(3).text(),
            )
        )
    return posts


def load_posts(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return re.findall(r'^\|\[(.*?)\]\((.*?)\)\|`(.*?)`\|(.*?)\|$', str.join('', file.readlines()), re.MULTILINE)
    except FileNotFoundError:
        return []


def save_posts(filename, posts):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write('|Post|Date|Forum|\n')
        file.write('|----|----|-----|\n')
        for post in posts:
            file.write('|[%s](%s)|`%s`|%s|\n' % post)


def make_posts(prev_posts, curr_posts):
    new_posts = []
    for curr_post in curr_posts:
        found = False
        for prev_post in prev_posts:
            if prev_post[0] == curr_post[0]:
                found = True
                break
        if not found:
            new_posts.append(curr_post)
    return new_posts + prev_posts


def job():
    filename = datetime.now().strftime('%Y-%m-%d.md')
    prev_posts = load_posts(filename)
    curr_posts = get_latest_posts()
    save_posts(filename, make_posts(prev_posts, curr_posts))


if __name__ == '__main__':
    job()
