import os
import json
import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db

# Secrets from environment (GitHub Actions)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
FIREBASE_CRED = os.getenv("FIREBASE_CREDENTIALS")
FIREBASE_DB_URL = "https://cpabot-a1604-default-rtdb.firebaseio.com"

# Firebase Init
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(FIREBASE_CRED))
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })

ref = db.reference("/users")

bot = telebot.TeleBot(BOT_TOKEN)

# Get user data or create default
def get_user(user_id):
    user_ref = ref.child(str(user_id))
    user = user_ref.get()
    if not user:
        user = {"balance": 0, "referrals": 0, "submitted": False}
        user_ref.set(user)
    return user

def update_user(user_id, data):
    ref.child(str(user_id)).update(data)

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    user = get_user(user_id)

    if len(message.text.split()) > 1:
        referrer = message.text.split()[1]
        if referrer != user_id:
            ref_user = get_user(referrer)
            ref_user['referrals'] += 1
            ref_user['balance'] += 10
            update_user(referrer, ref_user)
            bot.send_message(int(referrer), "✅ আপনি একজন কে রেফার করেছেন এবং ১০ টাকা পেয়েছেন!")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎯 টাস্ক", "💸 ব্যালেন্স", "📤 স্ক্রিনশট জমা দিন")
    markup.add("👥 রেফার", "📥 উইথড্র", "🧑‍💻 এডমিন")
    bot.send_message(message.chat.id, "✨ স্বাগতম! একটি অপশন নির্বাচন করুন:", reply_markup=markup)

# Task info
@bot.message_handler(func=lambda m: m.text == "🎯 টাস্ক")
def show_tasks(message):
    bot.send_message(message.chat.id, "🧾 নিচে আপনার টাস্ক লিঙ্ক:\n\n1️⃣ https://example.com\n2️⃣ https://example2.com\n3️⃣ https://example3.com\n4️⃣ https://example4.com\n\n📝 প্রতিটি টাস্কে ৩টি স্ক্রিনশট দিন। প্রতিটি টাস্কের জন্য ৩০ টাকা পাবেন।")

# Balance
@bot.message_handler(func=lambda m: m.text == "💸 ব্যালেন্স")
def show_balance(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id, f"💰 আপনার ব্যালেন্স: {user['balance']} টাকা\n👥 রেফার সংখ্যা: {user['referrals']}")

# Refer
@bot.message_handler(func=lambda m: m.text == "👥 রেফার")
def refer_info(message):
    user_id = str(message.from_user.id)
    link = f"https://t.me/myoffer363bot?start={user_id}"
    refs = get_user(user_id)["referrals"]
    bot.send_message(message.chat.id, f"🔗 আপনার রেফার লিঙ্ক:\n{link}\n\n👥 মোট রেফার: {refs}\n💵 প্রতি রেফার = ১০ টাকা")

# Screenshot submit
@bot.message_handler(func=lambda m: m.text == "📤 স্ক্রিনশট জমা দিন")
def submit_screenshot(message):
    update_user(message.from_user.id, {"submitted": True})
    bot.send_message(message.chat.id, "📸 দয়া করে আপনার টাস্ক স্ক্রিনশট পাঠান (৩টি)।")

# Withdraw
@bot.message_handler(func=lambda m: m.text == "📥 উইথড্র")
def withdraw_request(message):
    user = get_user(message.from_user.id)
    if user["balance"] >= 1000:
        bot.send_message(message.chat.id, "💳 আপনি কোন মাধ্যমে টাকা তুলতে চান?\nbKash / Nagad / Rocket সহ নাম্বার পাঠান:")
    else:
        bot.send_message(message.chat.id, "❌ মিনিমাম ১০০০ টাকা ব্যালেন্স থাকতে হবে উইথড্র করার জন্য।")

# Admin panel
@bot.message_handler(func=lambda m: m.text == "🧑‍💻 এডমিন")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👁️ ইউজার দেখুন", callback_data="view_user"))
    markup.add(types.InlineKeyboardButton("✏️ ইউজার এডিট", callback_data="edit_user"))
    bot.send_message(message.chat.id, "🛠️ এডমিন অপশন:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "view_user":
        bot.send_message(call.message.chat.id, "🆔 ইউজার আইডি দিন:")
        bot.register_next_step_handler(call.message, process_view_user)
    elif call.data == "edit_user":
        bot.send_message(call.message.chat.id, "✏️ ইউজার আইডি দিন:")
        bot.register_next_step_handler(call.message, process_edit_user)

def process_view_user(message):
    uid = message.text.strip()
    user = ref.child(uid).get()
    if user:
        bot.send_message(message.chat.id, f"🧑 ইউজার {uid}:\n💰 ব্যালেন্স: {user['balance']} টাকা\n👥 রেফার: {user['referrals']}")
    else:
        bot.send_message(message.chat.id, "❌ ইউজার খুঁজে পাওয়া যায়নি।")

def process_edit_user(message):
    uid = message.text.strip()
    if ref.child(uid).get():
        bot.send_message(message.chat.id, "📥 নতুন ব্যালেন্স দিন:")
        bot.register_next_step_handler(message, lambda m: update_balance(m, uid))
    else:
        bot.send_message(message.chat.id, "❌ ইউজার খুঁজে পাওয়া যায়নি।")

def update_balance(message, uid):
    try:
        new_balance = int(message.text.strip())
        update_user(uid, {"balance": new_balance})
        bot.send_message(message.chat.id, f"✅ ইউজার {uid} এর ব্যালেন্স আপডেট হয়েছে: {new_balance} টাকা")
    except:
        bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা দিন।")

# Approve/Reject system
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    uid = str(message.from_user.id)
    user = get_user(uid)
    if user.get("submitted"):
        caption = f"🆔 ইউজার: {uid}\n✅ স্ক্রিনশট জমা দিয়েছে"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{uid}"))
        markup.add(types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}"))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup)
        update_user(uid, {"submitted": False})

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def approve_reject(call):
    uid = call.data.split("_")[1]
    if call.data.startswith("approve"):
        user = get_user(uid)
        user["balance"] += 30
        update_user(uid, user)
        bot.send_message(int(uid), "✅ আপনার টাস্ক এপ্রুভ হয়েছে! ৩০ টাকা যোগ হয়েছে।")
    else:
        bot.send_message(int(uid), "❌ আপনার টাস্ক রিজেক্ট হয়েছে। দয়া করে সঠিকভাবে পূর্ণরায় দিন।")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

# Start bot
bot.infinity_polling()
