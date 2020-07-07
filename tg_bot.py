#!/usr/bin/env python3

import logging
import telegram
import config
import tweepy
import time
import nawab_logger
import pandas as pd
import twitter_bot

from datetime import timedelta, datetime, date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler

KILL_SIGNAL = 0


class Telegram_Bot(object):

    def __init__(self, twitter_api, dirpath, data, level, auto_retweet):
        self.dirpath = dirpath
        self.data = data
        self.twitter_api = twitter_api
        self.level = level
        self.nw_logger = nawab_logger.Nawab_Logging(dirpath, level)
        self.auto_retweet = auto_retweet
        self.tw_bot = twitter_bot.Twitter_Bot(self.dirpath, self.data, self.level)

    def nawab_tg_authenticate(self):
        updater = Updater(token=config.tg_token, use_context=True)
        return updater

    def help(self, update, context):
        text = 'The retweet option is only for the bot admins. However normal users can view the tweet.'\
            '\nSee the available commands in the keyboard below.'
        url = 'https://github.com/Aniketh01/NaWaB/'
        keyboard = [[InlineKeyboardButton("Source Code", url=url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text=text, reply_markup=reply_markup)

    def display_tweet(self, context):
        job = context.job
        global KILL_SIGNAL
        self.tw_bot.nawab_log('starting display parameter', 'info', 'Telegram_Bot ')

        # the previous date from which the tweets need to be sent
        previous_date = self.tw_bot.nawab_find_prev_date()
        previous_datetime = datetime(previous_date.year, previous_date.month, previous_date.day)
        tid = pd.read_csv(self.dirpath + 'tid_store.csv')
        tid['Date_time'] = pd.to_datetime(tid['Date_time'])

        for index, tid_store in tid[::-1].iterrows():
            scrape_date = tid_store['Date_time']
            if scrape_date <= previous_datetime:
                break
            try:
                u = self.twitter_api.get_status(id=tid_store['Id'])
                username = u.author.screen_name
            except tweepy.TweepError as e:
                self.tw_bot.nawab_log('Tweepy failed to get the status of the user from the ' +
                                    str(tid_store['Id'])  + ' because of ' + e.reason, 'error', 'Telegram_Bot ')
                pass
            url = 'https://twitter.com/' + \
                username + '/status/' + str(tid_store['Id'])

            if (job.context in config.tg_admin_id) and (self.auto_retweet == False or self.auto_retweet == None):
                keyboard = [[InlineKeyboardButton("Retweet", callback_data=int(
                    tid_store['Id'])), InlineKeyboardButton("View", url=url)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
            else:
                keyboard = [[InlineKeyboardButton(
                    "View", url=url)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
            if KILL_SIGNAL == 0:
                context.bot.send_message(job.context, text=str(
                    url), reply_markup=reply_markup)
                time.sleep(1)
            else:
                KILL_SIGNAL = 0
                break

    def start(self, update, context):
        global KILL_SIGNAL
        KILL_SIGNAL = 0
        chat_id = int(update.message.chat_id)
        try:
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()
            new_job = context.job_queue.run_once(
                self.display_tweet, 2, context=chat_id)
            context.chat_data['job'] = new_job
            update.message.reply_text('Successfully started!')
            self.tw_bot.nawab_log('new job ' +  str(new_job), 'info', 'Telegram_Bot ')
        except (IndexError, ValueError):
            update.message.reply_text('Did you /start yet?')


    def button(self, update, context):
        query = update.callback_query
        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        query.answer()
        data = query.data
        try:
            self.twitter_api.retweet(data)
        except tweepy.TweepError as e:
            self.tw_bot.nawab_log('Tweepy failed to retweet after reading from the store of id ' +
                                str(data)  + ' because of ' + e.reason, 'error', 'Telegram_Bot ')
            pass
        try:
            u = self.twitter_api.get_status(id=int(data))
            username = u.author.screen_name
        except tweepy.TweepError as e:
            self.tw_bot.nawab_log('Tweepy failed to get the status of the user from the ' +
                                str(data)  + ' because of ' + e.reason, 'error', 'Telegram_Bot ')
            pass
        url = 'https://twitter.com/' + \
            username + '/status/' + str(data)
        keyboard = [[InlineKeyboardButton(
                    "View", url=url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Retweeted: {}".format(
            url), reply_markup=reply_markup)

    def error(self, update, context):
        """
        Log Errors caused by Updates.
        """
        self.tw_bot.nawab_log('Update' + update + 'caused error ' + context.error, 'error', 'Telegram_Bot ')
        
    def stop(self, update, context):
        if 'job' not in context.chat_data:
            update.message.reply_text('You have not activated the bot yet!')
            return
        job = context.chat_data['job']
        job.schedule_removal()
        del context.chat_data['job']
        global KILL_SIGNAL
        KILL_SIGNAL = 1

        update.message.reply_text(
            'Nawab Telegram bot has been stopped successfully!')