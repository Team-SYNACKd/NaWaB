#!/usr/bin/env python2

import json
import config
import tweepy

from time import sleep

def nawab_twitter_authenticate():
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token_key, config.access_token_secret)
    api = tweepy.API(auth)
    return api

def nawab_read_list():
    proto_list = open('protobuf_list.txt', 'r')
    search_term = proto_list.readlines()
    return search_term

def nawab_twitter_retweet(api):  
   query = nawab_read_list()

   if len(query) > 0:
       for line in query:
           print("starting new query:\t" + line)
           for tweet in tweepy.Cursor(api.search, q=line,
                   tweet_mode="extended").items(2):
               user = tweet.user.screen_name
               id = tweet.id
               url = 'https://twitter.com/' + user +  '/status/' + str(id)
               print(url)
               
               if not tweet.retweeted:
                   tweet = api.user_timeline(id, count = 1)[0]
                   print(tweet.text)

                       #tweet.retweet()
                       #print("\t Retweeted")
                       # sleep(120)
                   #except tweepy.TweepError as e:
                       #print("\t Nawab Error: Retweet was not successful," + e.reason)

def main():
   api = nawab_twitter_authenticate()
   nawab_twitter_retweet(api)

if __name__ == "__main__":
    main()
