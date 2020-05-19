import unittest
import sys
sys.path.append('../')
import twitter_bot
import pandas as pd


class TestTwitter_Bot(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):     ##occour before every test used to handle db and file creation 
        print('setupClass')

    @classmethod
    def tearDownClass(cls): ## occur after every test
        print('teardownClass')

    def setUp(self):       ## create and use (__init__)
        print('setUp')
        self.data = pd.read_csv('../data.csv')
        self.tw1 = twitter_bot.Twitter_Bot('/var/log/nawab/',self.data,20)
        
    def tearDown(self):     ## destroy(destructor of object)
        print('tearDown\n')

    def test_relevant(self):
        
        search_list = ['#netsec', '#DNS', '#DANE', '#DNSSEC', '#QUIC', '#TCP/UDP', '#BGP', '#Routing', '#IP', '#IPv4', '#IPv6'
                       , '#SNI', '#HTTP/0.9', '#HTTP0.9', '#HTTP2', '#HTTP/2', '#HTTP3', '#HTTP/3', '#TLS', '#TCP', '#UDP']
        
        tweet_text1 = "iPhone SE delivery times suggest supply has caught up with demand https://t.co/yXoEdrLx5X TLS News"
        self.assertEqual(self.tw1.nawab_check_relevant(search_list,tweet_text1),1)
        
        tweet_text2 = "Netumo has added Slack integration so now you can get all of your downtime and expiration notifications directly into your #QUIC workspace.Check out https://t.co/mMT7F3lEPZ on information on how to set it up.uptime monitoring #TLS #netumo #downtime #http #https https://t.co/pjywhrX5sD"
        self.assertEqual(self.tw1.nawab_check_relevant(search_list,tweet_text2),2)
        
    def test_check_id(self):
        """Check for the tweet duplicate"""
        self.assertEqual(self.tw1.nawab_check_tweet(int(12352)),False)
        self.assertEqual(self.tw1.nawab_check_tweet(int(1235243242)),False)
        
    def test_isUserBanned(self):
        
        """ Check for Banned user"""
        self.assertEqual(self.tw1.isUserBanned("Ananthan2k","Ananthan2k"),True)
        self.assertEqual(self.tw1.isUserBanned("Pornhub","Ananthan2k"),False)
        
    def test_isSafeword(self):
        
        """ Check for Banned word"""
        tweet_text3 = "iPhone SE delivery times suggest supply has caught up with demand https://t.co/yXoEdrLx5X TLS News"
        tweet_text4 = "iPhone SE delivery times suggest supply has caught up with demand of xvideo"
        self.assertEqual(self.tw1.isSafeKeyword(tweet_text3),True)
        self.assertEqual(self.tw1.isSafeKeyword(tweet_text4),False)