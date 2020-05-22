#!/usr/bin/env python3

import logging
import telegram
import config
import tweepy
import time
import nawab_logger
import pandas as pd
import inspect
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
        if self.level == logging.CRITICAL or self.level == logging.WARNING:
             with open(self.dirpath + "results.log", "a") as fp:
                 fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + ',' +  ' INFO ' + 'Telegram_Bot '
                           + 'starting display parameter' + '\n')
        self.nw_logger.logger('Telegram_Bot starting display parameter', 'info', 'Results')
        job = context.job
        global KILL_SIGNAL
        # the previous date from which the tweets need to be sent
        previous_date = self.tw_bot.nawab_find_prev_date()
        tid = pd.read_csv(self.dirpath +  'tid_store.csv')
        for index, tid_store in tid[::-1].iterrows():
            scrape_date = tid_store['Date_time']
            if scrape_date<previous_date:
                break
            try:
                u = self.twitter_api.get_status(id=tid_store['Id'])
                username = u.author.screen_name
            except tweepy.TweepError as e:
                if self.level == logging.CRITICAL:
                        with open(self.dirpath + "error.log", "a") as fp:
                            fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + ',' +  ' ERROR ' + 'Telegram_Bot ' +
                                      "Tweepy failed to get the status of the user from the " +
                                 str(tid_store['Id']) +  ' because of ' + e.reason + "\n")
                self.nw_logger.logger('Telegram_Bot Tweepy failed to get the status of the user from the ' +
                                        str(tid_store['Id'])  + ' because of ' + e.reason, 'error', 'Error')
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
                #time.sleep(10)
            else:
                KILL_SIGNAL = 0
                break

    def start(self, update, context):
        if self.level == logging.CRITICAL or self.level == logging.WARNING:
             with open(self.dirpath + "results.log", "a") as fp:
                 fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + ',' +  ' INFO ' + 'Telegram_Bot '
                            + 'starting bot' + '\n')
        self.nw_logger.logger('Telegram_Bot starting bot', 'info', 'Results')
        chat_id = int(update.message.chat_id)
        try:
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()
            new_job = context.job_queue.run_once(
                self.display_tweet, 2, context=chat_id)
            if self.level == logging.CRITICAL or self.level == logging.WARNING:
             with open(self.dirpath + "results.log", "a") as fp:
                 fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + ',' + ' INFO ' + 'Telegram_Bot ' 
                           +'new job ' +  new_job + '\n')
            self.nw_logger.logger('Telegram_Bot  new job ' +  new_job , 'info', 'Results')
            context.chat_data['job'] = new_job
            update.message.reply_text('successfully started!')
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

            if self.level == logging.CRITICAL:
                with open(self.dirpath + "error.log", "a") as fp:
                    fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + ',' +  ' ERROR ' + 'Telegram_Bot '  
                             + "Tweepy failed to retweet after reading from the store of id " +
                         str(data) +  ' because of ' + e.reason + "\n")
                
            self.nw_logger.logger('Telegram_Bot' + ' Tweepy failed to retweet after reading from the store of id ' +
                                str(data)  + ' because of ' + e.reason, 'error', 'Error')
            pass
        try:
            u = self.twitter_api.get_status(id=int(data))
            username = u.author.screen_name
        except tweepy.TweepError as e:
            if self.level == logging.CRITICAL:
                with open(self.dirpath + "error.log", "a") as fp:
                    fp.write(time.strftime("%Y-%m-%d %I:%M:%S %p") + ',' + ' ERROR ' + 'Telegram_Bot ' +
                              "Tweepy failed to get the status of the user from the " +
                                    str(data) + ' because of ' + e.reason + '\n')
            self.nw_logger.logger('Telegram_Bot' + ' Tweepy failed to get the status of the user from the ' +
                                    str(data)  + ' because of ' + e.reason, 'error', 'Error')
            pass
        url = 'https://twitter.com/' + \
            username + '/status/' + str(data)
        keyboard = [[InlineKeyboardButton(
                    "View", url=url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Retweeted: {}".format(
            url), reply_markup=reply_markup)

    def error(self, update, context):
        """Log Errors caused by Updates."""
        if self.level == logging.CRITICAL:
            with open(self.dirpath + "error.log", "a") as fp:
                fp.write( time.strftime("%Y-%m-%d %I:%M:%S %p") + ',' +  ' ERROR ' + 'Telegram_Bot ' +
                          'Update ' + update + ' caused error ' + context.error + '\n')
        self.nw_logger.logger('Telegram_Bot' +
            ' Update' + update + 'caused error ' + context.error, 'error', 'Error')
    
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
