#!/usr/bin/env python3

import json
import config
import tweepy
import mmap
import time
import random
from datetime import date
import csv
import os
import logging
import nawab_logger
import pandas as pd


class Twitter_Bot(object):
    def __init__(self, dirpath, data, level):
        self.dirpath = dirpath
        self.data = data
        self.level= level
        self.nw_logger = nawab_logger.Nawab_Logging(dirpath, self.level)
        if not os.path.isfile(self.dirpath + 'tid_store.csv'):
            with open(self.dirpath + 'tid_store.csv', 'w') as f:
                Headers = ['Date_time', 'Id']
                writer = csv.writer(f)
                writer.writerow(Headers)

    def nawab_twitter_authenticate(self):
        auth = tweepy.OAuthHandler(config.tw_consumer_key, config.tw_consumer_secret)
        auth.set_access_token(config.tw_access_token_key,
                              config.tw_access_token_secret)
        api = tweepy.API(auth)
        return api

    def nawab_read_list(self):
        search_list = []
        for index, row in self.data.iterrows():
            search_list.append(row["Proto_list"])
        return (search_list)

    def nawab_store_id(self, tweet_id):
        ### Store a tweet id in a file
        dicts = { 'Date_time' : [time.strftime("%m/%d/%Y %I:%M:%S %p ")],
                'Id': [str(tweet_id)]}
        data = pd.DataFrame(dicts)
        data.to_csv(self.dirpath + 'tid_store.csv',mode='a',header=False,index=False)

    def isUserwhitelisted(self, userName):
        ### Search if the Whitelist user is in file
        if  any(str(acc["Whitelist"]).lower() == userName.lower() for index, acc in self.data.iterrows()):
            return True
        return False

    def isUserBanned(self, userName, admin_user):
        ### Search if the Blacklisted user is in file,and blacklist the bot's account
        if not any((str(acc["Blacklist"]).lower() == userName.lower()) or (admin_user.lower()==userName.lower()) for index, acc in self.data.iterrows()):
            return True
        return False

    """Get banned words for a safer content tweets by nawab"""

    def isSafeKeyword(self, tweetText):
        ### Search if tweettext is safe
        if not any(str(word["Banwords"]).lower() in tweetText.lower() for index, word in self.data.iterrows()):
            return True
        return False

    def nawab_get_id(self):
        ### Read the last retweeted id from a file
        tid = pd.read_csv(self.dirpath + 'tid_store.csv')
        last = tid['Id'].iloc[-1]
        return last

    def nawab_check_tweet(self, tweet_id):
        tid = pd.read_csv(self.dirpath + 'tid_store.csv')
        if any(tid_store["Id"] == tweet_id for index, tid_store in tid.iterrows()):
            return True
        else:
            return False
    
    def nawab_curate_list(self, api):
        query = self.nawab_read_list()
        self.nawab_search(api, query)

    def nawab_search(self, api, query):
        tweet_limit = 1
        latest_date = date.today()

        if len(query) > 0:
            for line in query:
                if self.level == logging.CRITICAL or self.level == logging.WARNING:
                    with open(self.dirpath + "results.log", "a") as fp:
                        fp.write('INFO:' + time.strftime("%m/%d/%Y %I:%M:%S %p ") + 
                                 "\t|starting new query search: \t" + line + "\n")
                        
                self.nw_logger.logger(
                    '\t|starting new query search: \t' + line, 'info', 'Results')

                try:
                    for tweets in tweepy.Cursor(api.search, q=line, tweet_mode="extended",
                                                lang='en', since=latest_date).items(tweet_limit):
                        user = tweets.user.screen_name
                        id = tweets.id
                        text = tweets.full_text
                        ## obtain user account for blacklist
                        admin = api.me()
                        admin_user = admin.screen_name

                        if (self.nawab_check_tweet(id)) and ('RT @' in text):
                            if self.level == logging.WARNING:
                                with open(self.dirpath + "error.log", "a") as fp:
                                    fp.write('ERROR:' + time.strftime("%m/%d/%Y %I:%M:%S %p ") + '\t|'+
                                        str(id) + ' ' + " already exists in the database or it is a retweet\n")
                            self.nw_logger.logger(
                                '\t|' + str(id) + 'already exists in the database or it is a retweet', 'error', 'Error')
                        else:
                            if (self.isUserwhitelisted(user) or (self.isUserBanned(user,admin_user) and self.isSafeKeyword(text))):
                                if not (self.nawab_check_tweet(id)):
                                    self.nawab_store_id(id)
                                url = 'https://twitter.com/' + \
                                    user + '/status/' + str(id)
                                    
                                if self.level == logging.CRITICAL or self.level == logging.WARNING:
                                    with open(self.dirpath + "results.log", "a") as fp:
                                        fp.write('INFO:' + time.strftime("%m/%d/%Y %I:%M:%S %p ") + '\t|' + url + '\n')
                                        
                                self.nw_logger.logger(
                                    '\t|' + url + '\n', 'info', 'Results')
                                
                    if self.level == logging.CRITICAL or self.level == logging.WARNING:
                         with open(self.dirpath + "results.log", "a") as fp:
                            fp.write('INFO:' + time.strftime("%m/%d/%Y %I:%M:%S %p ") + "\t|Id: " + str(id) +
                                 " is stored to the db from this iteration \n")
                        
                    self.nw_logger.logger(
                        '\t|Id: ' + str(id) + 'is stored to the db from this iteration', 'info', 'Results')

                except tweepy.TweepError as e:
                    if self.level == logging.CRITICAL:
                        with open(self.dirpath + "error.log", "a") as fp:
                            fp.write('ERROR:' + time.strftime("%m/%d/%Y %I:%M:%S %p ") + "\t|Tweepy failed at " + str(id) +
                                ' ' +  " because of " + e.reason + "\n")
                    self.nw_logger.logger(
                        '\t|Tweepy failed at ' + str(id) + 'because of' + e.reason, 'error', 'Error')
                    pass

    def nawab_retweet_tweet(self, api):
        tid = pd.read_csv(self.dirpath + 'tid_store.csv')
        for index, tid_store in tid.iterrows():
            tweet_id = int(tid_store['Id'])
            try:
                u = api.get_status(id=tweet_id)
                rt_username = u.author.screen_name
                api.retweet(tweet_id)
                time.sleep(60)
                retweet_url = 'https://twitter.com/' + \
                    rt_username + '/status/' + str(tweet_id)
                if self.level == logging.CRITICAL or self.level == logging.WARNING:
                        with open(self.dirpath + "results.log", "a") as fp:
                            fp.write('INFO:' + time.strftime("%m/%d/%Y %I:%M:%S %p ") + "\t|Nawab retweeted " +
                                 str(tweet_id) + " successfully \n")
                            
                self.nw_logger.logger('\t|Nawab retweeted' +
                                        str(tweet_id) + 'successfully', 'info', 'Results')

            except tweepy.TweepError as e:
                if self.level == logging.CRITICAL:
                        with open(self.dirpath + "error.log", "a") as fp:
                            fp.write('ERROR:' + time.strftime("%m/%d/%Y %I:%M:%S %p ") + "\t|Tweepy failed to retweet after reading from the store of id " +
                                    str(tweet_id) +  ' ' +" because of " + e.reason + "\n")

                self.nw_logger.logger('\t|Tweepy failed to retweet after reading from the store of id ' +
                                        str(tweet_id) + ' ' + 'because of' + e.reason, 'error', 'Error')
                pass
