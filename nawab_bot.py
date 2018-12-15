#!/usr/bin/env python2

import json
import config
import tweepy

def nawab_twitter_authenticate():
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token_key, config.access_token_secret)
    api = tweepy.API(auth)
    return api

def nawab_twitter_retweet(api):
    tweet = 'Hello, world!!!'
    api.update_status(status=tweet)

def main():
    api = nawab_twitter_authenticate()
    nawab_twitter_retweet(api)

if __name__ == "__main__":
    main()
