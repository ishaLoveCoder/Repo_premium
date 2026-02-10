# bot.py

import time
import asyncio
import datetime
import pytz

from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    CallbackQuery,
    PreCheckoutQuery
)

from info import (
    API_ID, API_HASH, BOT_TOKEN,
    CHANNEL_ID, CHANNEL_NAME,
    ADMINS, PREMIUM_LOGS,
    STAR_PREMIUM_PLANS,
    INVITE_LINK_VALID_SECONDS,
    INVITE_LINK_MEMBER_LIMIT
)

from db import db
from utils import get_seconds


IST = pytz.timezone("Asia/Kolkata")


app = Client(
    "star_premium_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# =========================================
# /start
# =========================================
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    user = message.from_user

    plans_btn = []
    for stars, t in STAR_PREMIUM_PLANS.items():
        plans_btn.append([InlineKeyboardButton(f"⭐ {stars} Stars = {t}", callback_data=f"buy_{stars}")])

    buttons = [
        [InlineKeyboardButton(f"📢 {CHANNEL_NAME}", url="https://t.me/+placeholder")],
        [InlineKeyboardButton("⭐ Buy Premium", callback_data="open_plans")],
        [InlineKeyboardButton("📦 My Plan", callback_data="myplan_btn")]
    ]

    await message.reply_text(
        f"Hey {user.mention} 👋\n\n"
        f"Welcome to **{CHANNEL_NAME} Premium Bot** ⭐\n\n"
        f"👇 Choose an option:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# =========================================
# Open plans
# =========================================
@app.on_callback_query(filters.regex("open_plans"))
async def open_plans(client, cq: CallbackQuery):
    plans_btn = []
    for stars, t in STAR_PREMIUM_PLANS.items():
        plans_btn.append([InlineKeyboardButton(f"⭐ {stars} Stars = {t}", callback_data=f"buy_{stars}")])

    plans_btn.append([InlineKeyboardButton("❌ Close", callback_data="close")])

    await cq.message.edit_text(
        f"⭐ **Premium Plans for {CHANNEL_NAME}**\n\nChoose your plan:",
        reply_markup=InlineKeyboardMarkup(plans_btn)
    )


@app.on_callback_query(filters.regex("close"))
async def close_menu(client, cq: CallbackQuery):
    await cq.message.delete()


# =========================================
# My Plan (button)
# =========================================
@app.on_callback_query(filters.regex("myplan_btn"))
async def myplan_button(client, cq: CallbackQuery):
    fake = type("obj", (), {})()
    fake.from_user = cq.from_user
    fake.reply_text = cq.message.reply_text
    await myplan_cmd(client, fake)
    await cq.answer()


# =========================================
# /myplan
# =========================================
@app.on_message(filters.command("myplan"))
async def myplan_cmd(client, message):
    user_id = message.from_user.id
    data = await db.get_user(user_id)

    if not data or not data.get("expiry_time"):
        return await message.reply_text(
            "❌ You don't have any active premium.\n\nClick ⭐ Buy Premium to purchase."
        )

    expiry = data["expiry_time"]
    now = datetime.datetime.now(datetime.timezone.utc)

    if expiry < now:
        return await message.reply_text("⚠️ Your premium is expired. Please renew.")

    expiry_ist = expiry.astimezone(IST)
    expiry_str = expiry_ist.strftime("%d-%m-%Y | %I:%M:%S %p")

    left = expiry_ist - datetime.datetime.now(IST)
    days = left.days
    hours, rem = divmod(left.seconds, 3600)
    mins, _ = divmod(rem, 60)

    await message.reply_text(
        f"✅ **Premium Active**\n\n"
        f"👤 User: {message.from_user.mention}\n"
        f"🆔 ID: `{user_id}`\n\n"
        f"⏳ Time Left: {days} days, {hours} hours, {mins} mins\n"
        f"⌛ Expiry: {expiry_str}"
    )


# =========================================
# 1) BUY BUTTON → INVOICE
# =========================================
@app.on_callback_query(filters.regex(r"buy_\d+"))
async def buy_handler(client, cq: CallbackQuery):
    try:
        amount = int(cq.data.split("_")[1])

        if amount not in STAR_PREMIUM_PLANS:
            return await cq.answer("⚠️ Invalid plan", show_alert=True)

        plan_time = STAR_PREMIUM_PLANS[amount]

        buttons = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_invoice")]]
        reply_markup = InlineKeyboardMarkup(buttons)

        await client.send_invoice(
            chat_id=cq.message.chat.id,
            title=f"{CHANNEL_NAME} Premium ⭐",
            description=f"Pay {amount} Stars and get Premium for {plan_time}",
            payload=f"premium_star_{amount}",
            currency="XTR",
            prices=[LabeledPrice(label="Premium", amount=amount)],
            reply_markup=reply_markup
        )

        await cq.answer()

    except Exception as e:
        await cq.answer("🚫 Error creating invoice", show_alert=True)
        print("Invoice Error:", e)


@app.on_callback_query(filters.regex("cancel_invoice"))
async def cancel_invoice(client, cq: CallbackQuery):
    try:
        await cq.message.delete()
    except:
        pass


# =========================================
# 2) PRE CHECKOUT
# =========================================
@app.on_pre_checkout_query()
async def pre_checkout(client, query: PreCheckoutQuery):
    if query.payload.startswith("premium_star_"):
        await query.answer(success=True)
    else:
        await query.answer(success=False, error_message="Invalid payment payload")


# =========================================
# 3) SUCCESSFUL PAYMENT
# =========================================
@app.on_message(filters.successful_payment)
async def success_payment(client, message):
    try:
        amount = int(message.successful_payment.total_amount)
        user_id = message.from_user.id

        if amount not in STAR_PREMIUM_PLANS:
            return await message.reply_text("⚠️ Invalid premium plan.")

        plan_time = STAR_PREMIUM_PLANS[amount]
        seconds = await get_seconds(plan_time)

        if seconds <= 0:
            return await message.reply_text("⚠️ Plan time config invalid.")

        # expiry time in UTC
        expiry_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
        await db.set_premium(user_id, expiry_time)

        # Create 1 hour single-use invite link
        invite = await client.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=INVITE_LINK_MEMBER_LIMIT,
            expire_date=int(time.time()) + INVITE_LINK_VALID_SECONDS
        )

        expiry_str = expiry_time.astimezone(IST).strftime("%d-%m-%Y | %I:%M:%S %p")

        await message.reply_text(
            f"✅ Payment Successful ⭐\n\n"
            f"⭐ Stars Paid: {amount}\n"
            f"📦 Plan: {plan_time}\n"
            f"⌛ Premium Expiry: {expiry_str}\n\n"
            f"🔗 **Your Private Join Link (Valid 1 hour, single-use):**\n"
            f"{invite.invite_link}\n\n"
            f"⚠️ Don't share this link with anyone!"
        )

        # logs
        try:
            await client.send_message(
                PREMIUM_LOGS,
                f"#STAR_PREMIUM\n\n"
                f"👤 {message.from_user.mention}\n"
                f"🆔 <code>{user_id}</code>\n"
                f"⭐ Paid: {amount}\n"
                f"📦 Plan: {plan_time}\n"
                f"⌛ Expiry: {expiry_str}\n"
                f"🔗 Invite: {invite.invite_link}"
            )
        except:
            pass

    except Exception as e:
        print("Payment success error:", e)
        await message.reply_text("✅ Payment received but error occurred. Contact admin.")


# =========================================
# Admin: set mode
# /set_mode remove
# /set_mode remind
# /set_mode both
# =========================================
@app.on_message(filters.command("set_mode") & filters.user(ADMINS))
async def set_mode_cmd(client, message):
    if len(message.command) != 2:
        return await message.reply_text("Usage: /set_mode remove | remind | both")

    mode = message.command[1].lower()

    if mode == "remove":
        await db.set_mode(auto_remove=True, remind=False)
        return await message.reply_text("✅ Mode set: AUTO_REMOVE_ON_EXPIRE = True, REMINDER = False")

    if mode == "remind":
        await db.set_mode(auto_remove=False, remind=True)
        return await message.reply_text("✅ Mode set: AUTO_REMOVE_ON_EXPIRE = False, REMINDER = True")

    if mode == "both":
        await db.set_mode(auto_remove=True, remind=True)
        return await message.reply_text("✅ Mode set: AUTO_REMOVE_ON_EXPIRE = True, REMINDER = True")

    await message.reply_text("Invalid mode. Use remove/remind/both")


# =========================================
# Expiry Checker Loop
# =========================================
async def expiry_checker():
    while True:
        try:
            mode = await db.get_mode()
            auto_remove = mode.get("auto_remove", True)
            remind = mode.get("remind", False)

            now = datetime.datetime.now(datetime.timezone.utc)

            async for user in db.get_all_users():
                user_id = user["_id"]
                expiry = user.get("expiry_time")

                if not expiry:
                    continue

                if expiry < now:
                    # expired
                    if auto_remove:
                        try:
                            # kick
                            await app.ban_chat_member(CHANNEL_ID, user_id)
                            await app.unban_chat_member(CHANNEL_ID, user_id)
                        except:
                            pass

                        try:
                            await app.send_message(
                                user_id,
                                f"⚠️ Your premium is expired.\n\n"
                                f"You have been removed from {CHANNEL_NAME}.\n"
                                f"Use /start to renew ⭐"
                            )
                        except:
                            pass

                        await db.remove_premium(user_id)

                    elif remind:
                        # remind every 24 hours (simple method)
                        # store last_remind
                        last_remind = user.get("last_remind")
                        if not last_remind or (now - last_remind).total_seconds() > 86400:
                            try:
                                await app.send_message(
                                    user_id,
                                    f"⚠️ Your premium is expired.\n\n"
                                    f"Renew to continue access: /start ⭐"
                                )
                            except:
                                pass

                            await db.users.update_one(
                                {"_id": user_id},
                                {"$set": {"last_remind": now}},
                                upsert=True
                            )

        except Exception as e:
            print("Expiry loop error:", e)

        await asyncio.sleep(600)  # check every 10 minutes


# =========================================
# Start bot
# =========================================
async def main():
    await app.start()
    print("✅ Bot started...")
    asyncio.create_task(expiry_checker())
    await asyncio.Event().wait()


if __name__ == "__main__":
    app.run(main())
