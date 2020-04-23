#!/usr/bin/env python2

import json
import config
import tweepy
import mmap
import time
import random
from datetime import date
import pandas as pd
import csv


data = pd.read_csv('data.csv')


def nawab_twitter_authenticate():
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token_key, config.access_token_secret)
    api = tweepy.API(auth)
    return api


def nawab_read_list():
    search_list = []
    for index, row in data.iterrows():
        search_list.append(row["Proto_list"])
    return (search_list)


def nawab_store_id(tweet_id):
    ### Store a tweet id in a file
    with open("tid_store.txt", "a") as fp:
        fp.write(str(tweet_id) + str('\n'))


def isUserwhitelisted(userName):
    ### Search if the Whitelist user is in file
    if not any(acc["Whitelist"] == userName.lower() for index, acc in data.iterrows()):
        return True
    return False


def isUserBanned(userName):
    ### Search if the Blacklisted user is in file
    if not any(acc["Blacklist"] == userName.lower() for index, acc in data.iterrows()):
        return True
    return False


"""Get banned words for a safer content tweets by nawab"""


def isSafeKeyword(tweetText):
    ### Search if tweettext is safe
    if not any(word["Banwords"] == tweetText.lower() for index, word in data.iterrows()):
        return True
    return False


def nawab_get_id():
    ### Read the last retweeted id from a file
    with open("tid_store.txt", "r") as fp:
        for line in fp:
            return line


def nawab_check_tweet(tweet_id):
    with open("tid_store.txt", "r") as fp:
        for line in fp:
            if line == tweet_id:
                return True
            else:
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
        fp.write(
            "No tweet id found, hence assuming no file created and therefore creating the new file \n")
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
                            fp.write(
                                str(id) + " already exists in the database or it is a retweet\n")
                    else:
                        if (isUserwhitelisted(user) or (isUserBanned(user) and isSafeKeyword(text))):
                            nawab_store_id(id)
                            url = 'https://twitter.com/' + \
                                user + '/status/' + str(id)
                            with open("nawab_results.log", "a") as fp:
                                fp.write(url)

                with open("nawab_results.log", "a") as fp:
                    fp.write("Id: " + str(id) +
                             " is stored to the db from this iteration \n")

            except tweepy.TweepError as e:
                with open("nawab_errors.log", "a") as fp:
                    fp.write("Tweepy failed at " + str(id) +
                             " because of " + e.reason + "\n")
                pass


def nawab_retweet_tweet(api):
    with open("tid_store.txt", "r") as fp:
        for line in fp:
            tweet_id = int(line)
            try:
                u = api.get_status(id=tweet_id)
                rt_username = u.author.screen_name
                api.retweet(tweet_id)
                time.sleep(60)
                retweet_url = 'https://twitter.com/' + \
                    rt_username + '/status/' + str(tweet_id)

                with open("nawab_results.log", "a") as fp:
                    fp.write("Nawab retweeted " +
                             str(tweet_id) + " successfully \n")

            except tweepy.TweepError as e:
                with open("nawab_errors.log", "a") as fp:
                    fp.write("Tweepy failed to retweet after reading from the store of id " +
                             str(tweet_id) + " because of " + e.reason + "\n")
                pass


def main():
    api = nawab_twitter_authenticate()
    nawab_curate_list(api)
    nawab_retweet_tweet(api)


if __name__ == "__main__":
    main()
