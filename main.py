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
def main_menu(user_id=None):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "🎯 টাস্ক করুন",
        "📷 স্ক্রিনশট সাবমিট",
        "💰 ব্যালেন্স",
        "👫 রেফার করুন",
        "ℹ️ নিয়মাবলী",
        "📤 উইথড্র করুন"
    ]
    # এডমিন হলে অ্যাডমিন বাটন দেখাবে
    if user_id and int(user_id) == ADMIN_ID:
        buttons.append("🧑‍💼 অ্যাডমিন")
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
            'withdraw': [],
            'tasks_completed': 0
        })

        if ref_id and ref_id != user_id:
            ref_ref = db.reference(f'users/{ref_id}')
            if ref_ref.get():
                current_refs = ref_ref.child('referrals').get() or 0
                ref_ref.child('referrals').set(current_refs + 1)
                current_balance = ref_ref.child('balance').get() or 0
                ref_bonus = 10
                ref_ref.child('balance').set(current_balance + ref_bonus)
                bot.send_message(int(ref_id), f'🎉 একজন নতুন রেফারেল জয়েন করেছে! আপনি {ref_bonus} টাকা পেয়েছেন।')

    bot.send_message(msg.chat.id, "🎉 স্বাগতম! আপনার মেনু থেকে অপশন বেছে নিন।", reply_markup=main_menu(user_id))


# 🎯 Show Tasks with Rules and 20 Tasks
@bot.message_handler(func=lambda msg: msg.text == "🎯 টাস্ক করুন")
def task(msg):
    task_text = (
        "📢 নিচের টাস্কগুলো সম্পন্ন করুন:\n\n"
        "★ প্রতিটি টাস্কে ৩টি করে স্ক্রিনশট দিতে হবে।\n"
        "★ স্ক্রিনশট দেখে এডমিনরা টাস্ক এপ্রুভ করবেন।\n"
        "★ ভুল বা ফেক স্ক্রিনশট দিলে একাউন্ট ব্যান হবে।\n"
        "★ সঠিকভাবে স্ক্রিনশট দিলে ১০০% উইথড্র পাবেন।\n"
        "★ ১টি টাস্ক শেষে কমপক্ষে ১০ মিনিট বিরতি দিতে হবে পরবর্তী টাস্ক করার আগে।\n\n"
        "টাস্ক লিস্ট:\n"
    )

    tasks = {
        "1": "Pin submit - https://tinyurl.com/37xxp2an",
        "2": "Pin submit - https://tinyurl.com/4vc76fw5",
        "3": "Sign-up - https://tinyurl.com/yyherfxt",
        "4": "Sign-up - https://tinyurl.com/25nt96v9",
        "5": "Any - https://trianglerockers.com/1830624",
        "6": "Any - https://trianglerockers.com/1830624",
        "7": "Any - https://trianglerockers.com/1830624",
        "8": "Any - https://trianglerockers.com/1830624",
        "9": "Pin or sign-up - https://short-link.me/19jeX",
        "10": "Pin or sign-up - https://short-link.me/19jfx",
        "11": "Pin or sign-up - https://short-link.me/19jfZ",
        "12": "Pin or sign-up - https://short-link.me/19jfx",
        "13": "Pin or sign-up - https://short-link.me/19jgz",
        "14": "Pin or sign-up - https://short-link.me/19jeX",
        "15": "Pin or sign-up - https://short-link.me/19jfx",
        "16": "Pin or sign-up - https://short-link.me/19jeX",
        "17": "Pin or sign-up - https://short-link.me/19jfx",
        "18": "Pin or sign-up - https://short-link.me/19jgz",
        "19": "Pin or sign-up - https://short-link.me/19jfx",
        "20": "Pin or sign-up - https://short-link.me/19jeX"
    }

    for k, v in tasks.items():
        task_text += f"{k}. {v}\n\n"

    bot.send_message(msg.chat.id, task_text)


# 📷 Screenshot Submission (same as before)
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
    data = db.reference(f'users/{user_id}').get() or {}
    bal = data.get('balance', 0)
    refs = data.get('referrals', 0)
    bot.send_message(msg.chat.id, f"💰 ব্যালেন্স: {bal} টাকা\n👥 রেফার: {refs} জন")


# 👬 Referral Link
@bot.message_handler(func=lambda msg: msg.text == "👫 রেফার করুন")
def refer(msg):
    link = f"https://t.me/myoffer363bot?start={msg.chat.id}"
    bot.send_message(msg.chat.id, f"📢 এই লিংকে বন্ধুদের ইনভাইট করুন:\n{link}")


# 🧑‍💼 Admin Panel (Only visible to ADMIN_ID)
@bot.message_handler(func=lambda msg: msg.text == "🧑‍💼 অ্যাডমিন" and msg.chat.id == ADMIN_ID)
def admin(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 ইউজার এডিট", "📋 মোট ইউজার", "🔙 মেইন মেনু")
    bot.send_message(msg.chat.id, "🧑‍💼 এডমিন প্যানেল:", reply_markup=markup)


# 📝 ইউজার এডিট হ্যান্ডলার
@bot.message_handler(func=lambda msg: msg.text == "📝 ইউজার এডিট" and msg.chat.id == ADMIN_ID)
def user_edit_start(msg):
    bot.send_message(msg.chat.id, "📌 ইউজার আইডি দিন যাকে এডিট করতে চান:")
    bot.register_next_step_handler(msg, user_edit_get_user)


def user_edit_get_user(msg):
    user_id = msg.text.strip()
    user_ref = db.reference(f'users/{user_id}')
    if not user_ref.get():
        bot.send_message(msg.chat.id, "❌ ইউজার পাওয়া যায়নি। আবার চেষ্টা করুন।")
        return
    data = user_ref.get()
    info_text = (
        f"🧑‍💻 ইউজার: {user_id}\n"
        f"💰 ব্যালেন্স: {data.get('balance',0)}\n"
        f"👥 রেফার: {data.get('referrals',0)}\n"
        f"🎯 টাস্ক সংখ্যা: {data.get('tasks_completed',0)}\n\n"
        f"নতুন ব্যালেন্স দিন:"
    )
    bot.send_message(msg.chat.id, info_text)
    bot.register_next_step_handler(msg, user_edit_update_balance, user_id)


def user_edit_update_balance(msg, user_id):
    try:
        new_balance = int(msg.text.strip())
    except ValueError:
        bot.send_message(msg.chat.id, "❌ অনুগ্রহ করে একটি সংখ্যা লিখুন। আবার চেষ্টা করুন।")
        return
    user_ref = db.reference(f'users/{user_id}')
    user_ref.update({'balance': new_balance})
    bot.send_message(msg.chat.id, f"✅ ইউজার {user_id} এর ব্যালেন্স সফলভাবে আপডেট হয়েছে: {new_balance} টাকা।")


# 📋 মোট ইউজার লিস্ট দেখানো
@bot.message_handler(func=lambda msg: msg.text == "📋 মোট ইউজার" and msg.chat.id == ADMIN_ID)
def show_all_users(msg):
    all_users = db.reference('users').get() or {}
    if not all_users:
        bot.send_message(msg.chat.id, "❌ কোনো ইউজার পাওয়া যায়নি।")
        return

    lines = []
    for uid, info in all_users.items():
        bal = info.get('balance', 0)
        refs = info.get('referrals', 0)
        tasks = info.get('tasks_completed', 0)
        lines.append(f"👤 {uid} | 💰 {bal} টাকা | 👥 {refs} রেফার | 🎯 {tasks} টাস্ক")

    chunk_size = 20  # প্রতি মেসেজে ২০ ইউজার দেখাবো
    for i in range(0, len(lines), chunk_size):
        bot.send_message(msg.chat.id, "\n".join(lines[i:i+chunk_size]))


# 💸 Withdraw System
@bot.message_handler(func=lambda msg: msg.text == "📤 উইথড্র করুন")
def withdraw(msg):
    user_id = str(msg.chat.id)
    data = db.reference(f'users/{user_id}').get() or {}
    balance = data.get("balance", 0)

    if balance < 600:
        bot.send_message(msg.chat.id, "❌ আপনার ব্যালেন্স উইথড্র করার জন্য কমপক্ষে ৬০০ টাকা থাকতে হবে।")
        return

    bot.send_message(msg.chat.id, "💳 নাম দিন:")
    bot.register_next_step_handler(msg, process_withdraw_name)


def process_withdraw_name(msg):
    name = msg.text.strip()
    bot.send_message(msg.chat.id, "📞 মোবাইল নম্বর দিন:")
    bot.register_next_step_handler(msg, process_withdraw_mobile, name)


def process_withdraw_mobile(msg, name):
    mobile = msg.text.strip()
    bot.send_message(msg.chat.id, "💳 পেমেন্ট মেথড দিন (bKash, Nagad, Rocket):")
    bot.register_next_step_handler(msg, process_withdraw_method, name, mobile)


def process_withdraw_method(msg, name, mobile):
    method = msg.text.strip()
    if method not in ["bKash", "Nagad", "Rocket"]:
        bot.send_message(msg.chat.id, "❌ শুধুমাত্র bKash, Nagad, অথবা Rocket ব্যবহার করুন। আবার চেষ্টা করুন।")
        bot.register_next_step_handler(msg, process_withdraw_method, name, mobile)
        return
    bot.send_message(msg.chat.id, "💰 উইথড্র এমাউন্ট দিন:")
    bot.register_next_step_handler(msg, process_withdraw_amount, name, mobile, method)


def process_withdraw_amount(msg, name, mobile, method):
    try:
        amount = int(msg.text.strip())
    except ValueError:
        bot.send_message(msg.chat.id, "❌ অনুগ্রহ করে একটি সঠিক সংখ্যা দিন। আবার চেষ্টা করুন।")
        bot.register_next_step_handler(msg, process_withdraw_amount, name, mobile, method)
        return

    user_id = str(msg.chat.id)
    data = db.reference(f'users/{user_id}').get() or {}
    balance = data.get("balance", 0)

    if amount < 600:
        bot.send_message(msg.chat.id, "❌ উইথড্রের জন্য ন্যূনতম পরিমাণ ৬০০ টাকা। আবার চেষ্টা করুন।")
        bot.register_next_step_handler(msg, process_withdraw_amount, name, mobile, method)
        return
    if amount > balance:
        bot.send_message(msg.chat.id, "❌ আপনার ব্যালেন্স উইথড্রের জন্য যথেষ্ট নয়। আবার চেষ্টা করুন।")
        bot.register_next_step_handler(msg, process_withdraw_amount, name, mobile, method)
        return

    withdraw_ref = db.reference(f'withdraw_requests')
    withdraw_ref.push({
        'user_id': user_id,
        'name': name,
        'mobile': mobile,
        'method': method,
        'amount': amount,
        'status': 'pending'
    })

    bot.send_message(msg.chat.id, "✅ আপনার উইথড্র রিকোয়েস্ট গ্রহণ করা হয়েছে। অ্যাডমিন রিভিউ করবেন।")
    bot.send_message(ADMIN_ID,
                     f"📥 উইথড্র রিকোয়েস্ট:\n👤 ইউজার: {user_id}\n👤 নাম: {name}\n📱 মোবাইল: {mobile}\n💳 মেথড: {method}\n💰 এমাউন্ট: {amount}",
                     reply_markup=withdraw_admin_markup(user_id))


# 🧑‍⚖️ Withdraw Admin Approval Buttons
def withdraw_admin_markup(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_withdraw:{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_withdraw:{user_id}")
    )
    return markup


# ⚙️ Withdraw Callback Handler
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_withdraw") or call.data.startswith("reject_withdraw"))
def handle_withdraw_callback(call):
    action, user_id = call.data.split(":")
    user_ref = db.reference(f'users/{user_id}')
    withdraw_requests = db.reference('withdraw_requests').order_by_child('user_id').equal_to(user_id).get()

    if action == "approve_withdraw":
        # প্রথম পেন্ডিং রিকোয়েস্ট আপডেট করা হবে
        for key, req in withdraw_requests.items():
            if req.get('status') == 'pending':
                amount = req.get('amount', 0)
                user_data = user_ref.get()
                balance = user_data.get('balance', 0)
                if balance >= amount:
                    user_ref.child('balance').set(balance - amount)
                    db.reference(f'withdraw_requests/{key}').update({'status': 'approved'})
                    bot.send_message(int(user_id), f"✅ আপনার উইথড্র রিকোয়েস্ট অনুমোদিত হয়েছে। {amount} টাকা পাঠানো হয়েছে।")
                    bot.edit_message_text("✅ Approve করা হয়েছে।", call.message.chat.id, call.message.message_id)
                else:
                    bot.edit_message_text("❌ ব্যালেন্স অপর্যাপ্ত।", call.message.chat.id, call.message.message_id)
                return
        bot.edit_message_text("❌ কোনো পেন্ডিং রিকোয়েস্ট পাওয়া যায়নি।", call.message.chat.id, call.message.message_id)

    else:
        for key, req in withdraw_requests.items():
            if req.get('status') == 'pending':
                db.reference(f'withdraw_requests/{key}').update({'status': 'rejected'})
                bot.send_message(int(user_id), "❌ আপনার উইথড্র রিকোয়েস্ট বাতিল করা হয়েছে।")
                bot.edit_message_text("❌ Reject করা হয়েছে।", call.message.chat.id, call.message.message_id)
                return
        bot.edit_message_text("❌ কোনো পেন্ডিং রিকোয়েস্ট পাওয়া যায়নি।", call.message.chat.id, call.message.message_id)


# ℹ️ Rules Handler
@bot.message_handler(func=lambda msg: msg.text == "ℹ️ নিয়মাবলী")
def rules(msg):
    rules_text = (
        "📌 নিয়মাবলী:\n\n"
        "১. সব টাস্ক সত্যভাবে করতে হবে।\n"
        "২. ভুল বা ফেক স্ক্রিনশট দিলে অ্যাকাউন্ট ব্লক হবে।\n"
        "৩. কমপক্ষে ১০ মিনিট বিরতি দিয়ে পরবর্তী টাস্ক করতে হবে।"
    )
    bot.send_message(msg.chat.id, rules_text)


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
