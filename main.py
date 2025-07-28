import os
import json
import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db

# 🔐 Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
FIREBASE_DB_URL = os.environ.get("FIREBASE_DB_URL")
FIREBASE_CRED = os.environ.get("FIREBASE_CRED")

# ✅ Firebase Init
cred = credentials.Certificate(json.loads(FIREBASE_CRED))
firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_DB_URL
})

bot = telebot.TeleBot(BOT_TOKEN)

# ✅ Example start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🌟 Bot is live and running successfully!")

# ✅ Final required for Render to detect success
print("✅ Bot is running...")
bot.infinity_polling()
