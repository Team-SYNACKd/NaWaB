import twitter_bot
import tg_bot
import pandas as pd
import pwd
import os
import threading

#TODO: Shouldn't import this here. Need a way to derive this from tg_bot instead.
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler


class Nawab(object):

    def __init__(self, dirpath, data):
        self.dirpath = dirpath
        self.data = data

    def retrieve_twitter_auth(self):
        tw_bot = twitter_bot.Twitter_Bot(self.dirpath, self.data)
        api = tw_bot.nawab_twitter_authenticate()
        return tw_bot, api


    def twitter_bot_run(self):
        tw_bot, api = self.retrieve_twitter_auth()
        tw_bot.nawab_curate_list(api)
        tw_bot.nawab_retweet_tweet(api)


    def tg_bot_run(self):
        tw_bot, api = self.retrieve_twitter_auth()
        bot = tg_bot.Telegram_Bot(api, self.dirpath)
        updater = bot.nawab_tg_authenticate()

        dp = updater.dispatcher
        dp.add_handler(CommandHandler('start', bot.start))
        dp.add_handler(CommandHandler("stop", bot.stop, pass_chat_data=True))
        dp.add_handler(CommandHandler('help',bot.help))
        dp.add_handler(CallbackQueryHandler(bot.button))
        dp.add_error_handler(bot.error)

        # Start the Bot
        updater.start_polling()

        # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT
        updater.idle()


def wrapper(func, args, res):
    res.append(func(*args))


def main():
    res = []
    data = pd.read_csv('data.csv')
    default_dir = '/var/log/nawab/'

    u_id = pwd.getpwuid(os.getuid()).pw_name

    if not os.path.exists(default_dir):
        os.system(("sudo mkdir %s" % (default_dir)))

    ownership_command = "sudo chown %s: %s" % (u_id, default_dir)
    os.system(ownership_command)

    nawab = Nawab(default_dir,data)
    #Initiate twitter bot
    thread = threading.Thread(target=wrapper, args=(
        nawab.twitter_bot_run, (), res))
    thread.start()
    while thread.is_alive:
        #Initiate telegram bot
        nawab.tg_bot_run()


if __name__ == "__main__":
    main()
