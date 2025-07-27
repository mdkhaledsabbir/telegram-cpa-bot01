import os
import json
import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db

# 🔐 Load Secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
firebase_creds_str = os.getenv("FIREBASE_CREDENTIALS")
firebase_creds = json.loads(firebase_creds_str)

# ✅ Initialize Firebase
cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://cpabot-a1604-default-rtdb.firebaseio.com/'
})
ref = db.reference('users')

bot = telebot.TeleBot(BOT_TOKEN)

# ✅ CPA Tasks
TASKS = {
    "Task 1": "📌 Pin Submit: https://tinyurl.com/37xxp2an\n🖼 ৩টি স্ক্রিনশট দিন",
    "Task 2": "📌 Pin Submit: https://tinyurl.com/4vc76fw5\n🖼 ৩টি স্ক্রিনশট দিন",
    "Task 3": "📧 Email Submit: https://tinyurl.com/yyherfxt\n🖼 ৩টি স্ক্রিনশট দিন",
    "Task 4": "📧 Email Submit: https://tinyurl.com/25nt96v9\n🖼 ৩টি স্ক্রিনশট দিন"
}

# ✅ Start Command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    data = ref.get() or {}
    if user_id not in data:
        data[user_id] = {'referrals': 0, 'balance': 0, 'submitted': False}
        ref_code = message.text.split(' ')[1] if len(message.text.split()) > 1 else None
        if ref_code and ref_code in data and ref_code != user_id:
            data[ref_code]['referrals'] += 1
            data[ref_code]['balance'] += 10
            bot.send_message(int(ref_code), f"🎉 আপনি ১টি রেফারেল পেয়েছেন!\n💰 ব্যালেন্স এখন: ৳{data[ref_code]['balance']}")
    ref.set(data)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 টাস্কগুলো", "📤 স্ক্রিনশট জমা", "💸 ব্যালেন্স", "📨 উইথড্র", "👥 রেফার লিংক")
    bot.send_message(message.chat.id, "স্বাগতম! নিচের বাটনগুলো ব্যবহার করুন 👇", reply_markup=markup)

# ✅ Task List
@bot.message_handler(func=lambda m: m.text == "📝 টাস্কগুলো")
def task_list(message):
    msg = "🔹 বর্তমান টাস্কসমূহ:\n\n"
    for title, link in TASKS.items():
        msg += f"✅ {title}\n{link}\n\n"
    bot.send_message(message.chat.id, msg)

# ✅ Screenshot prompt
@bot.message_handler(func=lambda m: m.text == "📤 স্ক্রিনশট জমা")
def ask_screenshot(message):
    bot.send_message(message.chat.id, "🔄 দয়া করে ৩টি স্ক্রিনশট এক এক করে পাঠান।")

# ✅ Screenshot handling
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = str(message.chat.id)
    caption = f"🆔 ইউজার ID: {user_id}\n👤 ইউজারনেম: @{message.chat.username or 'N/A'}"
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(ADMIN_ID, caption)
    bot.send_message(message.chat.id, "✅ আপনার স্ক্রিনশট গ্রহণ করা হয়েছে। চেক করে এপ্রুভ করা হবে।")

# ✅ Balance check
@bot.message_handler(func=lambda m: m.text == "💸 ব্যালেন্স")
def check_balance(message):
    user_id = str(message.chat.id)
    data = ref.get() or {}
    user = data.get(user_id, {})
    balance = user.get('balance', 0)
    referrals = user.get('referrals', 0)
    bot.send_message(message.chat.id, f"💰 ব্যালেন্স: ৳{balance} টাকা\n👥 রেফার: {referrals} জন")

# ✅ Withdraw
@bot.message_handler(func=lambda m: m.text == "📨 উইথড্র")
def withdraw(message):
    user_id = str(message.chat.id)
    data = ref.get() or {}
    if user_id not in data:
        return bot.send_message(message.chat.id, "❌ তথ্য খুঁজে পাওয়া যায়নি।")

    balance = data[user_id]['balance']
    if balance >= 1000:
        bot.send_message(message.chat.id, "✅ আপনার উইথড্র রিকোয়েস্ট গ্রহণ করা হয়েছে।\n📅 পেমেন্ট ৩১ তারিখে দেওয়া হবে।")
        bot.send_message(ADMIN_ID, f"📨 @{message.chat.username or user_id} উইথড্র চেয়েছে। ব্যালেন্স: ৳{balance}")
    else:
        bot.send_message(message.chat.id, "❌ উইথড্র এর জন্য অন্তত ১০০০ টাকা থাকতে হবে।")

# ✅ Referral link
@bot.message_handler(func=lambda m: m.text == "👥 রেফার লিংক")
def referral_link(message):
    bot.send_message(message.chat.id, f"🔗 আপনার রেফার লিংক:\nhttps://t.me/{bot.get_me().username}?start={message.chat.id}\n\n👥 প্রতি রেফারে ১০ টাকা!")

# ✅ Admin: Check user balance
@bot.message_handler(commands=['balance'])
def admin_check_balance(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        target = message.text.split()[1]
        data = ref.get() or {}
        if target in data:
            bal = data[target]['balance']
            ref_count = data[target]['referrals']
            bot.send_message(message.chat.id, f"📊 ইউজার {target}:\n💰 ব্যালেন্স: ৳{bal}\n👥 রেফার: {ref_count}")
        else:
            bot.send_message(message.chat.id, "❌ ইউজার খুঁজে পাওয়া যায়নি।")
    except:
        bot.send_message(message.chat.id, "⚠️ কমান্ড ভুল!\nব্যবহার: /balance <user_id>")

# ✅ Run the bot
bot.infinity_polling()
