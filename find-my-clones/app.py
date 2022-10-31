import argparse
import traceback
import yaml
import tweepy
import numpy as np
import pandas as pd
import os
import tempfile
import imageio as iio
import requests
import datetime

from flask import (
    Flask, request, render_template, Response,
    session, flash, redirect, url_for, jsonify,
    send_file
)
import flask

def get_user_info(screen_name,res=None):
    user = api.get_user(screen_name=screen_name)
    if res == 'high':
        url = user.profile_image_url.replace('_normal.jpg','_400x400.jpg')
    else:
        url = user.profile_image_url
    profile_image = get_image(url)
    return user,profile_image

def get_image(profile_url):
    with tempfile.TemporaryDirectory() as tmpdirname:
        response = requests.get(profile_url)
        filepath = os.path.join(tmpdirname,'profile.jpg')
        if response.status_code == 200:
            with open(filepath,'wb') as f:
                f.write(response.content)
            image=iio.v3.imread(filepath)
            return image
        else:
            return None


with open('apikey.yml','r') as f:
    secret = yaml.safe_load(f.read())

consumer_key = secret['consumer_key']
consumer_secret = secret['consumer_secret_key']
access_token = secret['access_token']
access_token_secret = secret['access_token_secret']
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

app = Flask(__name__,
    static_url_path='', 
    static_folder='static',
    template_folder='templates',
)

@app.route("/ping")
def ping():
    return jsonify(success=True)

@app.route('/find-my-clones', methods=['GET'])
def find_my_clones():
    return render_template('home.html',root_url="https://www.aigonewrong.com")

@app.route('/find-my-clones/v1/query_clones', methods=['GET'])
def query_clones():
    myresults = {}
    try:
        reference_screen_name = request.args.get('screen_name')
        user,reference_image = get_user_info(reference_screen_name)
        query = user.name
        myresults = dict(
            tstamp=datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S'),
            handle=reference_screen_name,
        )
    except:
        traceback.print_exc()
        myresults['error']='invalid handle'
        return jsonify(myresults)
    
    if reference_image is None:
        myresults['error']='handle have no profile pic'
        return jsonify(myresults)
    # find  page_count*items_per_page count that matches the query
    # API limit is 1k.
    fetch = []
    page_num = 10
    count_per_page = 100

    try:
        for x in range(page_num):
            print(f'querying page {x}')
            tmp = api.search_users(query,count=count_per_page,page=x)
            fetch.extend(tmp)
            if len(tmp)<count_per_page:
                break
    except:
        traceback.print_exc()
        myresults['error']='error occurred during querying.'
        return jsonify(myresults)
        
    print(len(fetch))
    
    # try to find a match based on profile image
    mylist = []
    profile_cache = {}
    user_cache = {}
    for n,x in enumerate(fetch):
        try:
            user,profile_image = get_user_info(x.screen_name)
            # skip item if its reference
            if user.screen_name == reference_screen_name:
                continue
            # if http error skip
            if profile_image is None:
                profile_cache[user.screen_name]=None
                continue
            # compute only if shape matches
            if profile_image.shape == reference_image.shape:
                item = dict(screen_name=user.screen_name,mean_pixel_diff=np.mean(profile_image-reference_image))
                profile_cache[user.screen_name]=profile_image.copy()
                user_cache[user.screen_name]=x
            else:
                item = dict(screen_name=user.screen_name,mean_pixel_diff=np.nan)
                profile_cache[user.screen_name]=None
                user_cache[user.screen_name]=x
            mylist.append(item)
        except:
            traceback.print_exc()
            continue

    if len(mylist)==0:
        myresults['result_count']=0
        myresults['results']=[]
        return jsonify(myresults)

    df = pd.DataFrame(mylist)
    df = df.sort_values('mean_pixel_diff')
    print(len(df))

    TH = 100 # empirically set threshold
    df = df[df.mean_pixel_diff<=TH]

    print(df.shape)

    matched_list = []
    for n,row in df.iterrows():
        user = user_cache[row.screen_name]
        screen_name = user.screen_name
        name = user.name
        url = f'https://twitter.com/{screen_name}'
        mean_pixel_diff = row.mean_pixel_diff

        item = dict(
            name=user.name,
            screen_name=screen_name,
            mean_pixel_diff=float(np.round(mean_pixel_diff,2)),
            url=url,
        )
        matched_list.append(item)

    myresults['result_count']=len(matched_list)
    myresults['results']=matched_list

    return jsonify(myresults)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p","--port",type=int,default=8080)
    args = parser.parse_args()
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True,host="0.0.0.0",port=args.port)


"""
curl -X GET localhost:8080/v1/query_clones?screen_name=VailshireCap

"""