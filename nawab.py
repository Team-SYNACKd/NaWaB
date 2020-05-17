import twitter_bot
import tg_bot
import pandas as pd
import pwd
import os
import sys
import threading
import argparse
import logging

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


    def twitter_bot_run(self, auto_retweet=None):
        tw_bot, api = self.retrieve_twitter_auth()
        tw_bot.nawab_curate_list(api)
        
        if auto_retweet == True:
            tw_bot.nawab_retweet_tweet(api)


    def tg_bot_run(self, auto_retweet=None):
        tw_bot, api = self.retrieve_twitter_auth()
        bot = tg_bot.Telegram_Bot(api, self.dirpath, self.level, auto_retweet)
        updater = bot.nawab_tg_authenticate()

        dp = updater.dispatcher
        dp.add_handler(CommandHandler('start', bot.start))
        dp.add_handler(CommandHandler("stop", bot.stop, pass_chat_data=True))
        dp.add_handler(CommandHandler('help',bot.help))
        dp.add_handler(CallbackQueryHandler(bot.button))
        dp.add_error_handler(bot.error)

        # Start the Bot

        # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT
        try:
            updater.start_polling()
        except KeyboardInterrupt:
            try:
                sys.exit(1)
            except SystemExit:
                os._exit(1)



def wrapper(func, args, res):
    res.append(func(*args))


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-r", "--retweet", help="Retweet all tweets automatically, doesn't spawn a telegram bot",
                        action='store_true', required=False)
    parser.add_argument("-b", "--blacklist",type=list, required=False, help="Blacklist the given username")
    parser.add_argument("-p", "--path", type=str, required=False,
                        help="Path where the log files be stored. Note to create directory in that path beforehand.")
    parser.add_argument('-V', '--verbose',action="store_const", const=20)
    parser.add_argument('-s', '--silent', action="store_const", const=50)
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit.')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 1.0', help="Show program's version number and exit.")
     ## verbose is log level of Info with integer value 20 and silent is log level of critical of 
     ## integer value of 50. The values are provided to futher assign  the level of logging.
     ## Since logging level hold integer values.
    args = vars(parser.parse_args())
    ## set manual loglevels
    if args['verbose']:
        level = args['verbose']
    elif args['silent']:
        level = args['silent']
    else:
        ## Default mode: log level is Warning and above.for further detail visit
        ## https://www.loggly.com/ultimate-guide/python-logging-basics/
        level = logging.WARNING  
    
    res = []
    data = pd.read_csv('data.csv')
    default_dir = '/var/log/nawab/'
    ## blacklisting the names to current data.csv files
    if args['blacklist']:
        blist = pd.DataFrame({'Blacklist': args['blacklist']})
        concats = pd.concat([data,blist])
        concats.to_csv('data.csv', index=False)
        ## if new path is passed then set new default path
    if args['path']:
        default_dir = args['path']
   
    u_id = pwd.getpwuid(os.getuid()).pw_name

    ownership_command = "sudo chown %s: %s" % (u_id, default_dir)
    os.system(ownership_command)

    nawab = Nawab(default_dir,data,level)
    #Initiate twitter bot
    if args['retweet']:
        auto_retweet = args['retweet']
        thread = threading.Thread(target=wrapper, args=(
            nawab.twitter_bot_run, (auto_retweet, ), res))
        thread.start()
    else:
        thread = threading.Thread(target=wrapper, args=(
            nawab.twitter_bot_run, (), res))
        thread.start()
    while thread.is_alive:
        #Initiate telegram bot
        if args['retweet']:
            nawab.tg_bot_run(args['retweet'])
        else:
            nawab.tg_bot_run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)
