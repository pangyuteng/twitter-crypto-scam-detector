import argparse
import traceback
import yaml
import re
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
api = tweepy.API(auth,wait_on_rate_limit=True)

app = Flask(__name__,
    static_url_path='', 
    static_folder='static',
    template_folder='templates',
)

@app.route("/ping")
def ping():
    return jsonify(success=True)

#https://stackoverflow.com/questions/1276764/stripping-everything-but-alphanumeric-chars-from-a-string-in-python
# some names have odd chars, strip it down to friendly chars.
from string import ascii_letters, digits
def specialstrip(InputString):
    return "".join([ch for ch in InputString if ch in (ascii_letters + digits)])

def _query_clones(reference_screen_name):

    myresults = dict(
        handle=reference_screen_name,
        tstamp=datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S'),
    )

    try:
        user,reference_image = get_user_info(reference_screen_name)
        user_name = user.name
        query_list = [reference_screen_name,user_name]
        query_list.extend(user.description.split('\n'))
    except:
        traceback.print_exc()
        myresults['error']=f'invalid handle! \n{traceback.format_exc()}'
        myresults['result_count']=0
        return myresults
    
    if reference_image is None:
        myresults['error']='handle have no profile pic'
        myresults['result_count']=0
        return myresults
    # find  page_count*items_per_page count that matches the query
    # API limit is 1k.
    fetch = []
    page_num = 10
    count_per_page = 100

    try:
        for query in query_list:
            for x in range(page_num):
                print(f'querying page {x}')
                tmp = api.search_users(query,count=count_per_page,page=x)
                fetch.extend(tmp)
                if len(tmp)<count_per_page:
                    break
    except:
        traceback.print_exc()
        myresults['error']=f'error occurred during querying. {traceback.format_exc()}'
        myresults['result_count']=0
        return myresults
        
    print(len(fetch))
    
    # try to find a match based on profile image
    mylist = []
    profile_cache = {}
    user_cache = {}
    for n,item in enumerate(fetch):
        try:
            user,profile_image = get_user_info(item.screen_name)
            # skip item if its reference
            if user.screen_name == reference_screen_name:
                continue
            # if http error skip
            if profile_image is None:
                profile_cache[user.screen_name]=None
                continue
            # compute only if shape matches
            if profile_image.shape == reference_image.shape:
                x = profile_image.ravel()
                y = reference_image.ravel()
                c=np.corrcoef(x,y)
                sim_val = c[0,1]
                item = dict(screen_name=user.screen_name,sim_val=sim_val)
                profile_cache[user.screen_name]=profile_image.copy()
                user_cache[user.screen_name]=user
            else:
                item = dict(screen_name=user.screen_name,sim_val=np.nan)
                profile_cache[user.screen_name]=None
                user_cache[user.screen_name]=user
            mylist.append(item)
        except:
            traceback.print_exc()
            continue

    if len(mylist)==0:
        myresults['result_count']=0
        myresults['results']=[]
        return myresults

    df = pd.DataFrame(mylist)
    df = df.sort_values('sim_val',ascending=False)
    print(len(df))

    TH = 0.6
    df = df[df.sim_val>=TH]

    print(df.shape)

    matched_list = []
    for n,row in df.iterrows():
        user = user_cache[row.screen_name]
        screen_name = user.screen_name
        stripped_name = specialstrip(user.name)
        profile_url = f'https://twitter.com/{screen_name}'
        sim_val = row.sim_val

        item = dict(            
            handle=screen_name,
            profile_url=profile_url,
            profile_image_url=user.profile_image_url,
            corr_coef=float(np.round(sim_val,2)),
            name=stripped_name,
        )

        # remove reference, and duplicates.
        if screen_name == reference_screen_name:
            continue
        if item in matched_list:
            continue

        print(user.name)
        print(len(user.name),'!!')
        matched_list.append(item)

    myresults['result_count']=len(matched_list)
    myresults['results']=matched_list
    return myresults

@app.route('/find-my-clones', methods=['GET'])
def find_my_clones():
    reference_screen_name = request.args.get('screen_name',None)
    if reference_screen_name is not None:
        result_dict = _query_clones(reference_screen_name)
    else:
        result_dict = {}
    print(result_dict)
    return render_template('home.html',
        result_dict=result_dict,
    )

# @app.route('/find-my-clones/v1/query_clones', methods=['GET'])
# def query_clones():
#     reference_screen_name = request.args.get('screen_name')    
#     myresults = _query_clones(reference_screen_name)
#     return jsonify(myresults)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p","--port",type=int,default=8080)
    args = parser.parse_args()
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True,host="0.0.0.0",port=args.port)


"""
curl -X GET localhost:8080/v1/query_clones?screen_name=VailshireCap

"""
