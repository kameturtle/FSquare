from flask import Flask, render_template, request, jsonify
import urllib.request
import requests
import re
from bs4 import BeautifulSoup

from urllib.error import URLError, HTTPError, ContentTooShortError
import json

app = Flask(__name__)


def download(url, user_agent='wswp', num_retries=2, charset='utf-8'):
    print('Downloading:', url)
    request = urllib.request.Request(url)
    request.add_header('User-agent', user_agent)
    try:
        resp = urllib.request.urlopen(request)
        cs = resp.headers.get_content_charset()
        if not cs:
            cs = charset
        html = resp.read().decode(cs)
    except (URLError, HTTPError, ContentTooShortError) as e:
        print('Download error:', e.reason)
        html = None
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                # recursively retry 5xx HTTP errors
                return download(url, num_retries - 1)
    return html


@app.route('/')
def index():
    print("a")
    return render_template('form.html')


@app.route('/process', methods=['POST'])
def process():
    key_word = request.form['email']
    name = request.form['name']
    url_set = set()

    key_word = key_word.replace(' ', '+')
            
    url = 'https://www.glassdoor.com/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword=' + key_word + '&sc.keyword=' + key_word + '&locT=&locId=&jobType='
    header = download(url)
    soup = BeautifulSoup(header, 'lxml')
    script = soup.find('script', type='application/ld+json')
    data = json.loads((script).text)

    total_num = int(data['numberOfItems'])

    # for i in range(0,total_num):
    for i in range(0, 1):
        header_child = download(data['itemListElement'][i]['url'])
        soup_child = BeautifulSoup(header_child, 'lxml')
        script_child = soup_child.find('script', type='application/ld+json')
        # print(script_child)
        data_child = json.loads((script_child).text, strict=False)
        print('Job Title = {}, Company = {}, URL = {}'.format(data_child['title'],
                                                              data_child['hiringOrganization']['name'],
                                                              data_child['url']))
        url_set.add(data_child['url'])
    return jsonify({'name': url_set.pop(), 'email': key_word})


if __name__ == '__main__':
    app.run(debug=True)
