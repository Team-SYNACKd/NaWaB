#!/usr/bin/env python2

import json
import config
import tweepy
import mmap
import time
import random
import pandas as pd
from datetime import date
import tg_config as tg
import telegram
import csv

# Banned handles and words
banned_accs =  []
banned_words = []
whitelist_accs = []

data = pd.read_csv("data.csv")
tid = pd.read_csv("tid_store.csv")

def nawab_twitter_authenticate():
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token_key, config.access_token_secret)
    api = tweepy.API(auth)
    return api

def nawab_read_list():
    proto_list = pd.Series(data['Proto_list'])
    search_term = list(proto_list)
    return search_term

def nawab_store_id(tweet_id):
    ### Store a tweet id in a file
    with open("tid_store.csv","a") as fp:
        append=csv.writer(fp)
        append.writerow(str(tweet_id))
        
def nawab_get_blacklist():
    ser = pd.Series(data['Blacklist'])
    for line in ser:
        if "#DO_NOT_REMOVE_THIS_LINE#" not in str(line):
            banned_accs.append(line.strip())

def nawab_get_bannedwords():
    ser = pd.Series(data['Banwords'])
    for line in ser:
        if "#DO_NOT_REMOVE_THIS_LINE#" not in str(line):
            banned_words.append(line.strip())

def nawab_get_whitelist():
     ser = pd.Series(data['Whitelist'])
     for line in ser:
        if "#DO_NOT_REMOVE_THIS_LINE#" not in str(line):
            whitelist_accs.append(line.strip())

def isUserwhitelisted(userName):
    if not any(acc == userName.lower() for acc in whitelist_accs):
        return True
    return False

def isUserBanned(userName):
    if not any(acc == userName.lower() for acc in banned_accs):
        return True
    return False

"""Get banned words for a safer content tweets by nawab"""
def isSafeKeyword(tweetText):
    if not any(word in tweetText.lower() for word in banned_words):
        return True
    return False

def nawab_get_id():
    ### Read the last retweeted id from a file
    ser = pd.Series(tid['id'])
    for line in ser:
        return line
        
def nawab_check_tweet(tweet_id):
    ser = pd.Series(tid['id'])
    for i in ser:
        if i == tweet_id:
            return True
    return False
    
def nawab_curate_list(api):
    query = nawab_read_list()
    nawab_search(api, query)

def nawab_search(api, query):
    tweet_limit = 1
    latest_date = date.today()

    try:
        last_id = nawab_get_id()
    except FileNotFoundError as e:
        fp = open("nawab_errors.log", "a")
        fp.write("No tweet id found, hence assuming no file created and therefore creating the new file \n")
        f = open("tid_store.txt", "w+")
        last_id = None

    if len(query) > 0:
        for line in query:
            
            with open("nawab_results.log", "a") as fp:
                fp.write("starting new query search: \t" + line + "\n")

            try:
                for tweets in tweepy.Cursor(api.search, q=line, tweet_mode="extended", 
                        lang='en', since=latest_date).items(tweet_limit):
                    user = tweets.user.screen_name
                    id = tweets.id
                    text = tweets.full_text

                    if (nawab_check_tweet(id)) and ('RT @' in tweets.text):
                        with open("nawab_errors.log", "a") as fp:
                            fp.write(str(id) + " already exists in the database or it is a retweet\n")
                    else:
                        if (isUserwhitelisted(user) or (isUserBanned(user) and isSafeKeyword(text))):
                            nawab_store_id(id)
                            url = 'https://twitter.com/' + user +  '/status/' + str(id)
                            with open("nawab_results.log", "a") as fp:
                                fp.write(url)

                with open("nawab_results.log", "a") as fp:
                    fp.write("Id: " + str(id) + " is stored to the db from this iteration \n")

            except tweepy.TweepError as e:
                with open("nawab_errors.log", "a") as fp:
                    fp.write("Tweepy failed at " + str(id) + " because of " + e.reason + "\n")
                pass

def nawab_retweet_tweet(api):
    with open("tid_store.txt", "r") as fp:
        for line in fp:
            tweet_id = int(line)
            try:
                u = api.get_status(id=tweet_id)
                rt_username = u.author.screen_name
                ##api.retweet(tweet_id)
                time.sleep(60)
                
                retweet_url = 'https://twitter.com/' + rt_username +  '/status/' + str(tweet_id)
                
                with open("nawab_results.log", "a") as fp:
                    fp.write("Nawab retweeted " + str(tweet_id) + " successfully \n")
                bot = telegram.Bot(token=tg.token)
                bot.sendMessage(chat_id=tg.chat_id, text=retweet_url)

            except tweepy.TweepError as e:
                with open("nawab_errors.log", "a") as fp:
                    fp.write("Tweepy failed to retweet after reading from the store of id " + str(tweet_id) + " because of " + e.reason + "\n")
                pass

def main():
   api = nawab_twitter_authenticate()
   nawab_get_blacklist()
   nawab_get_bannedwords()
   nawab_get_whitelist()
   nawab_curate_list(api)
   nawab_retweet_tweet(api)

if __name__ == "__main__":
    main()
