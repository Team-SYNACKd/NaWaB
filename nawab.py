import twitter_bot
import pandas as pd
import pwd
import os


def twitter_bot_run(data, default_dir):
    api = twitter_bot.nawab_twitter_authenticate()
    twitter_bot.nawab_curate_list(api, data, default_dir)
    twitter_bot.nawab_retweet_tweet(api, default_dir)


def main():
    data = pd.read_csv('data.csv')
    default_dir = '/var/log/nawab/'

    u_id = pwd.getpwuid(os.getuid()).pw_name

    if not os.path.exists(default_dir):
        os.system(("sudo mkdir %s" % (default_dir)))

    ownership_command = "sudo chown %s: %s" % (u_id, default_dir)
    os.system(ownership_command)

    twitter_bot_run(data, default_dir)


if __name__ == "__main__":
    main()
