#!/usr/bin/env python3

import logging
import telegram
import config
import tweepy
import time
import nawab_logger

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler


class Telegram_Bot(object):

    def __init__(self, twitter_api, dirpath):
        self.dirpath = dirpath
        self.twitter_api = twitter_api
        self.nw_logger = nawab_logger.Nawab_Logging(dirpath)

    def nawab_tg_authenticate(self):
        updater = Updater(token=config.tg_token, use_context=True)
        return updater

    def help(self, update, context):
        text = 'Hello, this is a bot which scrapes the tweets related to networks and gives you ' \
                'an option to retweet the tweet as well. Type the command /start to start and ' \
                '/stop to stop.'
        update.message.reply_text(text = text)

    def start(self, update, context):
        with open(self.dirpath + "tid_store.txt", "r") as fp:
            for line in fp:
                try:
                    u = self.twitter_api.get_status(id=line)
                    username = u.author.screen_name
                except tweepy.TweepError as e:
                    self.nw_logger.logger('\t|Tweepy failed to get the status of the user from the ' +
                                          str(line) + ' because of ' + e.reason + '\n\n', 'error', 'Error')
                    pass
                url = 'https://twitter.com/' + \
                    username + '/status/' + str(line)
                keyboard = [[InlineKeyboardButton(
                    "Retweet", callback_data=int(line))]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(text=url, reply_markup=reply_markup)
                #time.sleep(10)

    def stop(self, update, context):
        update.message.reply_text("Okay, Bye")
        return ConversationHandler.END

    def button(self, update, context):
        query = update.callback_query
        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        query.answer()
        data = query.data
        try:
            self.twitter_api.retweet(data)
        except tweepy.TweepError as e:
            self.nw_logger.logger('\t|Tweepy failed to retweet after reading from the store of id ' +
                                  str(data) + ' because of ' + e.reason + '\n\n', 'error', 'Error')
            pass
        query.edit_message_text(text="Retweeted: {}".format(query.data))

    def error(self, update, context):
        """Log Errors caused by Updates."""
        self.nw_logger.logger(
            '\t|Update' + update + 'caused error ' + context.error + '\n\n', 'error', 'Error')
