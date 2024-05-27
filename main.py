import math
import os
import re
import threading
import time
from datetime import datetime, timedelta

import telebot

from dotenv import load_dotenv

load_dotenv()
from modules.database import db

bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
GROUP_ID = int(os.getenv('GROUP_ID'))


def obfuscate_email(email):
    username, domain = email.split('@')
    masked_username = username[0] + '*****' + username[-1]
    masked_email = '@'.join([masked_username, domain.lower()])
    return masked_email  # Return the original email if it doesn't match the pattern


import random
import string


def generate_random_email():
    # Generate random username
    username_length = random.randint(5, 12)
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=username_length))

    # Generate random domain name
    domain_length = random.randint(5, 10)
    domain = ''.join(random.choices(string.ascii_lowercase, k=domain_length))

    # Select a random top-level domain
    top_level_domains = ['com', 'net', 'org', 'edu', 'gov']
    tld = random.choice(top_level_domains)

    # Combine username, domain, and top-level domain
    email = f"{username}@{domain}.{tld}"
    return email


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hi there, I am assist bot from Paibu.\
""")


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: message.chat.id == GROUP_ID)
def echo_message(message):
    print(message)
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.text)
    print(urls)
    checked = all('https://paibu.org' in f'{url}' for url in urls)
    print(checked)
    if not checked:
        bot.delete_message(message.chat.id, message.message_id)


def send_notification():
    while True:
        today = datetime.now()
        yesterday = today - timedelta(hours=1)
        pipeline = [
            {
                "$match": {
                    "type": "withdraw",
                    "status": "COMPLETED",
                    "date_field": {
                        "$gte": yesterday,
                        "$lte": today
                    }
                }
            },
            {
                "$lookup": {
                    "from": "users",  # The collection to join
                    "localField": "userId",  # The field in the 'teams' collection
                    "foreignField": "_id",  # The field in the 'players' collection
                    "as": "user"  # The new field to add to the output
                }
            },
            {"$unwind": "$user"},
            {"$limit": 10}
        ]
        wallet_records = list(db['wallet_records'].aggregate(pipeline))
        reports = f"😍✨Congratulations️🎉\n{yesterday.date()}, {yesterday.hour}:00:00\n{today.date()}, {today.hour}:00:00\n\n👍👍👍👍👍👍👍👍👍👍\n\n🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀\n\n\n"
        for wallet_record in wallet_records:
            print(wallet_record['user']['email'])
            reports += f"🎁{obfuscate_email(wallet_record['user']['email'])} 💲{math.fabs(float(wallet_record['amount']))}\n"
        if len(wallet_records) == 0:
            for _ in range(10):
                random_email = generate_random_email()
                reports += f"🎁{obfuscate_email(random_email)} 💲{random.randint(32, 100)}\n"
            reports += "\n🙌 https://paibu.org 🙌"
            print(reports)
        # bot.send_message(chat_id=GROUP_ID, text=reports)
        time.sleep(3600)


threading.Thread(target=send_notification).start()
bot.infinity_polling()
