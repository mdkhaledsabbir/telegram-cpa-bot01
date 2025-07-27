import os
import json
import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db

# 🔐 Secrets from environment (GitHub Actions)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
FIREBASE_CRED = os.getenv("FIREBASE_CREDENTIALS")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")

# 🔐 Firebase Init
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(FIREBASE_CRED))
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })

ref = db.reference("/users")
bot = telebot.TeleBot(BOT_TOKEN)

# -------------------------------
# Get user data or create default
def get_user(user_id):
    user_ref = ref.child(str(user_id))
    user = user_ref.get()
    if not user:
        user = {
            "balance": 0,
            "referrals": 0,
            "submitted": False,
            "rejected_before": False  # To track if user was rejected before
        }
        user_ref.set(user)
    return user

def update_user(user_id, data):
    ref.child(str(user_id)).update(data)

# -------------------------------
# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    user = get_user(user_id)

    # Handle referral
    if len(message.text.split()) > 1:
        referrer = message.text.split()[1]
        if referrer != user_id:
            ref_user = get_user(referrer)
            ref_user['referrals'] += 1
            ref_user['balance'] += 10
            update_user(referrer, ref_user)
            bot.send_message(int(referrer), "✅ আপনি একজনকে রেফার করেছেন এবং ১০ টাকা পেয়েছেন!")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # ৯টি বাটন এখানে যোগ করা হয়েছে
    markup.add("🎯 টাস্ক", "💸 ব্যালেন্স", "📤 স্ক্রিনশট জমা দিন")
    markup.add("👥 রেফার", "📥 উইথড্র", "🧑‍💻 এডমিন")
    markup.add("📜 নিয়মাবলী", "📞 যোগাযোগ", "ℹ️ সাহায্য")

    bot.send_message(message.chat.id, "✨ স্বাগতম! একটি অপশন নির্বাচন করুন:", reply_markup=markup)

# -------------------------------
# Task info
@bot.message_handler(func=lambda m: m.text == "🎯 টাস্ক")
def show_tasks(message):
    bot.send_message(message.chat.id, "🧾 নিচে আপনার টাস্ক লিঙ্ক:\n\n"
                                     "1️⃣ https://example.com\n"
                                     "2️⃣ https://example2.com\n"
                                     "3️⃣ https://example3.com\n"
                                     "4️⃣ https://example4.com\n\n"
                                     "📝 প্রতিটি টাস্কে ৩টি স্ক্রিনশট দিন। প্রতিটি টাস্কের জন্য ৩০ টাকা পাবেন।")

# -------------------------------
# Balance
@bot.message_handler(func=lambda m: m.text == "💸 ব্যালেন্স")
def show_balance(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id, f"💰 আপনার ব্যালেন্স: {user['balance']} টাকা\n👥 রেফার সংখ্যা: {user['referrals']}")

# -------------------------------
# Referral info
@bot.message_handler(func=lambda m: m.text == "👥 রেফার")
def refer_info(message):
    user_id = str(message.from_user.id)
    link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    refs = get_user(user_id)["referrals"]
    bot.send_message(message.chat.id, f"🔗 আপনার রেফার লিঙ্ক:\n{link}\n\n👥 মোট রেফার: {refs}\n💵 প্রতি রেফার = ১০ টাকা")

# -------------------------------
# Screenshot submission
@bot.message_handler(func=lambda m: m.text == "📤 স্ক্রিনশট জমা দিন")
def submit_screenshot(message):
    user_id = str(message.from_user.id)
    update_user(user_id, {"submitted": True})
    bot.send_message(message.chat.id, "📸 দয়া করে আপনার টাস্ক স্ক্রিনশট পাঠান (৩টি)।")

# -------------------------------
# Withdraw request
@bot.message_handler(func=lambda m: m.text == "📥 উইথড্র")
def withdraw_request(message):
    user = get_user(message.from_user.id)
    if user["balance"] >= 1000:
        bot.send_message(message.chat.id, "💳 আপনি কোন মাধ্যমে টাকা তুলতে চান?\nউদাহরণ: bKash / Nagad / Rocket সহ নাম্বার পাঠান:")
    else:
        bot.send_message(message.chat.id, "❌ মিনিমাম ১০০০ টাকা ব্যালেন্স থাকতে হবে উইথড্র করার জন্য।")

# -------------------------------
# Rules button
@bot.message_handler(func=lambda m: m.text == "📜 নিয়মাবলী")
def rules(message):
    rules_text = ("📋 টাস্ক নিয়মাবলী:\n"
                  "1. প্রতিটি টাস্কের জন্য ৩টি স্পষ্ট স্ক্রিনশট দিন।\n"
                  "2. স্ক্রিনশট অবশ্যই টাস্ক সম্পূর্ণ করার প্রমাণ হতে হবে।\n"
                  "3. ভুলে বা অসত্য স্ক্রিনশট দিলে আপনার টাস্ক বাতিল হতে পারে।\n"
                  "4. রিজেক্ট হলে আবার চেষ্টা করার সুযোগ পাবেন।\n"
                  "5. অন্যদের বিরক্ত করবেন না।")
    bot.send_message(message.chat.id, rules_text)

# -------------------------------
# Contact button
@bot.message_handler(func=lambda m: m.text == "📞 যোগাযোগ")
def contact(message):
    contact_text = "📞 যোগাযোগ:\n- Telegram: @adminusername\n- Email: admin@example.com\n- Phone: +880123456789"
    bot.send_message(message.chat.id, contact_text)

# -------------------------------
# Help button
@bot.message_handler(func=lambda m: m.text == "ℹ️ সাহায্য")
def help_info(message):
    help_text = ("ℹ️ সাহায্য:\n"
                 "টাস্ক সম্পর্কে, স্ক্রিনশট জমা দেওয়া এবং অন্যান্য বিষয় সম্পর্কে সাহায্যের জন্য আমাদের সাথে যোগাযোগ করুন।")
    bot.send_message(message.chat.id, help_text)

# -------------------------------
# Admin panel
@bot.message_handler(func=lambda m: m.text == "🧑‍💻 এডমিন")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👁️ ইউজার দেখুন", callback_data="view_user"))
    markup.add(types.InlineKeyboardButton("✏️ ইউজার এডিট", callback_data="edit_user"))
    bot.send_message(message.chat.id, "🛠️ এডমিন অপশন:", reply_markup=markup)

# -------------------------------
# Callback handler for admin buttons & approve/reject
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data

    if data == "view_user":
        bot.send_message(call.message.chat.id, "🆔 ইউজার আইডি দিন:")
        bot.register_next_step_handler(call.message, process_view_user)

    elif data == "edit_user":
        bot.send_message(call.message.chat.id, "✏️ ইউজার আইডি দিন:")
        bot.register_next_step_handler(call.message, process_edit_user)

    elif data.startswith("approve_"):
        uid = data.split("_")[1]
        user = get_user(uid)
        user["balance"] += 30
        # Reset rejected flag on approval
        user["rejected_before"] = False
        update_user(uid, user)
        bot.send_message(int(uid), "✅ আপনার টাস্ক এপ্রুভ হয়েছে! ৩০ টাকা যোগ হয়েছে।")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    elif data.startswith("reject_"):
        uid = data.split("_")[1]
        user = get_user(uid)
        user["rejected_before"] = True
        update_user(uid, user)
        bot.send_message(int(uid), "❌ আপনার টাস্ক পূরণ ভুল হয়েছে। নিয়মগুলো অনুসরণ করে আবার চেষ্টা করুন।")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

# -------------------------------
# View User Info (admin)
def process_view_user(message):
    uid = message.text.strip()
    user = ref.child(uid).get()
    if user:
        bot.send_message(message.chat.id, f"🧑 ইউজার {uid}:\n💰 ব্যালেন্স: {user['balance']} টাকা\n👥 রেফার: {user['referrals']}")
    else:
        bot.send_message(message.chat.id, "❌ ইউজার খুঁজে পাওয়া যায়নি।")

# -------------------------------
# Edit User (admin)
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

# -------------------------------
# Handle incoming photos (screenshots)
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    uid = str(message.from_user.id)
    user = get_user(uid)

    if user.get("submitted", False):
        caption = f"🆔 ইউজার: {uid}\n✅ স্ক্রিনশট জমা দিয়েছে"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{uid}"))
        markup.add(types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}"))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup)
        # Mark submitted false to wait for admin decision
        update_user(uid, {"submitted": False})
    else:
        bot.send_message(message.chat.id, "❌ আপনি প্রথমে স্ক্রিনশট জমা দেওয়ার জন্য '📤 স্ক্রিনশট জমা দিন' বাটনে ক্লিক করুন।")

# -------------------------------
bot.infinity_polling()
