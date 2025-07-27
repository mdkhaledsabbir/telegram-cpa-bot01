import os
import json
import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db

# 🔐 Bot Token & Admin ID from GitHub Secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ✅ Firebase Admin Init from GitHub Secrets (Properly loaded)
firebase_creds_str = os.getenv("FIREBASE_CREDENTIALS")
firebase_creds = json.loads(firebase_creds_str)

cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://cpabot-a1604-default-rtdb.firebaseio.com/'
})

bot = telebot.TeleBot(BOT_TOKEN)

# ✅ Start Command Handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🟢 বট কাজ করছে! স্বাগতম।")

# ✅ Run the Bot
bot.polling(non_stop=True)
