#!/usr/bin/env python2

import json
import config
import tweepy

def twitter_authenticate(config):
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token_key, config.access_token_secret)
    api = tweepy.API(auth)

tweet = 'Hello, world!!!'
api.update_status(status=tweet)


