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


class Twitter_Bot(object):
    def __init__(self, dirpath, data):
        self.dirpath = dirpath
        self.data = data

    def nawab_twitter_authenticate(self):
        auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
        auth.set_access_token(config.access_token_key,
                              config.access_token_secret)
        api = tweepy.API(auth)
        return api

    def nawab_read_list(self):
        search_list = []
        for index, row in self.data.iterrows():
            search_list.append(row["Proto_list"])
        return (search_list)

    def nawab_store_id(self, tweet_id):
        ### Store a tweet id in a file
        with open(self.dirpath + "tid_store.txt", "a") as fp:
            fp.write(str(tweet_id) + str('\n'))

    def isUserwhitelisted(self, userName):
        ### Search if the Whitelist user is in file
        if not any(acc["Whitelist"] == userName.lower() for index, acc in self.data.iterrows()):
            return True
        return False

    def isUserBanned(self, userName):
        ### Search if the Blacklisted user is in file
        if not any(acc["Blacklist"] == userName.lower() for index, acc in self.data.iterrows()):
            return True
        return False

    """Get banned words for a safer content tweets by nawab"""

    def isSafeKeyword(self, tweetText):
        ### Search if tweettext is safe
        if not any(word["Banwords"] == tweetText.lower() for index, word in self.data.iterrows()):
            return True
        return False

    def nawab_get_id(self):
        ### Read the last retweeted id from a file
        with open(self.dirpath + "tid_store.txt", "r") as fp:
            for line in fp:
                return line

    def nawab_check_tweet(self, tweet_id):
        with open(self.dirpath + "tid_store.txt", "r") as fp:
             if any(line.strip() == tweet_id for line in fp):
                 return True
             else:
                 return False

    def nawab_curate_list(self, api):
        query = self.nawab_read_list()
        self.nawab_search(api, query)

    def nawab_search(self, api, query):
        tweet_limit = 1
        latest_date = date.today()

        try:
            last_id = self.nawab_get_id()
        except FileNotFoundError as e:
            fp = open(self.dirpath + "error.log", "a")
            fp.write(
                "No tweet id found, hence assuming no file created and therefore creating the new file \n")
            f = open(self.dirpath + "tid_store.txt", "w+")
            last_id = None

        if len(query) > 0:
            for line in query:

                with open(self.dirpath + "results.log", "a") as fp:
                    fp.write("starting new query search: \t" + line + "\n")

                try:
                    for tweets in tweepy.Cursor(api.search, q=line, tweet_mode="extended",
                                                lang='en', since=latest_date).items(tweet_limit):
                        user = tweets.user.screen_name
                        id = tweets.id
                        text = tweets.full_text

                        if (self.nawab_check_tweet(id)) and ('RT @' in tweets.text):
                            with open(self.dirpath + "error.log", "a") as fp:
                                fp.write(
                                    str(id) + " already exists in the database or it is a retweet\n")
                        else:
                            if (self.isUserwhitelisted(user) or (self.isUserBanned(user) and self.isSafeKeyword(text))):
                                self.nawab_store_id(id)
                                url = 'https://twitter.com/' + \
                                    user + '/status/' + str(id)
                                with open(self.dirpath + "results.log", "a") as fp:
                                    fp.write(url)

                    with open(self.dirpath + "results.log", "a") as fp:
                        fp.write("Id: " + str(id) +
                                 " is stored to the db from this iteration \n")

                except tweepy.TweepError as e:
                    with open(self.dirpath + "error.log", "a") as fp:
                        fp.write("Tweepy failed at " + str(id) +
                                 " because of " + e.reason + "\n")
                    pass

    def nawab_retweet_tweet(self, api):
        with open(self.dirpath + "tid_store.txt", "r") as fp:
            for line in fp:
                tweet_id = int(line)
                try:
                    u = api.get_status(id=tweet_id)
                    rt_username = u.author.screen_name
                    api.retweet(tweet_id)
                    time.sleep(60)
                    retweet_url = 'https://twitter.com/' + \
                        rt_username + '/status/' + str(tweet_id)

                    with open(self.dirpath + "results.log", "a") as fp:
                        fp.write("Nawab retweeted " +
                                 str(tweet_id) + " successfully \n")

                except tweepy.TweepError as e:
                    with open(self.dirpath + "error.log", "a") as fp:
                        fp.write("Tweepy failed to retweet after reading from the store of id " +
                                 str(tweet_id) + " because of " + e.reason + "\n")
                    pass
