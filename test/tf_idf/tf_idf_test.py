import math
from bs4 import BeautifulSoup
import urllib.request
import json

from textblob import TextBlob as tb

def a(var1, var2):
    return var1+var2

def tf(word, blob):
    return blob.words.count(word) / len(blob.words)

def n_containing(word, bloblist):
    return sum(1 for blob in bloblist if word in blob.words)

def idf(word, bloblist):
    return math.log(len(bloblist) / (1 + n_containing(word, bloblist)))

def tfidf(word, blob, bloblist):
    return tf(word, blob) * idf(word, bloblist)


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


def readDescription(url, website, skill_dict):
    """
        Args:
            skill_list : existing skill list
            url: url of the job description page 
            website: website name (e.g. "glassdoor", "indeed", "linkedin")
        Returns:
            skill_set: list of skills appeared in the job description sorted by the frequency
            forF1Student: boolean
    """
    skill_set = []
    if website == "glassdoor":
        html = download(url)
        soup = BeautifulSoup(html, 'lxml')
        script = soup.find('script', type='application/ld+json')
        data = json.loads((script).text, strict=False)
        print(data["description"])
        
        jobDescription = tb(data["description"])
        scores = {word: tf(word, jobDescription) for word in jobDescription.words}
        sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for word, score in sorted_words[:len(sorted_words)-1]:
            print("\tWord: {}, TF-IDF: {}".format(word, round(score, 5)))
            if word in skill_list:    
                skill_set.append(word)
        return skill_set

if __name__ == '__main__':
    #url = "https://www.glassdoor.com/job-listing/programmer-analyst-nbec-nwoca-JV_IC3785292_KO0,18_KE19,29.htm?jl=2782957743"
    url = "https://www.glassdoor.com/job-listing/software-developer-oakland-schools-JV_IC1134743_KO0,18_KE19,34.htm?jl=2730807060"
    skill_list = ["Java", "SQL"]
    website = "glassdoor"
    skill_set = readDescription(url, website, skill_list)
    for skill in skill_set:
        print(skill)

#TODO
#      