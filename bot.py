import json, os, threading
from flask import Flask, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== SETTINGS =====
TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
ADMIN_USERNAME = "Hridoyvhai146"
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8418239556"))
DEPOSIT_NUMBER = "01408886128"
MIN_DEPOSIT = 50
WORKER_REWARD = 1
ADVERTISER_COST = 2
MIN_WITHDRAW = 100
DB_FILE = "database.json"
BLOCKED_WORDS = ["18+", "porn", "xxx", "sex", "nude", "adult", "onlyfans", "pornhub"]

def is_admin(user):
    if not user:
        return False
    if user.id == ADMIN_ID:
        return True
    if user.username and user.username.lower() == ADMIN_USERNAME.lower():
        return True
    return False

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

app_flask = Flask(__name__)

@app_flask.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@app_flask.route("/")
def home():
    return "Refer to Tk Bot is Running!"

@app_flask.route("/tasks")
def get_tasks():
    db = load_db()
    tasks = []
    for tid, t in db.get("tasks", {}).items():
        if t.get("active") and t.get("left", 0) > 0:
            tasks.append({"id": tid, "title": t["title"], "link": t["link"], "type": t["type"], "left": t["left"], "total": t["total"]})
    return jsonify(tasks)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

def main_menu(admin=False):
    kb = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"), InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("💵 Deposit", callback_data="deposit"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📋 Task List (Earn)", callback_data="task_list"), InlineKeyboardButton("➕ Add Task", callback_data="add_task")],
        [InlineKeyboardButton("📊 My Tasks", callback_data="my_tasks"), InlineKeyboardButton("🆘 Support", callback_data="support")],
    ]
    if admin:
        kb.append([InlineKeyboardButton("👨‍💻 Master Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(kb)

def admin_menu():
    kb = [
        [InlineKeyboardButton("📥 Pending Deposits", callback_data="admin_deposits"), InlineKeyboardButton("💸 Pending Withdraws", callback_data="admin_withdraws")],
        [InlineKeyboardButton("👥 All Users", callback_data="admin_users"), InlineKeyboardButton("📋 All Tasks", callback_data="admin_tasks")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")],
    ]
    return InlineKeyboardMarkup(kb)

async def show_admin_panel(q, db):
    pending_dep = len([d for d in db.get("deposits", {}).values() if d.get("status") == "pending"])
    pending_wd = len([w for w in db.get("withdraws", {}).values() if w.get("status") == "pending"])
    text = f"👨‍💻 Master Admin Panel\n\n👥 Total Users: {len(db.get('users', {}))}\n📋 Total Tasks: {len(db.get('tasks', {}))}\n📥 Pending Deposits: {pending_dep}\n💸 Pending Withdraws: {pending_wd}\n\n👇 নিচ থেকে বেছে নাও:"
    await q.edit_message_text(text, reply_markup=admin_menu())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user = update.effective_user
    u = get_user(db, user.id, user.username or "")
    if context.args:
        try:
            ref_id = context.args[0].replace("ref_", "")
            if ref_id != str(user.id) and u["refer_by"] is None:
                u["refer_by"] = ref_id
        except:
            pass
    save_db(db)
    await update.message.reply_text(f"👋 Welcome {user.first_name}!\n\n💰 Balance: {u['balance']} টাকা\n👥 Refer করে আয় করো!\n\n👇 মেনু থেকে বেছে নাও:", reply_markup=main_menu(admin=is_admin(user)))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    user = q.from_user
    u = get_user(db, user.id, user.username or "")
    data = q.data
    admin = is_admin(user)
    if data == "balance":
        await q.edit_message_text(f"💰 তোমার Balance\n\nEarn Balance: {u['balance']} টাকা\nDeposit Balance: {u['deposit_balance']} টাকা\nTotal Earn: {u['total_earn']} টাকা", reply_markup=main_menu(admin=admin))
    elif data == "refer":
        link = f"https://t.me/{context.bot.username}?start=ref_{user.id}"
        await q.edit_message_text(f"👥 Refer Link:\n{link}\n\nপ্রতি Refer এ বোনাস পাবা!", reply_markup=main_menu(admin=admin))
    elif data == "deposit":
        await q.edit_message_text(f"💵 Deposit\n\nNumber: {DEPOSIT_NUMBER}\nমিনিমাম: {MIN_DEPOSIT} টাকা\n\nলিখো: `/deposit 50 TrxID Bkash`", reply_markup=main_menu(admin=admin))
    elif data == "withdraw":
        await q.edit_message_text(f"💸 Withdraw\n\nBalance: {u['balance']} টাকা\nমিনিমাম: {MIN_WITHDRAW} টাকা\n\nলিখো: `/withdraw 100 Bkash 014...`", reply_markup=main_menu(admin=admin))
    elif data == "task_list":
        text = "📋 Task List:\n\n"
        found = False
        for tid, t in db.get("tasks", {}).items():
            if t.get("active") and t.get("left", 0) > 0:
                found = True
                text += f"ID: {tid} | {t['title']}\nLink: {t['link']}\nবাকি: {t['left']}/{t['total']} | Reward: {WORKER_REWARD} টাকা\n\n"
        if not found:
            text = "এখন কোনো টাস্ক নাই।"
        else:
            text += "কাজ শেষে লিখো: `/proof task_id` তারপর Screenshot পাঠাও। বট নিজেই Auto Approve করবে।"
        await q.edit_message_text(text, reply_markup=main_menu(admin=admin))
    elif data == "add_task":
        await q.edit_message_text("➕ Add Task\n\nলিখো:\n`/addtask Telegram | Title | Link | 10`", reply_markup=main_menu(admin=admin))
    elif data == "my_tasks":
        my = [t for t in db.get("tasks", {}).values() if str(t.get("owner")) == str(user.id)]
        text = "📊 তোমার টাস্ক:\n\n"
        if not my:
            text = "তুমি এখনো কোনো টাস্ক দাও নাই।"
        else:
            for t in my:
                text += f"🔹 {t['title']} - বাকি: {t['left']}/{t['total']}\n"
        await q.edit_message_text(text, reply_markup=main_menu(admin=admin))
    elif data == "support":
        await q.edit_message_text(f"🆘 Support\n\nAdmin: @{ADMIN_USERNAME}", reply_markup=main_menu(admin=admin))
    elif data == "admin_panel":
        if not admin:
            await q.edit_message_text("তুমি Admin না।", reply_markup=main_menu(admin=False))
            return
        await show_admin_panel(q, db)
    elif data == "admin_deposits":
        if not admin:
            return
        text = "📥 Pending Deposits:\n\n"
        found = False
        for key, d in db.get("deposits", {}).items():
            if d.get("status") == "pending":
                found = True
                text += f"User: {d['user']} | {d['amount']} টাকা | Trx: {d['trx']} | {d['method']}\nApprove: `/approve_deposit {d['user']} {d['trx']}`\n\n"
        if not found:
            text = "কোনো Pending Deposit নাই।"
        await q.edit_message_text(text, reply_markup=admin_menu())
    elif data == "admin_withdraws":
        if not admin:
            return
        text = "💸 Pending Withdraws:\n\n"
        found = False
        for key, w in db.get("withdraws", {}).items():
            if w.get("status") == "pending":
                found = True
                text += f"User: {w['user']} | {w['amount']} টাকা | {w['method']} {w['number']}\n\n"
        if not found:
            text = "কোনো Pending Withdraw নাই।"
        await q.edit_message_text(text, reply_markup=admin_menu())
    elif data == "admin_users":
        if not admin:
            return
        text = f"👥 Total Users: {len(db.get('users', {}))}\n\n"
        for uid, ud in list(db.get("users", {}).items())[:20]:
            text += f"ID: {uid} | @{ud.get('username','')} | Bal: {ud.get('balance',0)} | Dep: {ud.get('deposit_balance',0)}\n"
        await q.edit_message_text(text, reply_markup=admin_menu())
    elif data == "admin_tasks":
        if not admin:
            return
        text = "📋 All Tasks:\n\n"
        for tid, t in db.get("tasks", {}).items():
            text += f"ID: {tid} | {t['title']} | বাকি: {t['left']}/{t['total']} | Active: {t.get('active')}\n"
        if not db.get("tasks"):
            text = "কোনো টাস্ক নাই।"
        await q.edit_message_text(text, reply_markup=admin_menu())
    elif data == "back":
        await q.edit_message_text("👇 মেনু থেকে বেছে নাও:", reply_markup=main_menu(admin=admin))
    save_db(db)

async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user = update.effective_user
    u = get_user(db, user.id, user.username or "")
    text = update.message.text or ""
    args = text.split()
    admin = is_admin(user)
    if text.startswith("/admin"):
        if not admin:
            await update.message.reply_text("তুমি Admin না।")
            return
        pending_dep = len([d for d in db.get("deposits", {}).values() if d.get("status") == "pending"])
        pending_wd = len([w for w in db.get("withdraws", {}).values() if w.get("status") == "pending"])
        await update.message.reply_text(f"👨‍💻 Master Admin Panel\n\n👥 Total Users: {len(db.get('users', {}))}\n📋 Total Tasks: {len(db.get('tasks', {}))}\n📥 Pending Deposits: {pending_dep}\n💸 Pending Withdraws: {pending_wd}", reply_markup=admin_menu())
        return
    if text.startswith("/deposit"):
        if len(args) < 4:
            await update.message.reply_text("লিখো: `/deposit 50 TrxID Bkash`", parse_mode="Markdown"); return
        try:
            amt = int(args[1])
        except:
            await update.message.reply_text("টাকার পরিমাণ সংখ্যায় লিখো।"); return
        if amt < MIN_DEPOSIT:
            await update.message.reply_text(f"মিনিমাম {MIN_DEPOSIT} টাকা।"); return
        trx = args[2]; method = args[3]
        db["deposits"][f"{user.id}_{trx}"] = {"user": str(user.id), "amount": amt, "trx": trx, "method": method, "status": "pending"}
        save_db(db)
        await update.message.reply_text(f"✅ Deposit Request পাঠানো হইছে!\nAmount: {amt} টাকা\nTrxID: {trx}\nAdmin Approve করলেই যোগ হবে।")
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"📥 নতুন Deposit!\nUser: {user.id} (@{user.username})\nAmount: {amt} টাকা\nTrx: {trx}\nMethod: {method}\nApprove: /approve_deposit {user.id} {trx}")
        except:
            pass
    elif text.startswith("/approve_deposit"):
        if not admin:
            await update.message.reply_text("তুমি Admin না।"); return
        if len(args) < 3:
            await update.message.reply_text("লিখো: `/approve_deposit user_id trx`"); return
        key = f"{args[1]}_{args[2]}"
        d = db["deposits"].get(key)
        if not d:
            await update.message.reply_text("Deposit পাওয়া যায় নাই।"); return
        target = get_user(db, int(args[1]))
        target["deposit_balance"] += d["amount"]
        d["status"] = "approved"
        save_db(db)
        await update.message.reply_text(f"✅ Approved! {d['amount']} টাকা যোগ হইছে।")
        try:
            await context.bot.send_message(chat_id=int(args[1]), text=f"✅ তোমার {d['amount']} টাকা Deposit Approve হইছে!")
        except:
            pass
    elif text.startswith("/withdraw"):
        if len(args) < 4:
            await update.message.reply_text("লিখো: `/withdraw 100 Bkash 014...`"); return
        try:
            amt = int(args[1])
        except:
            await update.message.reply_text("টাকা সংখ্যায় লিখো।"); return
        if amt < MIN_WITHDRAW:
            await update.message.reply_text(f"মিনিমাম {MIN_WITHDRAW} টাকা।"); return
        if u["balance"] < amt:
            await update.message.reply_text("Balance যথেষ্ট নাই।"); return
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
        if u["deposit_balance"] < cost and not admin:
            await update.message.reply_text(f"❌ Deposit Balance যথেষ্ট নাই। লাগবে {cost} টাকা, আছে {u['deposit_balance']} টাকা।"); return
        db["task_counter"] += 1
        tid = str(db["task_counter"])
        db["tasks"][tid] = {"id": tid, "owner": str(user.id), "type": typ, "title": title, "link": link, "total": count, "left": count, "active": True, "done_by": []}
        save_db(db)
        await update.message.reply_text(f"✅ Task অ্যাড হইছে!\nID: {tid}\n{title}\nTotal: {count} জন")
    elif text.startswith("/proof"):
        if len(args) < 2:
            await update.message.reply_text("লিখো: `/proof task_id` তারপর Screenshot পাঠাও।"); return
        context.user_data["proof_task"] = args[1]
        await update.message.reply_text("এখন Screenshot টা পাঠাও। বট নিজেই Auto Approve করবে।")
    elif text.startswith("/approve_task"):
        if not admin:
            await update.message.reply_text("এখন Auto Approve চালু আছে।"); return
        await update.message.reply_text("এখন Auto Approve চালু আছে, হাতে Approve লাগে না। ইউজার ছবি দিলেই টাকা পেয়ে যাবে।")
    save_db(db)

# ===== AUTO APPROVE =====
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = context.user_data.get("proof_task")
    if not tid:
        await update.message.reply_text("আগে `/proof task_id` লিখো, তারপর Screenshot পাঠাও।")
        return
    user = update.effective_user
    db = load_db()
    t = db.get("tasks", {}).get(str(tid))
    worker = get_user(db, user.id, user.username or "")
    if not t:
        await update.message.reply_text("❌ এই Task ID দিয়ে কোনো টাস্ক নাই।")
        context.user_data["proof_task"] = None
        return
    if str(user.id) in t.get("done_by", []):
        await update.message.reply_text("❌ তুমি এই টাস্কের টাকা আগেই নিয়ে নিছো।")
        context.user_data["proof_task"] = None
        return
    if t.get("left", 0) <= 0 or not t.get("active"):
        await update.message.reply_text("❌ এই টাস্ক শেষ হয়ে গেছে।")
        context.user_data["proof_task"] = None
        return
    worker["balance"] += WORKER_REWARD
    worker["total_earn"] += WORKER_REWARD
    worker["done_tasks"].append(str(tid))
    t["done_by"].append(str(user.id))
    t["left"] -= 1
    owner = db["users"].get(t["owner"])
    if owner:
        owner["deposit_balance"] -= ADVERTISER_COST
    if t["left"] <= 0:
        t["active"] = False
    save_db(db)
    await update.message.reply_text(f"✅ Auto Approve হইছে!\n\n🎉 তুমি {WORKER_REWARD} টাকা পাইছো!\n💰 নতুন Balance: {worker['balance']} টাকা")
    try:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=f"✅ Auto Approved!\n\nTask: {tid} | {t['title']}\nUser: {user.id} (@{user.username})\nReward: {WORKER_REWARD} টাকা দেওয়া হইছে।\nবাকি: {t['left']}/{t['total']}")
    except Exception as e:
        print(f"Auto proof notify error: {e}")
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
