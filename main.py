import os
import json
import threading

import telebot
from telebot import types

from flask import Flask

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Environment variables থেকে token ও admin id নিন
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Firebase credentials লোড করুন
cred_data = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_data)

firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv("FIREBASE_DB_URL")
})

bot = telebot.TeleBot(BOT_TOKEN)

new_tasks = {
    "1": "✅ Pin submit: https://tinyurl.com/37xxp2an",
    "2": "✅ Pin submit: https://tinyurl.com/4vc76fw5",
    "3": "✅ Sign-up: https://tinyurl.com/yyherfxt",
    "4": "✅ Sign-up: https://tinyurl.com/25nt96v9",
    "5": "✅ Any: https://trianglerockers.com/1830624",
    "6": "✅ Any: https://trianglerockers.com/1830624",
    "7": "✅ Any: https://trianglerockers.com/1830624",
    "8": "✅ Any: https://trianglerockers.com/1830624",
    "9": "✅ Pin or Sign-up: https://short-link.me/19jeX",
    "10": "✅ Pin or Sign-up: https://short-link.me/19jfx",
    "11": "✅ Pin or Sign-up: https://short-link.me/19jfZ",
    "12": "✅ Pin or Sign-up: https://short-link.me/19jfx",
    "13": "✅ Pin or Sign-up: https://short-link.me/19jgz",
    "14": "✅ Pin or Sign-up: https://short-link.me/19jeX",
    "15": "✅ Pin or Sign-up: https://short-link.me/19jfx",
    "16": "✅ Pin or Sign-up: https://short-link.me/19jeX",
    "17": "✅ Pin or Sign-up: https://short-link.me/19jfx",
    "18": "✅ Pin or Sign-up: https://short-link.me/19jgz",
    "19": "✅ Pin or Sign-up: https://short-link.me/19jfx",
    "20": "✅ Pin or Sign-up: https://short-link.me/19jeX"
}

MIN_WITHDRAW_AMOUNT = 600

# ইউজারের স্ক্রিনশট সাবমিশন স্টেট ট্র্যাক করার জন্য dict
user_screenshot_state = {}

def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "🎯 টাস্ক করুন",
        "📷 স্ক্রিনশট সাবমিট",
        "💰 ব্যালেন্স",
        "👫 রেফার করুন",
        "ℹ️ নিয়মাবলী",
        "📤 উইথড্র করুন"
    ]
    if user_id == ADMIN_ID:
        buttons.append("🧑‍💼 অ্যাডমিন")
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = str(msg.chat.id)
    ref_id = None
    try:
        ref_id = str(msg.text.split()[1])
    except IndexError:
        ref_id = None

    user_ref = db.reference(f'users/{user_id}')

    if not user_ref.get():
        user_ref.set({
            'balance': 0,
            'referrals': 0,
            'screenshots': [],
            'submitted': False,
            'submitted_task': "",
            'withdraw': []
        })

        if ref_id and ref_id != user_id:
            ref_ref = db.reference(f'users/{ref_id}')
            if ref_ref.get():
                current_referrals = ref_ref.child('referrals').get() or 0
                ref_ref.child('referrals').set(current_referrals + 1)

                current_balance = ref_ref.child('balance').get() or 0
                ref_bonus = 10
                ref_ref.child('balance').set(current_balance + ref_bonus)

                bot.send_message(int(ref_id), f'🎉 একজন নতুন রেফারেল জয়েন করেছে! আপনি {ref_bonus} টাকা পেয়েছেন।')

    bot.send_message(msg.chat.id, "🎉 স্বাগতম! আপনার মেনু থেকে অপশন বেছে নিন।", reply_markup=main_menu(msg.chat.id))

@bot.message_handler(func=lambda msg: msg.text == "🎯 টাস্ক করুন")
def task(msg):
    task_text = "💸 প্রতি টাস্কে ৩০ টাকা পেমেন্ট দেওয়া হয়।\n\n"
    task_text += "📢 নিচের টাস্কগুলো সম্পন্ন করুন:\n\n"
    for k, v in new_tasks.items():
        task_text += f"{k}. {v}\n\n"
    bot.send_message(msg.chat.id, task_text)

# ================================
# স্ক্রিনশট সাবমিশন সিস্টেম আপডেট শুরু
# ================================

@bot.message_handler(func=lambda msg: msg.text == "📷 স্ক্রিনশট সাবমিট")
def request_screenshots(msg):
    user_id = str(msg.chat.id)
    user_data = db.reference(f'users/{user_id}').get() or {}
    existing_screenshots = user_data.get('screenshots', [])
    
    if existing_screenshots and len(existing_screenshots) >= 3:
        bot.send_message(msg.chat.id, "✅ আপনি ইতোমধ্যে ৩টি স্ক্রিনশট জমা দিয়েছেন। দয়া করে অপেক্ষা করুন।")
        return

    # ইউজারের স্ক্রিনশট জমা স্টেট রিসেট ও শুরু করা
    user_screenshot_state[user_id] = {
        'task': None,
        'screenshots': []
    }
    
    # টাস্ক লিস্ট থেকে সিলেকশন করাতে হবে
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for k, v in new_tasks.items():
        markup.add(types.KeyboardButton(f"{k}. {v}"))
    bot.send_message(msg.chat.id, "দয়া করে টাস্ক সিলেক্ট করুন যার স্ক্রিনশট জমা দিতে চান:", reply_markup=markup)

@bot.message_handler(func=lambda msg: str(msg.chat.id) in user_screenshot_state and user_screenshot_state[str(msg.chat.id)]['task'] is None)
def task_selected(msg):
    user_id = str(msg.chat.id)
    text = msg.text.strip()
    task_id = text.split('.')[0]  # "১. ..." থেকে শুধু ১ নিয়ে আসবে
    
    if task_id not in new_tasks:
        bot.send_message(msg.chat.id, "❌ অনুগ্রহ করে লিস্ট থেকে টাস্কটি সিলেক্ট করুন।")
        return

    user_screenshot_state[user_id]['task'] = task_id
    bot.send_message(msg.chat.id, f"আপনি সিলেক্ট করেছেন: {new_tasks[task_id]}\n\nএখন ৩টি স্ক্রিনশট একে একে পাঠান।")

@bot.message_handler(content_types=['photo'])
def handle_photo(msg):
    user_id = str(msg.chat.id)

    # যদি স্ক্রিনশট সাবমিশন স্টেট না থাকে
    if user_id not in user_screenshot_state or user_screenshot_state[user_id]['task'] is None:
        # আগের কোড অনুযায়ী হ্যান্ডল করতে পারেন
        existing = db.reference(f'users/{user_id}/screenshots').get() or []
        if len(existing) >= 3:
            bot.send_message(msg.chat.id, "✅ আপনি ইতোমধ্যে ৩টি স্ক্রিনশট জমা দিয়েছেন। দয়া করে অপেক্ষা করুন।")
            return
        else:
            bot.send_message(msg.chat.id, "স্ক্রিনশট জমা দিতে প্রথমে '📷 স্ক্রিনশট সাবমিট' বাটন চাপুন এবং টাস্ক সিলেক্ট করুন।")
            return

    # যদি স্টেট আছে, তাহলে স্ক্রিনশট যোগ করুন
    current_screenshots = user_screenshot_state[user_id]['screenshots']
    current_screenshots.append(msg.photo[-1].file_id)
    user_screenshot_state[user_id]['screenshots'] = current_screenshots
    bot.send_message(msg.chat.id, f"📸 স্ক্রিনশট {len(current_screenshots)} জমা হয়েছে।")

    if len(current_screenshots) == 3:
        # ৩টি স্ক্রিনশট জমা হলে Firebase এ আপডেট করুন
        user_ref = db.reference(f'users/{user_id}')
        user_ref.update({
            'screenshots': current_screenshots,
            'submitted_task': user_screenshot_state[user_id]['task'],
            'submitted': True
        })

        # এডমিনকে স্ক্রিনশট ও টাস্ক সহ পাঠান
        media_group = [types.InputMediaPhoto(fid) for fid in current_screenshots]
        bot.send_media_group(ADMIN_ID, media_group)
        task_name = new_tasks[user_screenshot_state[user_id]['task']]
        bot.send_message(ADMIN_ID, f"👤 ইউজার: {user_id}\nটাস্ক: {task_name}\n\nস্ক্রিনশট যাচাই করুন:", reply_markup=approve_reject_markup(user_id))

        bot.send_message(msg.chat.id, "✅ আপনার স্ক্রিনশট সফলভাবে জমা হয়েছে। এপ্রুভ হলে আপনাকে জানানো হবে।")

        # স্টেট ক্লিয়ার করুন
        del user_screenshot_state[user_id]

def approve_reject_markup(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_ss:{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_ss:{user_id}")
    )
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_ss") or call.data.startswith("reject_ss"))
def handle_ss_approval(call):
    action, user_id = call.data.split(":")
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get() or {}
    balance = user_data.get('balance', 0)

    if action == "approve_ss":
        user_ref.child('balance').set(balance + 30)
        user_ref.child('screenshots').set([])
        user_ref.child('submitted').set(False)
        user_ref.child('submitted_task').set("")
        bot.send_message(int(user_id), "🎉 আপনার স্ক্রিনশট এপ্রুভ হয়েছে। ৩০ টাকা ব্যালেন্সে যোগ হয়েছে।")
        bot.edit_message_text("✅ Approve করা হয়েছে।", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(int(user_id), "❌ আপনার টাস্ক পূরণ সঠিক হয়নি। স্ক্রিনশট রিজেক্ট করা হয়েছে। আবার চেষ্টা করুন।")
        user_ref.child('screenshots').set([])
        user_ref.child('submitted').set(False)
        user_ref.child('submitted_task').set("")
        bot.edit_message_text("❌ Reject করা হয়েছে।", call.message.chat.id, call.message.message_id)

# ================================
# স্ক্রিনশট সাবমিশন সিস্টেম আপডেট শেষ
# ================================

@bot.message_handler(func=lambda msg: msg.text == "💰 ব্যালেন্স")
def balance(msg):
    user_id = str(msg.chat.id)
    data = db.reference(f'users/{user_id}').get() or {}
    bal = data.get('balance', 0)
    refs = data.get('referrals', 0)
    bot.send_message(msg.chat.id, f"💰 ব্যালেন্স: {bal} টাকা\n👥 রেফার: {refs} জন")

@bot.message_handler(func=lambda msg: msg.text == "👫 রেফার করুন")
def refer(msg):
    link = f"https://t.me/myoffer363bot?start={msg.chat.id}"
    bot.send_message(msg.chat.id, f"📢 এই লিংকে বন্ধুদের ইনভাইট করুন:\n{link}\n\n💰 প্রতি রেফারের জন্য ১০ টাকা রিওয়ার্ড পাবেন।")

@bot.message_handler(func=lambda msg: msg.text == "📤 উইথড্র করুন")
def withdraw(msg):
    user_id = str(msg.chat.id)
    data = db.reference(f'users/{user_id}').get() or {}
    balance = data.get("balance", 0)

    if balance < MIN_WITHDRAW_AMOUNT:
        bot.send_message(msg.chat.id, f"❌ আপনার ব্যালেন্স উইথড্র করার জন্য যথেষ্ট নয়। কমপক্ষে {MIN_WITHDRAW_AMOUNT} টাকা লাগবে।",
                         reply_markup=main_menu(msg.chat.id))
        return

    bot.send_message(msg.chat.id, "💳 আপনার bKash/Nagad/Rocket নাম্বার দিন যার মাধ্যমে টাকা তুলতে চান:",
                     reply_markup=main_menu(msg.chat.id))
    bot.register_next_step_handler(msg, process_withdraw_number)

def process_withdraw_number(msg):
    number = msg.text.strip()
    user_id = str(msg.chat.id)
    withdraw_ref = db.reference(f'users/{user_id}/withdraw')

    withdraw_ref.push({
        'number': number,
        'status': 'pending'
    })

    bot.send_message(msg.chat.id, "✅ আপনার উইথড্র রিকোয়েস্ট গ্রহণ করা হয়েছে। অ্যাডমিন রিভিউ করবেন।")
    bot.send_message(ADMIN_ID, f"📥 উইথড্র রিকোয়েস্ট:\n👤 ইউজার: {user_id}\n📱 নাম্বার: {number}", reply_markup=withdraw_admin_markup(user_id, number))

def withdraw_admin_markup(user_id, number):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_withdraw:{user_id}:{number}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_withdraw:{user_id}:{number}")
    )
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_withdraw") or call.data.startswith("reject_withdraw"))
def handle_withdraw_callback(call):
    action, user_id, number = call.data.split(":")
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get() or {}
    balance = user_data.get('balance', 0)

    if action == "approve_withdraw":
        if balance >= MIN_WITHDRAW_AMOUNT:
            user_ref.child('balance').set(balance - MIN_WITHDRAW_AMOUNT)
            bot.send_message(int(user_id), f"✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে অনুমোদিত হয়েছে। টাকা পাঠানো হয়েছে: {number}")
            bot.edit_message_text("✅ Approve করা হয়েছে।", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "ইউজারের ব্যালেন্স কম আছে!")
    else:
        bot.send_message(int(user_id), "❌ আপনার উইথড্র রিকোয়েস্ট বাতিল করা হয়েছে।")
        bot.edit_message_text("❌ Reject করা হয়েছে।", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: msg.text == "ℹ️ নিয়মাবলী")
def rules(msg):
    bot.send_message(msg.chat.id, (
        "📌 এখানে মূলত Email, Pin, Sign-Up এই সার্ভে গুলো পূরণ করতে হয়।\n"
        "✅ প্রতিটি টাস্কে ৩টি করে স্ক্রিনশট দিতে হবে।\n"
        "🔍 স্ক্রিনশট দেখে এডমিনরা টাস্কগুলো এপ্রুভ করবে।\n"
        "🚫 ভুল বা ফেক স্ক্রিনশট দিলে একাউন্ট ব্যান হবে।\n"
        "✅ যারা সঠিকভাবে সার্ভে পূরণ ও স্ক্রিনশট সাবমিট করবে, তারাই ১০০% উইথড্র করতে পারবে কোনো ঝামেলা ছাড়াই।\n"
        "⏱️ ১টি টাস্ক পূরণ করার পর মিনিমাম ১০ মিনিট বিরতি দিয়ে পরবর্তী টাস্ক পূরণ করতে হবে।"
    ))
# ================================
# অ্যাডমিন প্যানেল আপডেট শুরু (আগের কোডের শেষে)
# ================================

@bot.message_handler(func=lambda msg: msg.text == "🧑‍💼 অ্যাডমিন" and msg.chat.id == ADMIN_ID)
def admin_panel(msg):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("👀 ইউজার দেখুন", callback_data="admin_view_users"),
        types.InlineKeyboardButton("✏️ ইউজার এডিট", callback_data="admin_edit_user")
    )
    bot.send_message(msg.chat.id, "অ্যাডমিন প্যানেল থেকে অপশন বেছে নিন:", reply_markup=markup)

# ইউজার দেখার জন্য callback
@bot.callback_query_handler(func=lambda call: call.data == "admin_view_users" and call.from_user.id == ADMIN_ID)
def admin_view_users(call):
    all_users = db.reference('users').get() or {}
    if not all_users:
        bot.answer_callback_query(call.id, "কোনো ইউজার পাওয়া যায়নি।")
        return
    msg_text = "📋 সকল ইউজার এর তথ্য:\n\n"
    for uid, data in all_users.items():
        bal = data.get('balance', 0)
        refs = data.get('referrals', 0)
        submitted_task = data.get('submitted_task', 'None')
        submitted = data.get('submitted', False)
        msg_text += (
            f"👤 ইউজার আইডি: {uid}\n"
            f"💰 ব্যালেন্স: {bal} টাকা\n"
            f"👥 রেফার: {refs} জন\n"
            f"📝 সাবমিট করা টাস্ক: {submitted_task}\n"
            f"📸 সাবমিশন স্ট্যাটাস: {'হ্যাঁ' if submitted else 'না'}\n\n"
        )
    # যদি অনেক বড় হয়, টুকরো পাঠাতে পারেন, এখানে একবারে পাঠানো হলো
    bot.send_message(call.message.chat.id, msg_text)
    bot.answer_callback_query(call.id)

# ইউজার এডিট এর জন্য callback (স্টেপ বাই স্টেপ)
admin_edit_state = {}

@bot.callback_query_handler(func=lambda call: call.data == "admin_edit_user" and call.from_user.id == ADMIN_ID)
def admin_edit_user_start(call):
    bot.send_message(call.message.chat.id, "🔢 ইউজারের আইডি লিখুন যার ব্যালেন্স পরিবর্তন করতে চান:")
    admin_edit_state[call.message.chat.id] = {'step': 'awaiting_user_id'}
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda msg: msg.chat.id in admin_edit_state and admin_edit_state[msg.chat.id]['step'] == 'awaiting_user_id')
def admin_receive_user_id(msg):
    user_id = msg.text.strip()
    user_ref = db.reference(f'users/{user_id}')
    if not user_ref.get():
        bot.send_message(msg.chat.id, "❌ ইউজার আইডি পাওয়া যায়নি। আবার চেষ্টা করুন।")
        return
    admin_edit_state[msg.chat.id]['user_id'] = user_id
    admin_edit_state[msg.chat.id]['step'] = 'awaiting_new_balance'
    bot.send_message(msg.chat.id, f"✅ ইউজার পাওয়া গেছে: {user_id}\n\nনতুন ব্যালেন্স (টাকায়) লিখুন:")

@bot.message_handler(func=lambda msg: msg.chat.id in admin_edit_state and admin_edit_state[msg.chat.id]['step'] == 'awaiting_new_balance')
def admin_receive_new_balance(msg):
    try:
        new_balance = int(msg.text.strip())
        if new_balance < 0:
            raise ValueError
    except ValueError:
        bot.send_message(msg.chat.id, "❌ অনুগ্রহ করে একটি বৈধ ধনাত্মক সংখ্যা লিখুন।")
        return

    user_id = admin_edit_state[msg.chat.id]['user_id']
    user_ref = db.reference(f'users/{user_id}')
    user_ref.child('balance').set(new_balance)
    bot.send_message(msg.chat.id, f"✅ ইউজার {user_id} এর ব্যালেন্স সফলভাবে আপডেট হয়েছে: {new_balance} টাকা।")
    del admin_edit_state[msg.chat.id]

# ================================
# অ্যাডমিন প্যানেল আপডেট শেষ
# ================================


# Flask app এবং polling (আগের মতোই)

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is alive and running."

def run_http():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Flask সার্ভার আলাদা থ্রেডে রান করুন
threading.Thread(target=run_http).start()

bot.infinity_polling()
