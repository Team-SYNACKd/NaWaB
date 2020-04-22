import logging
import telegram
import config
import tweepy
import tg_config as tg
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from functools import partial


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

"""
def nawab_twitter_authenticate():
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token_key, config.access_token_secret)
    api = tweepy.API(auth)
    return api
"""


def start(update, context):
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token_key, config.access_token_secret)
    api = tweepy.API(auth)
    with open("tid_store.txt", "r") as fp:
        for line in fp:
            u = api.get_status(id=line)
            username = u.author.screen_name
            url = 'https://twitter.com/' + username +  '/status/' + str(line)
            keyboard = [[InlineKeyboardButton("Retweet", callback_data=int(line))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text=url, reply_markup = reply_markup)
            #time.sleep(10)

def button(update, context):
    query = update.callback_query
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token_key, config.access_token_secret)
    api = tweepy.API(auth)
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    data = query.data
    api.retweet(data)
    query.edit_message_text(text="Retweeted: {}".format(query.data))


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(token = tg.token, use_context = True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()