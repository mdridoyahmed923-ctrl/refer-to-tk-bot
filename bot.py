import json, os, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== SETTINGS =====
TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
ADMIN_USERNAME = "Hridoyvhai146"
DEPOSIT_NUMBER = "01408886128"
MIN_DEPOSIT = 50
WORKER_REWARD = 1
ADVERTISER_COST = 2
MIN_WITHDRAW = 100
DB_FILE = "database.json"
BLOCKED_WORDS = ["18+", "porn", "xxx", "sex", "nude", "adult", "onlyfans", "pornhub"]

# Flask for Render 24h alive
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Refer to Tk Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "tasks": {}, "deposits": {}, "withdraws": {}, "task_counter": 0}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "tasks": {}, "deposits": {}, "withdraws": {}, "task_counter": 0}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def get_user(db, user_id, username=""):
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {"username": username, "balance": 0, "deposit_balance": 0, "refer_by": None, "done_tasks": [], "total_earn": 0}
    return db["users"][uid]

def main_menu():
    kb = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"), InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("💵 Deposit", callback_data="deposit"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📋 Task List (Earn)", callback_data="task_list"), InlineKeyboardButton("➕ Add Task", callback_data="add_task")],
        [InlineKeyboardButton("📊 My Tasks", callback_data="my_tasks"), InlineKeyboardButton("🆘 Support", callback_data="support")],
    ]
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user = update.effective_user
    u = get_user(db, user.id, user.username or "")
    if context.args:
        try:
            ref_id = context.args[0].replace("ref_", "")
            if ref_id != str(user.id) and u["refer_by"] is None:
                u["refer_by"] = ref_id
        except: pass
    save_db(db)
    text = f"👋 আসসালামু আলাইকুম {user.first_name}!\n\n🎉 Refer to Tk এ স্বাগতম!\n\n💰 প্রতি টাস্কে পাবে ১ টাকা\n♾️ আনলিমিটেড কাজ করতে পারবে\n\n📢 তোমার লিংক প্রমোট করতে চাইলে Deposit করে Task অ্যাড করো।\nপ্রতি টাস্কে খরচ ২ টাকা।"
    await update.message.reply_text(text, reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    user = q.from_user
    u = get_user(db, user.id, user.username or "")
    data = q.data

    if data == "balance":
        await q.edit_message_text(f"💰 তোমার Balance\n\n💵 Earn Balance: {u['balance']} টাকা\n💳 Deposit Balance: {u['deposit_balance']} টাকা\n✅ সম্পন্ন টাস্ক: {len(u['done_tasks'])} টি\n\nWithdraw মিনিমাম {MIN_WITHDRAW} টাকা।", reply_markup=main_menu())
    elif data == "refer":
        link = f"https://t.me/Hridovhaibot?start=ref_{user.id}"
        await q.edit_message_text(f"👥 Refer & Earn\n\nতোমার লিংক:\n`{link}`\n\nবন্ধু জয়েন করলে বোনাস পাবা।", reply_markup=main_menu(), parse_mode="Markdown")
    elif data == "deposit":
        await q.edit_message_text(f"💵 Deposit\n\nমিনিমাম: {MIN_DEPOSIT} টাকা\n\n১. {DEPOSIT_NUMBER} নাম্বারে বিকাশ / নগদ থেকে Send Money করো\n২. TrxID কপি করো\n৩. এইভাবে পাঠাও:\n`/deposit 50 TrxID1234 Bkash`\n\nAdmin Approve করলেই যোগ হবে।", reply_markup=main_menu(), parse_mode="Markdown")
    elif data == "withdraw":
        await q.edit_message_text(f"💸 Withdraw\n\nBalance: {u['balance']} টাকা\nমিনিমাম: {MIN_WITHDRAW} টাকা\n\nলিখো:\n`/withdraw 100 Bkash 01408886128`", reply_markup=main_menu(), parse_mode="Markdown")
    elif data == "task_list":
        tasks = [t for t in db["tasks"].values() if t["active"] and str(user.id) not in t["done_by"] and t["owner"] != str(user.id)]
        if not tasks:
            await q.edit_message_text("😔 এখন কোনো টাস্ক নাই। পরে আবার চেক করো।", reply_markup=main_menu()); return
        text = "📋 Available Tasks - প্রতি টাস্কে ১ টাকা\n\n"
        kb = []
        for t in tasks[:10]:
            text += f"🔹 {t['title']} - {t['type']} - {t['left']} টা বাকি\n"
            kb.append([InlineKeyboardButton(f"✅ {t['title'][:20]} - ১ টাকা", callback_data=f"do_{t['id']}")])
        kb.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("do_"):
        tid = data.replace("do_", "")
        t = db["tasks"].get(tid)
        if not t:
            await q.edit_message_text("টাস্ক পাওয়া যায় নাই।", reply_markup=main_menu()); return
        if t["type"] == "Telegram":
            text = f"📢 {t['title']}\n\n১. নিচের লিংকে জয়েন করো:\n{t['link']}\n২. জয়েন করে Verify চাপ দাও\n\nReward: ১ টাকা"
            kb = [[InlineKeyboardButton("🔗 Join Channel", url=t['link'])], [InlineKeyboardButton("✅ Verify Join", callback_data=f"verify_{tid}")], [InlineKeyboardButton("🔙 Back", callback_data="back")]]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
        else:
            text = f"🎬 {t['title']}\n\nType: {t['type']}\n\n১. লিংকে যাও:\n{t['link']}\n২. {t['type']} করো\n৩. Screenshot তুলে পাঠাও\n\nলিখো: `/proof {tid}` তারপর Screenshot পাঠাও\nReward: ১ টাকা"
            kb = [[InlineKeyboardButton("🔗 Open Link", url=t['link'])], [InlineKeyboardButton("🔙 Back", callback_data="back")]]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("verify_"):
        tid = data.replace("verify_", "")
        t = db["tasks"].get(tid)
        try:
            chat_id = "@" + t['link'].split("/")[-1]
            member = await context.bot.get_chat_member(chat_id, user.id)
            if member.status in ["member", "administrator", "creator"]:
                u["balance"] += WORKER_REWARD
                u["total_earn"] += WORKER_REWARD
                u["done_tasks"].append(tid)
                t["done_by"].append(str(user.id))
                t["left"] -= 1
                owner = db["users"].get(t["owner"])
                if owner: owner["deposit_balance"] -= ADVERTISER_COST
                if t["left"] <= 0: t["active"] = False
                save_db(db)
                await q.edit_message_text(f"✅ Verified! তুমি পাইছো ১ টাকা।\nনতুন Balance: {u['balance']} টাকা", reply_markup=main_menu())
            else:
                await q.edit_message_text("❌ তুমি এখনো জয়েন করো নাই। আগে জয়েন করো।", reply_markup=main_menu())
        except:
            await q.edit_message_text(f"⚠️ বট চ্যানেলে Admin নাই। Screenshot পাঠাও, Admin Approve করবে।\nলিখো: `/proof {tid}` তারপর Screenshot পাঠাও", reply_markup=main_menu())
    elif data == "add_task":
        await q.edit_message_text(f"➕ Add Task\n\nDeposit Balance: {u['deposit_balance']} টাকা\nপ্রতি টাস্কে খরচ: ২ টাকা\n\nলিখো:\n`/addtask Telegram | My Channel | https://t.me/xxx | 10`\n\nType: Telegram / YouTubeSub / YouTubeView / TikTokFollow\n\n⚠️ ১৮+ লিংক অ্যাড করলে ID ব্যান হবে।", reply_markup=main_menu(), parse_mode="Markdown")
    elif data == "my_tasks":
        my = [t for t in db["tasks"].values() if t["owner"] == str(user.id)]
        if not my:
            await q.edit_message_text("তুমি এখনো কোনো টাস্ক অ্যাড করো নাই।", reply_markup=main_menu()); return
        text = "📊 তোমার টাস্ক:\n\n"
        for t in my:
            text += f"🔹 {t['title']} - বাকি: {t['left']}/{t['total']}\n"
        await q.edit_message_text(text, reply_markup=main_menu())
    elif data == "support":
        await q.edit_message_text(f"🆘 Support\n\nAdmin: @{ADMIN_USERNAME}", reply_markup=main_menu())
    elif data == "back":
        await q.edit_message_text("👇 মেনু থেকে বেছে নাও:", reply_markup=main_menu())
    save_db(db)

async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user = update.effective_user
    u = get_user(db, user.id, user.username or "")
    text = update.message.text or ""
    args = text.split()
    if text.startswith("/deposit"):
        if len(args) < 4:
            await update.message.reply_text("লিখো: `/deposit 50 TrxID Bkash`", parse_mode="Markdown"); return
        try: amt = int(args[1])
        except: await update.message.reply_text("টাকার পরিমাণ সংখ্যায় লিখো।"); return
        if amt < MIN_DEPOSIT:
            await update.message.reply_text(f"মিনিমাম {MIN_DEPOSIT} টাকা।"); return
        trx = args[2]; method = args[3]
        db["deposits"][f"{user.id}_{trx}"] = {"user": str(user.id), "amount": amt, "trx": trx, "method": method, "status": "pending"}
        save_db(db)
        await update.message.reply_text(f"✅ Deposit Request পাঠানো হইছে!\nAmount: {amt} টাকা\nTrxID: {trx}\nAdmin Approve করলেই যোগ হবে।")
    elif text.startswith("/approve_deposit"):
        if user.username != ADMIN_USERNAME:
            await update.message.reply_text("তুমি Admin না।"); return
        if len(args) < 3: await update.message.reply_text("লিখো: `/approve_deposit user_id trx`"); return
        key = f"{args[1]}_{args[2]}"
        d = db["deposits"].get(key)
        if not d: await update.message.reply_text("Deposit পাওয়া যায় নাই।"); return
        target = get_user(db, int(args[1]))
        target["deposit_balance"] += d["amount"]
        d["status"] = "approved"
        save_db(db)
        await update.message.reply_text(f"✅ Approved! {d['amount']} টাকা যোগ হইছে।")
        try: await context.bot.send_message(chat_id=int(args[1]), text=f"✅ তোমার {d['amount']} টাকা Deposit Approve হইছে!")
        except: pass
    elif text.startswith("/withdraw"):
        if len(args) < 4: await update.message.reply_text("লিখো: `/withdraw 100 Bkash 014...`"); return
        try: amt = int(args[1])
        except: await update.message.reply_text("টাকা সংখ্যায় লিখো।"); return
        if amt < MIN_WITHDRAW: await update.message.reply_text(f"মিনিমাম {MIN_WITHDRAW} টাকা।"); return
        if u["balance"] < amt: await update.message.reply_text("Balance যথেষ্ট নাই।"); return
        u["balance"] -= amt
        db["withdraws"][f"{user.id}_{len(db['withdraws'])}"] = {"user": str(user.id), "amount": amt, "method": args[2], "number": args[3], "status": "pending"}
        save_db(db)
        await update.message.reply_text(f"✅ Withdraw Request পাঠানো হইছে: {amt} টাকা।")
    elif text.startswith("/addtask"):
        try:
            parts = text.replace("/addtask ", "").split("|")
            typ = parts[0].strip(); title = parts[1].strip(); link = parts[2].strip(); count = int(parts[3].strip())
        except:
            await update.message.reply_text("ফরম্যাট ভুল! `/addtask Telegram | Title | Link | 10`"); return
        low = (title + " " + link).lower()
        if any(w in low for w in BLOCKED_WORDS):
            await update.message.reply_text("⛔ ১৮+ / Adult লিংক অ্যাড করা যাবে না।"); return
        cost = count * ADVERTISER_COST
        if u["deposit_balance"] < cost:
            await update.message.reply_text(f"❌ Deposit Balance যথেষ্ট নাই। লাগবে {cost} টাকা, আছে {u['deposit_balance']} টাকা।"); return
        db["task_counter"] += 1
        tid = str(db["task_counter"])
        db["tasks"][tid] = {"id": tid, "owner": str(user.id), "type": typ, "title": title, "link": link, "total": count, "left": count, "active": True, "done_by": []}
        save_db(db)
        await update.message.reply_text(f"✅ Task অ্যাড হইছে!\n{title}\nTotal: {count} জন\nখরচ হবে: {cost} টাকা")
    elif text.startswith("/proof"):
        if len(args) < 2: await update.message.reply_text("লিখো: `/proof task_id` তারপর Screenshot পাঠাও।"); return
        context.user_data["proof_task"] = args[1]
        await update.message.reply_text("এখন Screenshot টা পাঠাও। Admin Approve করবে।")
    elif text.startswith("/approve_task"):
        if user.username != ADMIN_USERNAME: await update.message.reply_text("তুমি Admin না।"); return
        if len(args) < 3: await update.message.reply_text("লিখো: `/approve_task task_id user_id`"); return
        tid, worker_id = args[1], args[2]
        t = db["tasks"].get(tid)
        worker = get_user(db, int(worker_id))
        if not t: await update.message.reply_text("Task নাই।"); return
        if worker_id in t["done_by"]: await update.message.reply_text("আগেই Approve করা হইছে।"); return
        worker["balance"] += WORKER_REWARD
        worker["total_earn"] += WORKER_REWARD
        worker["done_tasks"].append(tid)
        t["done_by"].append(worker_id)
        t["left"] -= 1
        owner = db["users"].get(t["owner"])
        if owner: owner["deposit_balance"] -= ADVERTISER_COST
        if t["left"] <= 0: t["active"] = False
        save_db(db)
        await update.message.reply_text("✅ Task Approve হইছে, Worker ১ টাকা পাইছে।")
        try: await context.bot.send_message(chat_id=int(worker_id), text=f"✅ তোমার টাস্ক Approve হইছে! ১ টাকা পাইছো। Balance: {worker['balance']} টাকা")
        except: pass
    save_db(db)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = context.user_data.get("proof_task")
    if not tid:
        await update.message.reply_text("আগে `/proof task_id` লিখো, তারপর Screenshot পাঠাও।"); return
    await update.message.reply_text("✅ Screenshot পাঠানো হইছে। Admin Approve করলেই ১ টাকা পাবা।")
    context.user_data["proof_task"] = None

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.COMMAND, handle_commands))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
