import os
import json
import telebot
from telebot import types
from flask import Flask
import threading
import firebase_admin
from firebase_admin import credentials, db

# 🔐 Load Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# 🔥 Firebase Setup
cred_data = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_data)
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv("FIREBASE_DB_URL")
})

bot = telebot.TeleBot(BOT_TOKEN)

# 📌 Custom Buttons
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "🎯 টাস্ক করুন", "📷 স্ক্রিনশট সাবমিট", "💰 ব্যালেন্স", "👫 রেফার করুন",
        "ℹ️ নিয়মাবলী", "📤 উইথড্র করুন", "🧑‍💼 অ্যাডমিন", "📈 আমার রিপোর্ট", "📞 যোগাযোগ"
    ]
    markup.add(*buttons)
    return markup

# 🟢 Start Command
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = str(msg.chat.id)
    ref_id = str(msg.text.split()[1]) if len(msg.text.split()) > 1 else None
    user_ref = db.reference(f'users/{user_id}')

    if not user_ref.get():
        user_ref.set({
            'balance': 0,
            'referrals': 0,
            'screenshots': [],
            'submitted': False
        })
        if ref_id and ref_id != user_id:
            ref_ref = db.reference(f'users/{ref_id}')
            if ref_ref.get():
                ref_ref.child('referrals').set(ref_ref.child('referrals').get() + 1)
                ref_bonus = 10
                ref_ref.child('balance').set(ref_ref.child('balance').get() + ref_bonus)
                bot.send_message(int(ref_id), f'🎉 একজন নতুন রেফারেল জয়েন করেছে! আপনি {ref_bonus} টাকা পেয়েছেন।')

    bot.send_message(msg.chat.id, "🎉 স্বাগতম! আপনার মেনু থেকে অপশন বেছে নিন।", reply_markup=main_menu())

# 🎯 Task Show
@bot.message_handler(func=lambda msg: msg.text == "🎯 টাস্ক করুন")
def task(msg):
    task_text = "📢 নিচের টাস্কগুলো সম্পন্ন করুন:\n\n"
    tasks = {
        "1": "✅ Visit and signup: https://example.com/task1",
        "2": "✅ Complete profile: https://example.com/task2",
        "3": "✅ Download App: https://example.com/task3",
        "4": "✅ Watch 1 video: https://example.com/task4"
    }
    for k, v in tasks.items():
        task_text += f"{k}. {v}\n\n"
    bot.send_message(msg.chat.id, task_text)

# 📷 Screenshot Submission
@bot.message_handler(content_types=['photo'])
def handle_photo(msg):
    user_id = str(msg.chat.id)
    screenshot_ref = db.reference(f'users/{user_id}/screenshots')
    existing = screenshot_ref.get() or []
    if len(existing) >= 3:
        bot.send_message(msg.chat.id, "✅ আপনি ইতোমধ্যে ৩টি স্ক্রিনশট জমা দিয়েছেন। দয়া করে অপেক্ষা করুন।")
        return

    existing.append(msg.photo[-1].file_id)
    screenshot_ref.set(existing)

    bot.send_message(msg.chat.id, f"📸 স্ক্রিনশট {len(existing)} জমা হয়েছে।")
    bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)

    if len(existing) == 3:
        bot.send_message(msg.chat.id, "✅ আপনি ৩টি স্ক্রিনশট সফলভাবে জমা দিয়েছেন। দয়া করে অনুমোদনের জন্য অপেক্ষা করুন।")

# 💰 Balance & Referral
@bot.message_handler(func=lambda msg: msg.text == "💰 ব্যালেন্স")
def balance(msg):
    user_id = str(msg.chat.id)
    data = db.reference(f'users/{user_id}').get()
    bal = data.get('balance', 0)
    refs = data.get('referrals', 0)
    bot.send_message(msg.chat.id, f"💰 ব্যালেন্স: {bal} টাকা\n👥 রেফার: {refs} জন")

# 👥 Referral
@bot.message_handler(func=lambda msg: msg.text == "👫 রেফার করুন")
def refer(msg):
    link = f"https://t.me/myoffer363bot?start={msg.chat.id}"
    bot.send_message(msg.chat.id, f"📢 এই লিংকে বন্ধুদের ইনভাইট করুন:\n{link}")

# 🧑‍💼 Admin Panel
@bot.message_handler(func=lambda msg: msg.text == "🧑‍💼 অ্যাডমিন" and msg.chat.id == ADMIN_ID)
def admin(msg):
    all_users = db.reference('users').get() or {}
    msg_text = f"📊 মোট ইউজার: {len(all_users)} জন\n"
    bot.send_message(msg.chat.id, msg_text)

# 📤 Withdraw
@bot.message_handler(func=lambda msg: msg.text == "📤 উইথড্র করুন")
def withdraw(msg):
    bot.send_message(msg.chat.id, "💳 উইথড্র করতে চাইলে আপনার ব্যালেন্স কমপক্ষে ১০০০ টাকা হতে হবে।\n\nBkash, Nagad বা Rocket নাম্বার পাঠান:")

# ℹ️ Rules
@bot.message_handler(func=lambda msg: msg.text == "ℹ️ নিয়মাবলী")
def rules(msg):
    bot.send_message(msg.chat.id, "📌 নিয়মাবলী:\n\n১. সব টাস্ক সত্যভাবে করতে হবে।\n২. ভুয়া স্ক্রিনশট দিলে অ্যাকাউন্ট ব্লক হবে।")

# 📞 Contact
@bot.message_handler(func=lambda msg: msg.text == "📞 যোগাযোগ")
def contact(msg):
    bot.send_message(msg.chat.id, "✉️ যোগাযোগ করুন: @yourusername")

# 📈 Report
@bot.message_handler(func=lambda msg: msg.text == "📈 আমার রিপোর্ট")
def report(msg):
    user_id = str(msg.chat.id)
    data = db.reference(f'users/{user_id}').get()
    if not data:
        bot.send_message(msg.chat.id, "🔍 কোনো তথ্য পাওয়া যায়নি।")
        return
    screenshots = data.get('screenshots', [])
    refs = data.get('referrals', 0)
    bal = data.get('balance', 0)
    bot.send_message(msg.chat.id, f"📝 রিপোর্ট:\nস্ক্রিনশট জমা: {len(screenshots)} টি\nরেফার: {refs} জন\nব্যালেন্স: {bal} টাকা")

# 🌐 Fake HTTP Server for Render Web Service
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is alive and running."

def run_http():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# 🔁 Run Web Server & Start Bot
threading.Thread(target=run_http).start()
print("✅ Bot is running...")
bot.infinity_polling()
