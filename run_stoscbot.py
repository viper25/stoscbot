import urllib3.util.ssl_ as urllib3_ssl

# Corporate (Zscaler) root CA lacks critical Basic Constraints, which Python 3.13's strict X.509 check rejects.
urllib3_ssl.VERIFY_X509_STRICT = 0

from stoscbots.bot import bot

if __name__ == '__main__':
    bot.run()