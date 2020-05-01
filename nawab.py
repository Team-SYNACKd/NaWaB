import twitter_bot
import tg_bot
import pandas as pd
import pwd
import os
import threading
import argparse

#TODO: Shouldn't import this here. Need a way to derive this from tg_bot instead.
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler


class Nawab(object):

    def __init__(self, dirpath, data, level):
        self.dirpath = dirpath
        self.data = data
        self.level = level

    def retrieve_twitter_auth(self):
        tw_bot = twitter_bot.Twitter_Bot(self.dirpath, self.data, self.level)
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
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-d', '--default', action="store_const", const=30)
    parser.add_argument('-V', '--verbose',action="store_const", const=20)
    parser.add_argument('-s', '--silent', action="store_const", const=50)
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit.')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 1.0', help="Show program's version number and exit.")

    args = vars(parser.parse_args())
    ## set manual loglevels
    if args['default']:
        level = args['default']
    elif args['verbose']:
        level = args['verbose']
    elif args['silent']:
        level = args['silent']
    else:
        level = 10
    
    res = []
    data = pd.read_csv('data.csv')
    default_dir = '/var/log/nawab/'
   
    u_id = pwd.getpwuid(os.getuid()).pw_name

    ownership_command = "sudo chown %s: %s" % (u_id, default_dir)
    os.system(ownership_command)

    nawab = Nawab(default_dir,data,level)
    #Initiate twitter bot
    thread = threading.Thread(target=wrapper, args=(
        nawab.twitter_bot_run, (), res))
    thread.start()
    while thread.is_alive:
        #Initiate telegram bot
        nawab.tg_bot_run()


if __name__ == "__main__":
    main()
