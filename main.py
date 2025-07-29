# ✅ Import Statements
import os
import json
import threading

import telebot
from telebot import types

from flask import Flask

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# 🔐 Load Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# 🔥 Firebase Setup
cred_data = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_data)
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv("FIREBASE_DB_URL")
})

# 🤖 Bot Initialization
bot = telebot.TeleBot(BOT_TOKEN)

# 📌 Main Menu Buttons
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "🎯 টাস্ক করুন",
        "📷 স্ক্রিনশট সাবমিট",
        "💰 ব্যালেন্স",
        "👫 রেফার করুন",
        "ℹ️ নিয়মাবলী",
        "📤 উইথড্র করুন",
        "🧑‍💼 অ্যাডমিন"
    ]
    markup.add(*buttons)
    return markup


# 🟢 /start Command with Referral System
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
            'submitted': False,
            'withdraw': []
        })

        if ref_id and ref_id != user_id:
            ref_ref = db.reference(f'users/{ref_id}')
            if ref_ref.get():
                ref_ref.child('referrals').set(ref_ref.child('referrals').get() + 1)
                ref_bonus = 10
                ref_ref.child('balance').set(ref_ref.child('balance').get() + ref_bonus)
                bot.send_message(int(ref_id), f'🎉 একজন নতুন রেফারেল জয়েন করেছে! আপনি {ref_bonus} টাকা পেয়েছেন।')

    bot.send_message(msg.chat.id, "🎉 স্বাগতম! আপনার মেনু থেকে অপশন বেছে নিন।", reply_markup=main_menu())


# 🎯 Show Tasks
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


# 💰 Balance & Referral Count
@bot.message_handler(func=lambda msg: msg.text == "💰 ব্যালেন্স")
def balance(msg):
    user_id = str(msg.chat.id)
    data = db.reference(f'users/{user_id}').get()
    bal = data.get('balance', 0)
    refs = data.get('referrals', 0)
    bot.send_message(msg.chat.id, f"💰 ব্যালেন্স: {bal} টাকা\n👥 রেফার: {refs} জন")


# 👬 Referral Link
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


# 💸 Withdraw System
@bot.message_handler(func=lambda msg: msg.text == "📤 উইথড্র করুন")
def withdraw(msg):
    user_id = str(msg.chat.id)
    data = db.reference(f'users/{user_id}').get()
    balance = data.get("balance", 0)

    if balance < 1000:
        bot.send_message(msg.chat.id, "❌ আপনার ব্যালেন্স উইথড্র করার জন্য যথেষ্ট নয়। কমপক্ষে ১০০০ টাকা লাগবে।")
        return

    bot.send_message(msg.chat.id, "💳 আপনার bKash/Nagad/Rocket নাম্বার দিন যার মাধ্যমে টাকা তুলতে চান:")
    bot.register_next_step_handler(msg, process_withdraw_number)


# 🧾 Process Withdraw Request
def process_withdraw_number(msg):
    number = msg.text
    user_id = str(msg.chat.id)
    withdraw_ref = db.reference(f'users/{user_id}/withdraw')

    withdraw_ref.push({
        'number': number,
        'status': 'pending'
    })

    bot.send_message(msg.chat.id, "✅ আপনার উইথড্র রিকোয়েস্ট গ্রহণ করা হয়েছে। অ্যাডমিন রিভিউ করবেন।")
    bot.send_message(ADMIN_ID, f"📥 উইথড্র রিকোয়েস্ট:\n👤 ইউজার: {user_id}\n📱 নাম্বার: {number}",
                     reply_markup=withdraw_admin_markup(user_id, number))


# 🧑‍⚖️ Withdraw Admin Approval Buttons
def withdraw_admin_markup(user_id, number):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_withdraw:{user_id}:{number}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_withdraw:{user_id}:{number}")
    )
    return markup


# ⚙️ Withdraw Callback Handler
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_withdraw") or call.data.startswith("reject_withdraw"))
def handle_withdraw_callback(call):
    action, user_id, number = call.data.split(":")
    user_ref = db.reference(f'users/{user_id}')

    if action == "approve_withdraw":
        user_data = user_ref.get()
        balance = user_data.get('balance', 0)

        if balance >= 1000:
            user_ref.child('balance').set(balance - 1000)
            bot.send_message(int(user_id), f"✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে অনুমোদিত হয়েছে। টাকা পাঠানো হয়েছে: {number}")
            bot.edit_message_text("✅ Approve করা হয়েছে।", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(int(user_id), f"❌ আপনার উইথড্র রিকোয়েস্ট বাতিল করা হয়েছে।")
        bot.edit_message_text("❌ Reject করা হয়েছে।", call.message.chat.id, call.message.message_id)


# ℹ️ Rules Handler
@bot.message_handler(func=lambda msg: msg.text == "ℹ️ নিয়মাবলী")
def rules(msg):
    bot.send_message(msg.chat.id, "📌 নিয়মাবলী:\n\n১. সব টাস্ক সত্যভাবে করতে হবে।\n২. ভুয়া স্ক্রিনশট দিলে অ্যাকাউন্ট ব্লক হবে।")


# 🌐 Dummy HTTP Server for Railway/Render
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is alive and running."


# 🌍 Run HTTP Server
def run_http():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


# 🔁 Start Server and Bot
threading.Thread(target=run_http).start()
print("✅ Bot is running...")
bot.infinity_polling()
