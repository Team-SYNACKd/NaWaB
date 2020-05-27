#!/usr/bin/env python3

import json
import config
import tweepy
import mmap
import time
import random
from datetime import date, datetime
import csv
import os
import logging
import nawab_logger
import pandas as pd


class Twitter_Bot(object):
    def __init__(self, dirpath, data, level):
        self.dirpath = dirpath
        self.data = data
        self.level = level
        self.nw_logger = nawab_logger.Nawab_Logging(dirpath, self.level)
        if not os.path.isfile(self.dirpath + 'tid_store.csv'):
            with open(self.dirpath + 'tid_store.csv', 'w') as f:
                Headers = ['Date_time', 'Id']
                writer = csv.writer(f)
                writer.writerow(Headers)
        if not os.path.isfile(self.dirpath + 'backup_tid_store.csv'):
            with open(self.dirpath + 'backup_tid_store.csv', 'w') as f:
                Headers = ['Date_time', 'Id']
                writer = csv.writer(f)
                writer.writerow(Headers)

    def nawab_twitter_authenticate(self):
        auth = tweepy.OAuthHandler(
            config.tw_consumer_key, config.tw_consumer_secret)
        auth.set_access_token(config.tw_access_token_key,
                              config.tw_access_token_secret)
        api = tweepy.API(auth)
        return api

    def nawab_read_list(self):
        search_list = []
        for index, row in self.data.iterrows():
            search_list.append(row["Proto_list"])
        return (search_list)

    def nawab_store_id(self, tweet_id, isrelevant):
        ### Store a tweet id in a file
        if isrelevant:
            dicts = {'Date_time': [datetime.now()],
                     'Id': [str(tweet_id)]}
            data = pd.DataFrame(dicts)
            data.to_csv(self.dirpath + 'tid_store.csv',
                        mode='a', header=False, index=False)
        else:
            dicts = {'Date_time': [datetime.now()],
                     'Id': [str(tweet_id)]}
            data = pd.DataFrame(dicts)
            data.to_csv(self.dirpath + 'backup_tid_store.csv',
                        mode='a', header=False, index=False)

    def isUserwhitelisted(self, userName):
        ### Search if the Whitelist user is in file
        if any(str(acc["Whitelist"]).lower() == userName.lower() for index, acc in self.data.iterrows()):
            return True
        return False

    def isUserBanned(self, userName, admin_user):
        ### Search if the Blacklisted user is in file,and blacklist the bot's account
        if not any((str(acc["Blacklist"]).lower() == userName.lower()) or (admin_user.lower() == userName.lower()) for index, acc in self.data.iterrows()):
            return True
        return False

    """Get banned words for a safer content tweets by nawab"""

    def isSafeKeyword(self, tweetText):
        ### Search if tweettext is safe
        if not any(str(word["Banwords"]).lower() in tweetText.lower() for index, word in self.data.iterrows()):
            return True
        return False

    def nawab_get_id(self):
        ### Read the  retweeted id from tid_store
        tid_store = pd.read_csv(self.dirpath + 'tid_store.csv')
        return tid_store['Id']  

    def nawab_find_prev_date(self):
        """to find the previous date in the tid"""
        tid = pd.read_csv(self.dirpath + 'tid_store.csv')
        tid["Date_time"]= pd.to_datetime(tid["Date_time"])
        previous_date = tid['Date_time'].iloc[-1]
        #find the previous date by iterating tid_store bottom-up 
        for index, tid_store in tid[::-1].iterrows():
            scrape_datetime = tid_store['Date_time']
            scrape_date = date(scrape_datetime.year, scrape_datetime.month, scrape_datetime.day)
            if scrape_date!=previous_date:
                previous_date = scrape_date
                break
        return previous_date

    def nawab_check_relevant(self, query, text):
        """Check for count of keywords in text"""
        cnt = 0
        for line in query:
            key = str(line).strip('#')
            if key in text:
                cnt += text.count(key)
        return cnt

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
                        fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + ',' +  ' INFO ' +'Twitter_Bot ' +
                                 "starting new query search: " + line + "\n")
                        
                self.nw_logger.logger('Twitter_Bot' +
                    ' starting new query search: ' + line, 'info', 'Results')

                try:
                    for tweets in tweepy.Cursor(api.search, q=line, tweet_mode="extended",
                                                lang='en', since=latest_date).items(tweet_limit):
                        user = tweets.user.screen_name
                        id = tweets.id
                        text = tweets.full_text
                        ## obtain user account for blacklist
                        admin = api.me()
                        admin_user = admin.screen_name
                        ## minimum no of keywords required
                        min_freq = 2

                        if (self.nawab_check_tweet(id)) and ('RT @' in text):
                            if self.level == logging.WARNING:
                                with open(self.dirpath + "error.log", "a") as fp:
                                    fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") +',' +  ' ERROR ' + 'Twitter_Bot ' +
                                        str(id)  + " already exists in the database or it is a retweet\n")
                            self.nw_logger.logger('Twitter_Bot ' +
                                  str(id) + ' already exists in the database or it is a retweet', 'error', 'Error')
                        else:
                            if (self.isUserwhitelisted(user) or (self.isUserBanned(user, admin_user) and self.isSafeKeyword(text))):
                                if not (self.nawab_check_tweet(id)):
                                    ##check if it is a relevant tweet
                                    if self.nawab_check_relevant(query, text) >= min_freq:
                                        if self.level == logging.CRITICAL or self.level == logging.WARNING:
                                            with open(self.dirpath + "results.log", "a") as fp:
                                                fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + "," + ' INFO ' + 'Twitter_Bot ' + "Id: " + str(id) +
                                                         " is a relevant tweet and is stored to the db from this iteration \n")

                                        self.nw_logger.logger('Twitter_Bot ' +
                                                              'Id: ' + str(id) + 'is a relevant tweet and is  stored to the db from this iteration', 'info', 'Results')
                                        self.nawab_store_id(id, True)
                                    else:
                                        if self.level == logging.CRITICAL or self.level == logging.WARNING:
                                            with open(self.dirpath + "results.log", "a") as fp:
                                                fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + "," + ' INFO ' + 'Twitter_Bot ' + "Id: " + str(id) +
                                                         " is not a relevant tweet and is stored to the db from this iteration \n")
                                        self.nw_logger.logger('Twitter_Bot ' +
                                                              'Id: ' + str(id) + 'is not a relevant tweet and will not be  from this iteration', 'info', 'Results')
                                        self.nawab_store_id(id, False)
                                url = 'https://twitter.com/' + \
                                    user + '/status/' + str(id)

                                if self.level == logging.CRITICAL or self.level == logging.WARNING:
                                    with open(self.dirpath + "results.log", "a") as fp:
                                        fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + ',' + ' INFO '
                                                  +'Twitter_Bot ' + url + '\n')   
                                self.nw_logger.logger('Twitter_Bot ' + url, 'info', 'Results')

                except tweepy.TweepError as e:
                    if self.level == logging.CRITICAL:
                        fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + ',' +  ' ERROR ' + 'Twitter_Bot '
                                     +"Tweepy failed at " + str(id) + " because of " + e.reason + "\n")
                    self.nw_logger.logger('Twitter_Bot' +
                        ' Tweepy failed at ' + str(id) + ' because of ' + e.reason, 'error', 'Error')
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
                            fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + ',' +  ' INFO ' + 'Twitter_Bot ' +
                                     "Nawab retweeted " + str(tweet_id) + " successfully \n")

                self.nw_logger.logger('Twitter_Bot' +' Nawab retweeted ' +
                                        str(tweet_id) + ' successfully', 'info', 'Results')

            except tweepy.TweepError as e:
                if self.level == logging.CRITICAL:
                        with open(self.dirpath + "error.log", "a") as fp:
                            fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") +',' +  ' ERROR ' + 'Twitter_Bot ' +
                                     "Tweepy failed to retweet after reading from the store of id " +
                                    str(tweet_id)  +" because of " + e.reason + "\n")
                self.nw_logger.logger('Twitter_Bot' + ' Tweepy failed to retweet after reading from the store of id ' +
                                        str(tweet_id) + ' because of ' + e.reason, 'error', 'Error')
                pass
