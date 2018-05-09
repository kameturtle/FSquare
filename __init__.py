from flask import Flask, render_template, request, url_for, redirect

import urllib.request
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

def search(key_word, name):
    url_dict = {"urls":[], "others":[]}
    key_word = key_word.replace(' ', '+')

    url = 'https://www.glassdoor.com/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword=' + key_word + '&sc.keyword=' + key_word + '&locT=&locId=&jobType='
    header = download(url)
    soup = BeautifulSoup(header, 'lxml')
    script = soup.find('script', type='application/ld+json')
    data = json.loads((script).text)
    total_num = int(data['numberOfItems'])

    # for i in range(0,total_num):
    for i in range(0, 2):
        header_child = download(data['itemListElement'][i]['url'])
        soup_child = BeautifulSoup(header_child, 'lxml')
        script_child = soup_child.find('script', type='application/ld+json')
        # print(script_child)
        data_child = json.loads((script_child).text, strict=False)
        print('Job Title = {}, Company = {}, URL = {}'.format(data_child['title'],data_child['hiringOrganization']['name'],data_child['url']))
        url_dict["urls"].append([data_child['title'],data_child['hiringOrganization']['name'],data_child['url']])
    return url_dict



@app.route('/')
def home_page():
	return render_template("main.html")

@app.route('/result/', methods=["GET","POST"])
def result_page():
    error = ''
    try:
        if request.method == "POST":
            attempted_jobTitle = request.form['jobTitle']
            attempted_location = request.form['location']
            if attempted_jobTitle != "" and attempted_location != "":
                url_dict = search(attempted_jobTitle, attempted_location)
                return render_template("result.html", TOPIC_DICT = url_dict)
            else:
                error = "Invalid credentials. Try Again!"
        return render_template("main.html")
    except Exception as e:
        return render_template("500.html", error = str(e))

@app.route('/login/', methods=["GET","POST"])
def login_page():
    error = ''
    try:
        if request.method == "POST":
            attempted_username = request.form['username']
            attempted_password = request.form['password']
            if attempted_username == "admin" and attempted_password == "password":
                return redirect(url_for('home_page'))
            else:
                error = "Invalid credentials. Try Again!"
        return render_template("login.html", error = error)
    except Exception as e:
        return render_template("500.html", error = str(e))



if __name__ == "__main__":
    app.run()
