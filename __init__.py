from flask import Flask, render_template, request, url_for, redirect, session, flash

import urllib.request
import re
from bs4 import BeautifulSoup
from urllib.error import URLError, HTTPError, ContentTooShortError
import json

import MySQLdb

from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
import gc

from functools import wraps

app = Flask(__name__)
app.secret_key = "super secret key"

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

def connection():
    conn = MySQLdb.connect(host="localhost",
                           user = "root",
                           passwd = "sorasora0421",
                           db = "FSquare_test")
    c = conn.cursor()

    return c, conn

@app.route('/', methods=["GET","POST"])
def home_page():
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

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))

    return wrap

@app.route("/logout/")
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('home_page'))


@app.route('/login/', methods=["GET","POST"])
def login_page():
    error = ''
    try:
        c, conn = connection()
        if request.method == "POST":

            data = c.execute("SELECT * FROM users WHERE username = '%s'" % (request.form['username']))
            #data = c.execute("SELECT * FROM users WHERE username = (%s)",thwart(request.form['username']))

            data = c.fetchone()[2]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']

                flash("You are now logged in")
                return redirect(url_for('home_page'))

            else:
                error = "Invalid credentials, try again."

        gc.collect()

        return render_template("login.html", error=error)

    except Exception as e:
        #flash(e)
        error = "Invalid credentials, try again!"
        return render_template("login.html", error = str(e)) 

class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the Terms of Service and Privacy Notice (updated Jan 22, 2015)', [validators.Required()])

@app.route('/register/', methods=["GET","POST"])   
def register_page():
    try:
        form = RegistrationForm(request.form)

        if request.method == "POST" and form.validate():
            username  = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))
            c, conn = connection()
            
            
            x = c.execute("SELECT * FROM users WHERE username = '%s'" % (username))
            #x = c.execute("SELECT * FROM users WHERE username = '%s'", thwart(username))

            if int(x) > 0:
                return render_template('register.html', form=form)

            else:
                c.execute("INSERT INTO users (username, password, email, tracking) VALUES ('%s', '%s', '%s', '%s')" % (username, password, email, "/introduction-to-python-programming/"))
                #c.execute("INSERT INTO users (username, password, email, tracking) VALUES (%s, %s, %s, %s)",(thwart(username), thwart(password), thwart(email), thwart("/introduction-to-python-programming/")))
            
                conn.commit()
                
                c.close()
                conn.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('home_page'))

        return render_template("register.html", form=form)

    except Exception as e:
        return(str(e))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", error = str(e))


if __name__ == "__main__":
    app.run()
