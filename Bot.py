```python
import sqlite3
import re
import logging
from datetime import datetime, timedelta, time
import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler, JobQueue
import telegram.error

# تنظیمات اولیه
BOT_TOKEN = os.getenv("BOT_TOKEN", "7996022698:AAG65GXEjbDbgMGFVT9ExeGFmkvj0UDqbXE")
CHANNEL_ID = "-1001197183322"
OPERATOR_GROUP_ID = "-1002574996302"
ADMIN_IDS = {5701423397, 158893761}  # مجموعه برای دسترسی سریع‌تر
DATABASE_PATH = "chemeng_bot.db"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

CHECK_CHANNEL, PROFILE_NAME, PROFILE_NATIONAL_ID, PROFILE_STUDENT_ID, PROFILE_CONTACT, EVENT_SELECTION, REGISTRATION, SEND_MESSAGE, ADD_EVENT_TYPE, ADD_EVENT_TITLE, ADD_EVENT_DESCRIPTION, ADD_EVENT_DATE, ADD_EVENT_LOCATION, ADD_EVENT_CAPACITY, SEND_ADMIN_MESSAGE, SUPPORT_MESSAGE, ADD_EVENT_COST, REPORTS, MANUAL_REGISTRATION_EVENT, MANUAL_REGISTRATION_STUDENT_ID, MANUAL_REGISTRATION_CONFIRM, PAYMENT_RECEIPT, EDIT_EVENT_TEXT = range(23)

def init_db():
    with sqlite3.connect(DATABASE_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY, full_name TEXT, national_id TEXT, student_id TEXT, phone TEXT, created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS events
                     (event_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, type TEXT, date TEXT, location TEXT, 
                      capacity INTEGER, current_capacity INTEGER, description TEXT, is_active INTEGER, hashtag TEXT, 
                      cost INTEGER, card_number TEXT, deactivation_reason TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS registrations
                     (registration_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, event_id INTEGER, registered_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS payments
                     (payment_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, event_id INTEGER, amount INTEGER, confirmed_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (user_id INTEGER PRIMARY KEY, added_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (message_id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, event_id INTEGER, message_text TEXT, sent_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS operator_messages
                     (message_id INTEGER PRIMARY KEY, chat_id INTEGER, user_id INTEGER, event_id INTEGER, 
                      message_type TEXT, sent_at TEXT)''')
        conn.commit()
        logger.info("Database initialized successfully")

def get_user_profile(user_id):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = c.fetchone()
            return user
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        return None

def get_event(event_id):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
            event = c.fetchone()
            return event
    except Exception as e:
        logger.error(f"Error fetching event: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    try:
        await context.bot.get_chat_member(CHANNEL_ID, user_id)
        user = get_user_profile(user_id)
        if user:
            await update.message.reply_text(
                f"{user['full_name']} عزیز، خوش آمدید! 😊\nلطفاً از منوی زیر گزینه موردنظر را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("مشاهده رویدادها 📅", callback_data="view_events")],
                    [InlineKeyboardButton("ویرایش پروفایل ✏️", callback_data="edit_profile"),
                     InlineKeyboardButton("پشتیبانی 📞", callback_data="support")],
                    [InlineKeyboardButton("سوالات متداول ❓", callback_data="faq")]
                ])
            )
            return EVENT_SELECTION
        else:
            await update.message.reply_text(
                f"{user_name} عزیز، لطفاً برای ثبت‌نام، نام و نام‌خانوادگی خود را وارد کنید:"
            )
            return PROFILE_NAME
    except telegram.error.TelegramError:
        await update.message.reply_text(
            f"{user_name} عزیز، لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}\nسپس دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("عضویت در کانال 📢", url=f"https://t.me/{CHANNEL_ID[1:]}")],
                [InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_channel")]
            ])
        )
        return CHECK_CHANNEL

async def check_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    try:
        await context.bot.get_chat_member(CHANNEL_ID, user_id)
        user = get_user_profile(user_id)
        if user:
            await query.message.reply_text(
                f"{user['full_name']} عزیز، خوش آمدید! 😊\nلطفاً از منوی زیر گزینه موردنظر را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("مشاهده رویدادها 📅", callback_data="view_events")],
                    [InlineKeyboardButton("ویرایش پروفایل ✏️", callback_data="edit_profile"),
                     InlineKeyboardButton("پشتیبانی 📞", callback_data="support")],
                    [InlineKeyboardButton("سوالات متداول ❓", callback_data="faq")]
                ])
            )
            return EVENT_SELECTION
        else:
            await query.message.reply_text(
                f"{user_name} عزیز، لطفاً برای ثبت‌نام، نام و نام‌خانوادگی خود را وارد کنید:"
            )
            return PROFILE_NAME
    except telegram.error.TelegramError:
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}\nسپس دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("عضویت در کانال 📢", url=f"https://t.me/{CHANNEL_ID[1:]}")],
                [InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_channel")]
            ])
        )
        return CHECK_CHANNEL

async def profile_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    full_name = update.message.text.strip()
    if not re.match(r"^[\u0600-\u06FF\s]+$", full_name):
        await update.message.reply_text(
            f"{user_name} عزیز،\nلطفاً نام و نام‌خانوادگی را فقط با حروف فارسی وارد کنید:"
        )
        return PROFILE_NAME
    context.user_data['full_name'] = full_name
    await update.message.reply_text(
        f"نام و نام‌خانوادگی: {full_name}\n"
        f"آیا این اطلاعات درست است؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("تأیید ✅", callback_data="confirm_name"),
             InlineKeyboardButton("ویرایش ✏️", callback_data="retry_name")]
        ])
    )
    return PROFILE_NAME

async def confirm_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    if query.data == "confirm_name":
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً کد ملی خود را وارد کنید (۱۰ رقم):"
        )
        return PROFILE_NATIONAL_ID
    else:
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً نام و نام‌خانوادگی خود را دوباره وارد کنید:"
        )
        return PROFILE_NAME

async def profile_national_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    national_id = update.message.text.strip()
    if not re.match(r"^\d{10}$", national_id):
        await update.message.reply_text(
            f"{user_name} عزیز،\nلطفاً کد ملی را به‌صورت ۱۰ رقم وارد کنید:"
        )
        return PROFILE_NATIONAL_ID
    context.user_data['national_id'] = national_id
    await update.message.reply_text(
        f"کد ملی: {national_id}\n"
        f"آیا این اطلاعات درست است؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("تأیید ✅", callback_data="confirm_national_id"),
             InlineKeyboardButton("ویرایش ✏️", callback_data="retry_national_id")]
        ])
    )
    return PROFILE_NATIONAL_ID

async def confirm_national_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    if query.data == "confirm_national_id":
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً شماره دانشجویی خود را وارد کنید:"
        )
        return PROFILE_STUDENT_ID
    else:
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً کد ملی خود را دوباره وارد کنید (۱۰ رقم):"
        )
        return PROFILE_NATIONAL_ID

async def profile_student_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    student_id = update.message.text.strip()
    if not re.match(r"^\d{8,10}$", student_id):
        await update.message.reply_text(
            f"{user_name} عزیز،\nلطفاً شماره دانشجویی را به‌صورت ۸ تا ۱۰ رقم وارد کنید:"
        )
        return PROFILE_STUDENT_ID
    context.user_data['student_id'] = student_id
    await update.message.reply_text(
        f"شماره دانشجویی: {student_id}\n"
        f"آیا این اطلاعات درست است؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("تأیید ✅", callback_data="confirm_student_id"),
             InlineKeyboardButton("ویرایش ✏️", callback_data="retry_student_id")]
        ])
    )
    return PROFILE_STUDENT_ID

async def confirm_student_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    if query.data == "confirm_student_id":
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً شماره تماس خود را وارد کنید یا دکمه زیر را فشار دهید:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("ارسال شماره تماس 📱", request_contact=True)]],
                one_time_keyboard=True, resize_keyboard=True
            )
        )
        return PROFILE_CONTACT
    else:
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً شماره دانشجویی خود را دوباره وارد کنید:"
        )
        return PROFILE_STUDENT_ID

async def profile_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()
        if not re.match(r"^\+?98\d{9}$|^0\d{10}$", phone):
            await update.message.reply_text(
                f"{user_name} عزیز،\nلطفاً شماره تماس را به‌صورت معتبر وارد کنید (مثل 09123456789 یا +989123456789):"
            )
            return PROFILE_CONTACT
    context.user_data['phone'] = phone
    full_name = context.user_data.get('full_name')
    national_id = context.user_data.get('national_id')
    student_id = context.user_data.get('student_id')
    await update.message.reply_text(
        f"{user_name} عزیز، لطفاً اطلاعات زیر را بررسی کنید:\n"
        f"نام و نام‌خانوادگی: {full_name}\n"
        f"کد ملی: {national_id}\n"
        f"شماره دانشجویی: {student_id}\n"
        f"شماره تماس: {phone}\n"
        f"آیا این اطلاعات درست است؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("تأیید ✅", callback_data="confirm_all"),
             InlineKeyboardButton("ویرایش ✏️", callback_data="retry_all")]
        ])
    )
    return PROFILE_CONTACT

async def confirm_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    if query.data == "confirm_all":
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO users (user_id, full_name, national_id, student_id, phone, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, context.user_data['full_name'], context.user_data['national_id'],
                     context.user_data['student_id'], context.user_data['phone'],
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
            await query.message.reply_text(
                f"{user_name} عزیز، ثبت‌نام شما با موفقیت انجام شد! 🎉\n"
                f"لطفاً از منوی زیر گزینه موردنظر را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("مشاهده رویدادها 📅", callback_data="view_events")],
                    [InlineKeyboardButton("ویرایش پروفایل ✏️", callback_data="edit_profile"),
                     InlineKeyboardButton("پشتیبانی 📞", callback_data="support")],
                    [InlineKeyboardButton("سوالات متداول ❓", callback_data="faq")]
                ]),
                reply_to_message_id=None
            )
            context.user_data.clear()
            admin_buttons = []
            with sqlite3.connect(DATABASE_PATH) as conn:
                c = conn.cursor()
                if user_id in ADMIN_IDS:
                    admin_buttons = [
                        [InlineKeyboardButton("افزودن رویداد ➕", callback_data="add_event"),
                         InlineKeyboardButton("ویرایش رویداد ✏️", callback_data="edit_event")],
                        [InlineKeyboardButton("فعال/غیرفعال کردن رویداد 🔄", callback_data="toggle_event"),
                         InlineKeyboardButton("مدیریت ادمین‌ها 👤", callback_data="manage_admins")],
                        [InlineKeyboardButton("ارسال پیام ادمین 📩", callback_data="admin_message"),
                         InlineKeyboardButton("گزارش‌ها 📊", callback_data="reports")],
                        [InlineKeyboardButton("ثبت‌نام دستی ✍️", callback_data="manual_registration")]
                    ]
                elif c.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,)).fetchone():
                    admin_buttons = [
                        [InlineKeyboardButton("ارسال پیام ادمین 📩", callback_data="admin_message"),
                         InlineKeyboardButton("گزارش‌ها 📊", callback_data="reports")],
                        [InlineKeyboardButton("ثبت‌نام دستی ✍️", callback_data="manual_registration")]
                    ]
            if admin_buttons:
                await query.message.reply_text(
                    f"{user_name} عزیز، گزینه‌های مدیریت:",
                    reply_markup=InlineKeyboardMarkup(admin_buttons)
                )
            return EVENT_SELECTION
        except Exception as e:
            logger.error(f"Error saving user profile: {e}")
            await query.message.reply_text(
                f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
            )
            return PROFILE_CONTACT
    else:
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً نام و نام‌خانوادگی خود را دوباره وارد کنید:"
        )
        context.user_data.clear()
        return PROFILE_NAME

async def view_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM events WHERE is_active = 1 ORDER BY date")
            events = c.fetchall()
        if not events:
            await query.message.reply_text(
                f"{user_name} عزیز،\nدر حال حاضر رویداد فعالی وجود ندارد. 📪"
            )
            return EVENT_SELECTION
        buttons = []
        for event in events:
            buttons.append([InlineKeyboardButton(
                f"{event['type']} {event['title']} - {event['date']}",
                callback_data=f"event_{event['event_id']}"
            )])
        buttons.append([InlineKeyboardButton("بازگشت ↩️", callback_data="main_menu")])
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً رویداد موردنظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return EVENT_SELECTION
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def event_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        event_id = int(query.data.split("_")[1])
        event = get_event(event_id)
        if not event or not event['is_active']:
            await query.message.reply_text(
                f"{user_name} عزیز،\nاین رویداد دیگر در دسترس نیست. 📪"
            )
            return EVENT_SELECTION
        cost_text = f"هزینه: {event['cost']} تومان\n" if event['cost'] > 0 else "هزینه: رایگان\n"
        await query.message.reply_text(
            f"{user_name} عزیز، جزئیات رویداد:\n\n"
            f"#{event['type']} {event['hashtag']}\n"
            f"عنوان: {event['title']}\n"
            f"نوع: {event['type']}\n"
            f"تاریخ: {event['date']}\n"
            f"محل: {event['location']}\n"
            f"ظرفیت: {event['current_capacity']}/{event['capacity']}\n"
            f"{cost_text}"
            f"توضیحات: {event['description']}\n\n"
            f"آیا می‌خواهید برای این رویداد ثبت‌نام کنید؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ثبت‌نام 📝", callback_data=f"register_{event_id}")],
                [InlineKeyboardButton("بازگشت ↩️", callback_data="view_events")]
            ])
        )
        return REGISTRATION
    except Exception as e:
        logger.error(f"Error fetching event details: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def check_channel_register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return await event_details(update, context)
    except telegram.error.TelegramError:
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}\nسپس دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("عضویت در کانال 📢", url=f"https://t.me/{CHANNEL_ID[1:]}")],
                [InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_channel_register")]
            ])
        )
        return REGISTRATION

async def register_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        event_id = int(query.data.split("_")[1])
        event = get_event(event_id)
        if not event or not event['is_active']:
            await query.message.reply_text(
                f"{user_name} عزیز،\nاین رویداد دیگر در دسترس نیست. 📪"
            )
            return EVENT_SELECTION
        if event['current_capacity'] >= event['capacity']:
            await query.message.reply_text(
                f"{user_name} عزیز،\nظرفیت این رویداد تکمیل شده است. 🚫"
            )
            return EVENT_SELECTION
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM registrations WHERE user_id = ? AND event_id = ?", (user_id, event_id))
            if c.fetchone():
                await query.message.reply_text(
                    f"{user_name} عزیز،\nشما قبلاً برای این رویداد ثبت‌نام کرده‌اید! ✅"
                )
                return EVENT_SELECTION
            c.execute(
                "INSERT INTO registrations (user_id, event_id, registered_at) VALUES (?, ?, ?)",
                (user_id, event_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            c.execute("UPDATE events SET current_capacity = current_capacity + 1 WHERE event_id = ?", (event_id,))
            c.execute("SELECT COUNT(*) FROM registrations WHERE event_id = ?", (event_id,))
            registration_count = c.fetchone()[0]
            conn.commit()
        user = get_user_profile(user_id)
        message_to_operators = (
            f"#{event['type']} {event['hashtag']}\n"
            f"{registration_count}.\n"
            f"نام: {user['full_name']}\n"
            f"کد ملی: {user['national_id']}\n"
            f"شماره دانشجویی: {user['student_id']}\n"
            f"شماره تماس: {user['phone']}"
        )
        sent_message = await context.bot.send_message(chat_id=OPERATOR_GROUP_ID, text=message_to_operators)
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO operator_messages (message_id, chat_id, user_id, event_id, message_type, sent_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (sent_message.message_id, OPERATOR_GROUP_ID, user_id, event_id, "registration", 
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
        if event['cost'] > 0:
            await query.message.reply_text(
                f"{user_name} عزیز،\n"
                f"لطفاً مبلغ {event['cost']} تومان را به شماره کارت زیر واریز کنید و تصویر رسید را ارسال کنید:\n"
                f"{event['card_number']}"
            )
            context.user_data['event_id'] = event_id
            return PAYMENT_RECEIPT
        else:
            await query.message.reply_text(
                f"{user_name} عزیز،\nثبت‌نام شما در {event['type']} {event['title']} با موفقیت انجام شد! ✅"
            )
            return EVENT_SELECTION
    except telegram.error.TelegramError as e:
        logger.error(f"Error registering event: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
    except Exception as e:
        logger.error(f"Error in register_event: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
    return EVENT_SELECTION

async def payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    event_id = context.user_data.get('event_id')

    if not update.message.photo:
        await update.message.reply_text(
            f"{user_name} عزیز،\n"
            f"لطفاً فقط تصویر رسید پرداخت را ارسال کنید."
        )
        return PAYMENT_RECEIPT

    event = get_event(event_id)
    if not event:
        await update.message.reply_text(
            f"{user_name} عزیز،\n"
            f"این رویداد دیگر در دسترس نیست. 📪"
        )
        return EVENT_SELECTION

    user = get_user_profile(user_id)
    message_to_operators = (
        f"#{event['type']} {event['hashtag']}\n"
        f"نام: {user['full_name']}\n"
        f"کد ملی: {user['national_id']}\n"
        f"شماره دانشجویی: {user['student_id']}\n"
        f"شماره تماس: {user['phone']}\n"
        f"مبلغ: {event['cost']} تومان"
    )

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            sent_message = await context.bot.send_message(
                chat_id=OPERATOR_GROUP_ID,
                text=message_to_operators,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("تأیید ✅", callback_data=f"confirm_payment_{user_id}_{event_id}")],
                    [
                        InlineKeyboardButton("ناخوانا 🚫", callback_data=f"unreadable_payment_{user_id}_{event_id}"),
                        InlineKeyboardButton("ابطال ❎", callback_data=f"reject_payment_{user_id}_{event_id}")
                    ]
                ])
            )
            c.execute(
                "INSERT INTO operator_messages (message_id, chat_id, user_id, event_id, message_type, sent_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (sent_message.message_id, OPERATOR_GROUP_ID, user_id, event_id, "payment", 
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            await context.bot.forward_message(
                chat_id=OPERATOR_GROUP_ID,
                from_chat_id=user_id,
                message_id=update.message.message_id
            )
            conn.commit()
        await update.message.reply_text(
            f"{user_name} عزیز،\n"
            f"رسید شما ارسال شد و در انتظار تأیید ادمین است. به‌زودی اطلاع‌رسانی می‌شود. ✅"
        )
    except telegram.error.TelegramError as e:
        logger.error(f"Error sending payment receipt: {e}")
        await update.message.reply_text(
            f"{user_name} عزیز،\n"
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
    except Exception as e:
        logger.error(f"Error in payment_receipt: {e}")
        await update.message.reply_text(
            f"{user_name} عزیز،\n"
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
    return EVENT_SELECTION

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    admin_id = update.effective_user.id
    admin_name = get_user_profile(admin_id)['full_name'] if get_user_profile(admin_id) else update.effective_user.first_name

    if admin_id not in ADMIN_IDS:
        await query.message.reply_text(
            f"{admin_name} عزیز،\n"
            f"فقط ادمین‌های اصلی می‌توانند این عملیات را انجام دهند! 🚫"
        )
        return EVENT_SELECTION

    try:
        _, user_id, event_id = query.data.split("_")[1:]
        user_id = int(user_id)
        event_id = int(event_id)
    except ValueError as e:
        logger.error(f"Error parsing payment confirmation data: {e}")
        await query.message.reply_text(
            f"{admin_name} عزیز،\n"
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

    event = get_event(event_id)
    user = get_user_profile(user_id)
    if not event or not user:
        await query.message.reply_text(
            f"{admin_name} عزیز،\n"
            f"رویداد یا کاربر یافت نشد! 📪"
        )
        return EVENT_SELECTION

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO payments (user_id, event_id, amount, confirmed_at) VALUES (?, ?, ?, ?)",
                (user_id, event_id, event['cost'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
        await query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("تأیید ✅", callback_data="no_action")]
            ])
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=f"{user['full_name']} عزیز،\nپرداخت شما تأیید شد و ثبت‌نام شما در {event['type']} {event['title']} تکمیل شد! ✅"
        )
        await query.message.reply_text(
            f"{admin_name} عزیز،\nپرداخت برای {user['full_name']} تأیید شد! ✅"
        )
    except telegram.error.TelegramError as e:
        logger.error(f"Error confirming payment: {e}")
        await query.message.reply_text(
            f"{admin_name} عزیز،\nخطایی رخ داد. ممکن است پیام قدیمی باشد. 🚫"
        )
    except Exception as e:
        logger.error(f"Error in confirm_payment: {e}")
        await query.message.reply_text(
            f"{admin_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
    return EVENT_SELECTION

async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    admin_id = update.effective_user.id
    admin_name = get_user_profile(admin_id)['full_name'] if get_user_profile(admin_id) else update.effective_user.first_name

    if admin_id not in ADMIN_IDS:
        await query.message.reply_text(
            f"{admin_name} عزیز،\n"
            f"فقط ادمین‌های اصلی می‌توانند این عملیات را انجام دهند! 🚫"
        )
        return EVENT_SELECTION

    try:
        _, user_id, event_id = query.data.split("_")[1:]
        user_id = int(user_id)
        event_id = int(event_id)
    except ValueError as e:
        logger.error(f"Error parsing payment rejection data: {e}")
        await query.message.reply_text(
            f"{admin_name} عزیز،\n"
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

    event = get_event(event_id)
    user = get_user_profile(user_id)
    if not event or not user:
        await query.message.reply_text(
            f"{admin_name} عزیز،\n"
            f"رویداد یا کاربر یافت نشد! 📪"
        )
        return EVENT_SELECTION

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM registrations WHERE user_id = ? AND event_id = ?", (user_id, event_id))
            c.execute("UPDATE events SET current_capacity = current_capacity - 1 WHERE event_id = ?", (event_id,))
            conn.commit()
        await query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ابطال ❎", callback_data="no_action")]
            ])
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=f"{user['full_name']} عزیز،\nپرداخت شما تأیید نشد. لطفاً رسید را بررسی کنید یا عملیات پرداخت را دوباره انجام دهید."
        )
        await query.message.reply_text(
            f"{admin_name} عزیز،\nپرداخت برای {user['full_name']} رد شد و ثبت‌نام لغو شد. 🚫"
        )
    except telegram.error.TelegramError as e:
        logger.error(f"Error rejecting payment: {e}")
        await query.message.reply_text(
            f"{admin_name} عزیز،\nخطایی رخ داد. ممکن است پیام قدیمی باشد. 🚫"
        )
    except Exception as e:
        logger.error(f"Error in reject_payment: {e}")
        await query.message.reply_text(
            f"{admin_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
    return EVENT_SELECTION

async def unreadable_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    admin_id = update.effective_user.id
    admin_name = get_user_profile(admin_id)['full_name'] if get_user_profile(admin_id) else update.effective_user.first_name

    if admin_id not in ADMIN_IDS:
        await query.message.reply_text(
            f"{admin_name} عزیز،\n"
            f"فقط ادمین‌های اصلی می‌توانند این عملیات را انجام دهند! 🚫"
        )
        return EVENT_SELECTION

    try:
        _, user_id, event_id = query.data.split("_")[1:]
        user_id = int(user_id)
        event_id = int(event_id)
    except ValueError as e:
        logger.error(f"Error parsing unreadable payment data: {e}")
        await query.message.reply_text(
            f"{admin_name} عزیز،\n"
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

    event = get_event(event_id)
    user = get_user_profile(user_id)
    if not event or not user:
        await query.message.reply_text(
            f"{admin_name} عزیز،\n"
            f"رویداد یا کاربر یافت نشد! 📪"
        )
        return EVENT_SELECTION

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM registrations WHERE user_id = ? AND event_id = ?", (user_id, event_id))
            c.execute("UPDATE events SET current_capacity = current_capacity - 1 WHERE event_id = ?", (event_id,))
            conn.commit()
        await query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ناخوانا 🚫", callback_data="no_action")]
            ])
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=f"{user['full_name']} عزیز،\nرسید تراکنش شما ناخوانا یا غیرقابل بررسی بود. لطفا رسید تراکنش تون رو دوباره آپلود کنید."
        )
        await query.message.reply_text(
            f"{admin_name} عزیز،\nرسید برای {user['full_name']} به دلیل ناخوانا بودن رد شد و ثبت‌نام لغو شد. 🚫"
        )
    except telegram.error.TelegramError as e:
        logger.error(f"Error marking payment as unreadable: {e}")
        await query.message.reply_text(
            f"{admin_name} عزیز،\nخطایی رخ داد. ممکن است پیام قدیمی باشد. 🚫"
        )
    except Exception as e:
        logger.error(f"Error in unreadable_payment: {e}")
        await query.message.reply_text(
            f"{admin_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
    return EVENT_SELECTION

async def cleanup_old_messages(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            cutoff_time = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("SELECT message_id, chat_id FROM operator_messages WHERE sent_at < ?", (cutoff_time,))
            messages = c.fetchall()
            for message_id, chat_id in messages:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                except telegram.error.TelegramError as e:
                    logger.warning(f"Could not delete message {message_id}: {e}")
            c.execute("DELETE FROM operator_messages WHERE sent_at < ?", (cutoff_time,))
            deleted_count = c.rowcount
            conn.commit()
            logger.info(f"Cleaned up {deleted_count} old messages from operator_messages")
    except Exception as e:
        logger.error(f"Error cleaning up old messages: {e}")

async def no_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    await query.message.reply_text(
        f"{user_name} عزیز، لطفاً نام و نام‌خانوادگی جدید را وارد کنید:"
    )
    return PROFILE_NAME

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    await query.message.reply_text(
        f"{user_name} عزیز، لطفاً پیام خود را برای پشتیبانی وارد کنید:"
    )
    return SUPPORT_MESSAGE

async def support_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    message_text = update.message.text.strip()
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            sent_message = await context.bot.send_message(
                chat_id=OPERATOR_GROUP_ID,
                text=f"پیام پشتیبانی از {user_name}:\n{message_text}"
            )
            c.execute(
                "INSERT INTO operator_messages (message_id, chat_id, user_id, event_id, message_type, sent_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (sent_message.message_id, OPERATOR_GROUP_ID, user_id, None, "support", 
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
        await update.message.reply_text(
            f"{user_name} عزیز،\nپیام شما به پشتیبانی ارسال شد. به‌زودی پاسخ داده خواهد شد. ✅"
        )
    except telegram.error.TelegramError as e:
        logger.error(f"Error sending support message: {e}")
        await update.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
    except Exception as e:
        logger.error(f"Error in support_message: {e}")
        await update.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
    return EVENT_SELECTION

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    await query.message.reply_text(
        f"{user_name} عزیز، سؤالات متداول:\n\n"
        f"۱. چگونه می‌توانم در رویدادها ثبت‌نام کنم؟\n"
        f"از منوی اصلی گزینه 'مشاهده رویدادها' را انتخاب کنید و رویداد موردنظر را برگزینید.\n\n"
        f"۲. آیا می‌توانم پروفایل خود را ویرایش کنم؟\n"
        f"بله، از منوی اصلی گزینه 'ویرایش پروفایل' را انتخاب کنید.\n\n"
        f"۳. برای پشتیبانی چه کنم؟\n"
        f"از منوی اصلی گزینه 'پشتیبانی' را انتخاب کنید و پیام خود را ارسال کنید.\n\n"
        f"برای اطلاعات بیشتر، با پشتیبانی تماس بگیرید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بازگشت ↩️", callback_data="main_menu")]
        ])
    )
    return EVENT_SELECTION

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            await query.message.reply_text(
                f"{user_name} عزیز، خوش آمدید! 😊\nلطفاً از منوی زیر گزینه موردنظر را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("مشاهده رویدادها 📅", callback_data="view_events")],
                    [InlineKeyboardButton("ویرایش پروفایل ✏️", callback_data="edit_profile"),
                     InlineKeyboardButton("پشتیبانی 📞", callback_data="support")],
                    [InlineKeyboardButton("سوالات متداول ❓", callback_data="faq")]
                ])
            )
            admin_buttons = []
            if user_id in ADMIN_IDS:
                admin_buttons = [
                    [InlineKeyboardButton("افزودن رویداد ➕", callback_data="add_event"),
                     InlineKeyboardButton("ویرایش رویداد ✏️", callback_data="edit_event")],
                    [InlineKeyboardButton("فعال/غیرفعال کردن رویداد 🔄", callback_data="toggle_event"),
                     InlineKeyboardButton("مدیریت ادمین‌ها 👤", callback_data="manage_admins")],
                    [InlineKeyboardButton("ارسال پیام ادمین 📩", callback_data="admin_message"),
                     InlineKeyboardButton("گزارش‌ها 📊", callback_data="reports")],
                    [InlineKeyboardButton("ثبت‌نام دستی ✍️", callback_data="manual_registration")]
                ]
            elif c.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,)).fetchone():
                admin_buttons = [
                    [InlineKeyboardButton("ارسال پیام ادمین 📩", callback_data="admin_message"),
                     InlineKeyboardButton("گزارش‌ها 📊", callback_data="reports")],
                    [InlineKeyboardButton("ثبت‌نام دستی ✍️", callback_data="manual_registration")]
                ]
            if admin_buttons:
                await query.message.reply_text(
                    f"{user_name} عزیز، گزینه‌های مدیریت:",
                    reply_markup=InlineKeyboardMarkup(admin_buttons)
                )
            return EVENT_SELECTION
    except Exception as e:
        logger.error(f"Error in main_menu: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def add_event_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    if user_id not in ADMIN_IDS:
        await query.message.reply_text(
            f"{user_name} عزیز،\nشما دسترسی ادمین ندارید! 🚫"
        )
        return EVENT_SELECTION
    await query.message.reply_text(
        f"{user_name} عزیز، نوع رویداد را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("دوره 📚", callback_data="type_دوره"),
             InlineKeyboardButton("بازدید 🏭", callback_data="type_بازدید")]
        ])
    )
    return ADD_EVENT_TYPE

async def add_event_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    if user_id not in ADMIN_IDS:
        await query.message.reply_text(
            f"{user_name} عزیز،\nشما دسترسی ادمین ندارید! 🚫"
        )
        return EVENT_SELECTION
    context.user_data['event_type'] = query.data.split("_")[1]
    await query.message.reply_text(
        f"{user_name} عزیز، لطفاً عنوان رویداد را وارد کنید:"
    )
    return ADD_EVENT_TITLE

async def add_event_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    context.user_data['event_title'] = update.message.text.strip()
    await update.message.reply_text(
        f"{user_name} عزیز، لطفاً توضیحات رویداد را وارد کنید:"
    )
    return ADD_EVENT_DESCRIPTION

async def add_event_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    date = update.message.text.strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        await update.message.reply_text(
            f"{user_name} عزیز،\nلطفاً تاریخ را به‌صورت YYYY-MM-DD وارد کنید:"
        )
        return ADD_EVENT_DATE
    try:
        datetime.strptime(date, "%Y-%m-%d")
        context.user_data['event_date'] = date
        await update.message.reply_text(
            f"{user_name} عزیز، لطفاً محل برگزاری رویداد را وارد کنید:"
        )
        return ADD_EVENT_LOCATION
    except ValueError:
        await update.message.reply_text(
            f"{user_name} عزیز،\nتاریخ واردشده معتبر نیست. لطفاً تاریخ را به‌صورت YYYY-MM-DD وارد کنید:"
        )
        return ADD_EVENT_DATE

async def add_event_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    context.user_data['event_location'] = update.message.text.strip()
    await update.message.reply_text(
        f"{user_name} عزیز، لطفاً ظرفیت رویداد را وارد کنید (عدد):"
    )
    return ADD_EVENT_CAPACITY

async def add_event_capacity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        capacity = int(update.message.text.strip())
        if capacity <= 0:
            raise ValueError
        context.user_data['event_capacity'] = capacity
        await update.message.reply_text(
            f"{user_name} عزیز، لطفاً هزینه رویداد را وارد کنید (به تومان، برای رویداد رایگان 0 وارد کنید):"
        )
        return ADD_EVENT_COST
    except ValueError:
        await update.message.reply_text(
            f"{user_name} عزیز،\nلطفاً یک عدد معتبر برای ظرفیت وارد کنید:"
        )
        return ADD_EVENT_CAPACITY

async def add_event_cost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        cost = int(update.message.text.strip())
        if cost < 0:
            raise ValueError
        context.user_data['event_cost'] = cost
        if cost > 0:
            await update.message.reply_text(
                f"{user_name} عزیز، لطفاً شماره کارت برای پرداخت را وارد کنید (مثل 1234-5678-9012-3456):"
            )
            return ADD_EVENT_COST
        else:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    c = conn.cursor()
                    hashtag = f"{context.user_data['event_type']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    c.execute(
                        "INSERT INTO events (title, type, date, location, capacity, current_capacity, description, is_active, hashtag, cost, card_number) "
                        "VALUES (?, ?, ?, ?, ?, 0, ?, 1, ?, ?, ?)",
                        (context.user_data['event_title'], context.user_data['event_type'], context.user_data['event_date'],
                         context.user_data['event_location'], context.user_data['event_capacity'],
                         context.user_data['event_description'], hashtag, cost, "")
                    )
                    conn.commit()
                await update.message.reply_text(
                    f"{user_name} عزیز،\nرویداد با موفقیت اضافه شد! 🎉\nهشتگ: #{hashtag}"
                )
                context.user_data.clear()
                return EVENT_SELECTION
            except Exception as e:
                logger.error(f"Error adding event: {e}")
                await update.message.reply_text(
                    f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
                )
                return ADD_EVENT_COST
    except ValueError:
        await update.message.reply_text(
            f"{user_name} عزیز،\nلطفاً یک عدد معتبر برای هزینه وارد کنید:"
        )
        return ADD_EVENT_COST

async def save_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    card_number = update.message.text.strip()
    if not re.match(r"^\d{4}-\d{4}-\d{4}-\d{4}$", card_number):
        await update.message.reply_text(
            f"{user_name} عزیز،\nلطفاً شماره کارت را به‌صورت معتبر وارد کنید (مثل 1234-5678-9012-3456):"
        )
        return ADD_EVENT_COST
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            hashtag = f"{context.user_data['event_type']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            c.execute(
                "INSERT INTO events (title, type, date, location, capacity, current_capacity, description, is_active, hashtag, cost, card_number) "
                "VALUES (?, ?, ?, ?, ?, 0, ?, 1, ?, ?, ?)",
                (context.user_data['event_title'], context.user_data['event_type'], context.user_data['event_date'],
                 context.user_data['event_location'], context.user_data['event_capacity'],
                 context.user_data['event_description'], hashtag, context.user_data['event_cost'], card_number)
            )
            conn.commit()
        await update.message.reply_text(
            f"{user_name} عزیز،\nرویداد با موفقیت اضافه شد! 🎉\nهشتگ: #{hashtag}"
        )
        context.user_data.clear()
        return EVENT_SELECTION
    except Exception as e:
        logger.error(f"Error saving event: {e}")
        await update.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return ADD_EVENT_COST

async def edit_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    if user_id not in ADMIN_IDS:
        await query.message.reply_text(
            f"{user_name} عزیز،\nشما دسترسی ادمین ندارید! 🚫"
        )
        return EVENT_SELECTION
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM events ORDER BY date")
            events = c.fetchall()
        if not events:
            await query.message.reply_text(
                f"{user_name} عزیز،\nهیچ رویدادی برای ویرایش وجود ندارد. 📪"
            )
            return EVENT_SELECTION
        buttons = []
        for event in events:
            buttons.append([InlineKeyboardButton(
                f"{event['type']} {event['title']} - {event['date']}",
                callback_data=f"edit_event_{event['event_id']}"
            )])
        buttons.append([InlineKeyboardButton("بازگشت ↩️", callback_data="main_menu")])
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً رویداد موردنظر برای ویرایش را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return EVENT_SELECTION
    except Exception as e:
        logger.error(f"Error fetching events for edit: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def edit_event_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    if user_id not in ADMIN_IDS:
        await query.message.reply_text(
            f"{user_name} عزیز،\nشما دسترسی ادمین ندارید! 🚫"
        )
        return EVENT_SELECTION
    try:
        event_id = int(query.data.split("_")[2])
        context.user_data['edit_event_id'] = event_id
        event = get_event(event_id)
        if not event:
            await query.message.reply_text(
                f"{user_name} عزیز،\nاین رویداد یافت نشد! 📪"
            )
            return EVENT_SELECTION
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً توضیحات جدید رویداد را وارد کنید (فعلی: {event['description']}):"
        )
        return EDIT_EVENT_TEXT
    except Exception as e:
        logger.error(f"Error starting event edit: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def save_event_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    event_id = context.user_data.get('edit_event_id')
    new_description = update.message.text.strip()
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute("UPDATE events SET description = ? WHERE event_id = ?", (new_description, event_id))
            conn.commit()
        await update.message.reply_text(
            f"{user_name} عزیز،\nتوضیحات رویداد با موفقیت ویرایش شد! ✅"
        )
        context.user_data.clear()
        return EVENT_SELECTION
    except Exception as e:
        logger.error(f"Error saving event text: {e}")
        await update.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EDIT_EVENT_TEXT

async def toggle_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    if user_id not in ADMIN_IDS:
        await query.message.reply_text(
            f"{user_name} عزیز،\nشما دسترسی ادمین ندارید! 🚫"
        )
        return EVENT_SELECTION
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM events ORDER BY date")
            events = c.fetchall()
        if not events:
            await query.message.reply_text(
                f"{user_name} عزیز،\nهیچ رویدادی برای مدیریت وجود ندارد. 📪"
            )
            return EVENT_SELECTION
        buttons = []
        for event in events:
            status = "فعال ✅" if event['is_active'] else "غیرفعال 🚫"
            buttons.append([InlineKeyboardButton(
                f"{event['type']} {event['title']} - {status}",
                callback_data=f"toggle_event_{event['event_id']}"
            )])
        buttons.append([InlineKeyboardButton("بازگشت ↩️", callback_data="main_menu")])
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً رویداد موردنظر را برای تغییر وضعیت انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return EVENT_SELECTION
    except Exception as e:
        logger.error(f"Error fetching events for toggle: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def toggle_event_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    if user_id not in ADMIN_IDS:
        await query.message.reply_text(
            f"{user_name} عزیز،\nشما دسترسی ادمین ندارید! 🚫"
        )
        return EVENT_SELECTION
    try:
        event_id = int(query.data.split("_")[2])
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT is_active FROM events WHERE event_id = ?", (event_id,))
            is_active = c.fetchone()[0]
            new_status = 0 if is_active else 1
            reason = "دستی توسط ادمین" if new_status == 0 else ""
            c.execute(
                "UPDATE events SET is_active = ?, deactivation_reason = ? WHERE event_id = ?",
                (new_status, reason, event_id)
            )
            conn.commit()
        status_text = "غیرفعال" if new_status == 0 else "فعال"
        await query.message.reply_text(
            f"{user_name} عزیز،\nرویداد با موفقیت {status_text} شد! ✅"
        )
        return EVENT_SELECTION
    except Exception as e:
        logger.error(f"Error toggling event: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def manage_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    if user_id not in ADMIN_IDS:
        await query.message.reply_text(
            f"{user_name} عزیز،\nشما دسترسی ادمین ندارید! 🚫"
        )
        return EVENT_SELECTION
    await query.message.reply_text(
        f"{user_name} عزیز، لطفاً ID کاربری ادمین جدید را وارد کنید یا برای بازگشت انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بازگشت ↩️", callback_data="main_menu")]
        ])
    )
    return EVENT_SELECTION

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(
            f"{user_name} عزیز،\nشما دسترسی ادمین ندارید! 🚫"
        )
        return EVENT_SELECTION
    try:
        new_admin_id = int(update.message.text.strip())
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM admins WHERE user_id = ?", (new_admin_id,))
            if c.fetchone():
                await update.message.reply_text(
                    f"{user_name} عزیز،\nاین کاربر قبلاً ادمین است! 🚫"
                )
                return EVENT_SELECTION
            c.execute(
                "INSERT INTO admins (user_id, added_at) VALUES (?, ?)",
                (new_admin_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
        await update.message.reply_text(
            f"{user_name} عزیز،\nادمین جدید با موفقیت اضافه شد! ✅"
        )
        await context.bot.send_message(
            chat_id=new_admin_id,
            text="شما به‌عنوان ادمین ربات انتخاب شده‌اید! 🎉\nبرای شروع از /start استفاده کنید."
        )
        return EVENT_SELECTION
    except ValueError:
        await update.message.reply_text(
            f"{user_name} عزیز،\nلطفاً یک ID معتبر وارد کنید:"
        )
        return EVENT_SELECTION
    except telegram.error.TelegramError as e:
        logger.error(f"Error notifying new admin: {e}")
        await update.message.reply_text(
            f"{user_name} عزیز،\nادمین اضافه شد اما نتوانستیم به او اطلاع دهیم. 🚫"
        )
        return EVENT_SELECTION
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        await update.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            if user_id not in ADMIN_IDS:
                c.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,))
                if not c.fetchone():
                    await query.message.reply_text(
                        f"{user_name} عزیز،\nشما دسترسی ادمین ندارید! 🚫"
                    )
                    return EVENT_SELECTION
            c.execute("SELECT * FROM events WHERE is_active = 1 ORDER BY date")
            events = c.fetchall()
        buttons = [[InlineKeyboardButton("بدون رویداد 📢", callback_data="message_no_event")]]
        for event in events:
            buttons.append([InlineKeyboardButton(
                f"{event['type']} {event['title']}",
                callback_data=f"message_event_{event['event_id']}"
            )])
        buttons.append([InlineKeyboardButton("بازگشت ↩️", callback_data="main_menu")])
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً رویداد مرتبط با پیام را انتخاب کنید یا بدون رویداد ادامه دهید:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return SEND_ADMIN_MESSAGE
    except Exception as e:
        logger.error(f"Error fetching events for admin message: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def send_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            if user_id not in ADMIN_IDS:
                c.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,))
                if not c.fetchone():
                    await query.message.reply_text(
                        f"{user_name} عزیز،\nشما دسترسی ادمین ندارید! 🚫"
                    )
                    return EVENT_SELECTION
        if query.data == "message_no_event":
            context.user_data['event_id'] = None
        else:
            context.user_data['event_id'] = int(query.data.split("_")[2])
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً متن پیام را وارد کنید:"
        )
        return SEND_ADMIN_MESSAGE
    except Exception as e:
        logger.error(f"Error starting admin message: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def save_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    message_text = update.message.text.strip()
    event_id = context.user_data.get('event_id')
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            if event_id:
                c.execute("SELECT * FROM registrations WHERE event_id = ?", (event_id,))
                registrations = c.fetchall()
                user_ids = [reg[1] for reg in registrations]
            else:
                c.execute("SELECT user_id FROM users")
                user_ids = [row[0] for row in c.fetchall()]
            for uid in user_ids:
                await context.bot.send_message(chat_id=uid, text=message_text)
            c.execute(
                "INSERT INTO messages (admin_id, event_id, message_text, sent_at) VALUES (?, ?, ?, ?)",
                (user_id, event_id, message_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
        await update.message.reply_text(
            f"{user_name} عزیز،\nپیام شما با موفقیت برای {len(user_ids)} کاربر ارسال شد! ✅"
        )
        context.user_data.clear()
        return EVENT_SELECTION
    except telegram.error.TelegramError as e:
        logger.error(f"Error sending admin message: {e}")
        await update.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. ممکن است برخی کاربران پیام را دریافت نکرده باشند. 🚫"
        )
        return EVENT_SELECTION
    except Exception as e:
        logger.error(f"Error in save_admin_message: {e}")
        await update.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return SEND_ADMIN_MESSAGE

async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            if user_id not in ADMIN_IDS:
                c.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,))
                if not c.fetchone():
                    await query.message.reply_text(
                        f"{user_name} عزیز،\nشما دسترسی ادمین ندارید! 🚫"
                    )
                    return EVENT_SELECTION
            c.execute("SELECT * FROM events ORDER BY date")
            events = c.fetchall()
        buttons = []
        for event in events:
            buttons.append([InlineKeyboardButton(
                f"{event['type']} {event['title']} - {event['date']}",
                callback_data=f"report_{event['event_id']}"
            )])
        buttons.append([InlineKeyboardButton("بازگشت ↩️", callback_data="main_menu")])
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً رویداد موردنظر برای گزارش را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return REPORTS
    except Exception as e:
        logger.error(f"Error fetching events for reports: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        event_id = int(query.data.split("_")[1])
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            event = get_event(event_id)
            if not event:
                await query.message.reply_text(
                    f"{user_name} عزیز،\nاین رویداد یافت نشد! 📪"
                )
                return EVENT_SELECTION
            c.execute("SELECT * FROM registrations WHERE event_id = ?", (event_id,))
            registrations = c.fetchall()
        report_text = f"گزارش برای {event['type']} {event['title']}:\n\n"
        report_text += f"تعداد ثبت‌نام‌ها: {len(registrations)}\n"
        report_text += f"ظرفیت باقی‌مانده: {event['capacity'] - event['current_capacity']}\n\n"
        report_text += "لیست ثبت‌نام‌کنندگان:\n"
        for reg in registrations:
            user = get_user_profile(reg[1])
            if user:
                report_text += f"- {user['full_name']} (کد ملی: {user['national_id']}, تماس: {user['phone']})\n"
        await query.message.reply_text(
            report_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("بازگشت ↩️", callback_data="main_menu")]
            ])
        )
        return EVENT_SELECTION
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def manual_registration_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            if user_id not in ADMIN_IDS:
             ```python
            c.execute("SELECT * FROM events WHERE is_active = 1 ORDER BY date")
            events = c.fetchall()
        if not events:
            await query.message.reply_text(
                f"{user_name} عزیز،\nهیچ رویداد فعالی برای ثبت‌نام دستی وجود ندارد. 📪"
            )
            return EVENT_SELECTION
        buttons = []
        for event in events:
            buttons.append([InlineKeyboardButton(
                f"{event['type']} {event['title']} - {event['date']}",
                callback_data=f"manual_reg_{event['event_id']}"
            )])
        buttons.append([InlineKeyboardButton("بازگشت ↩️", callback_data="main_menu")])
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً رویداد موردنظر برای ثبت‌نام دستی را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return MANUAL_REGISTRATION_EVENT
    except Exception as e:
        logger.error(f"Error fetching events for manual registration: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def manual_registration_student_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    try:
        event_id = int(query.data.split("_")[2])
        context.user_data['manual_event_id'] = event_id
        event = get_event(event_id)
        if not event or not event['is_active']:
            await query.message.reply_text(
                f"{user_name} عزیز،\nاین رویداد دیگر در دسترس نیست. 📪"
            )
            return EVENT_SELECTION
        if event['current_capacity'] >= event['capacity']:
            await query.message.reply_text(
                f"{user_name} عزیز،\nظرفیت این رویداد تکمیل شده است. 🚫"
            )
            return EVENT_SELECTION
        await query.message.reply_text(
            f"{user_name} عزیز، لطفاً شماره دانشجویی کاربر را وارد کنید:"
        )
        return MANUAL_REGISTRATION_STUDENT_ID
    except Exception as e:
        logger.error(f"Error starting manual registration: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return EVENT_SELECTION

async def manual_registration_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    student_id = update.message.text.strip()
    if not re.match(r"^\d{8,10}$", student_id):
        await update.message.reply_text(
            f"{user_name} عزیز،\nلطفاً شماره دانشجویی را به‌صورت ۸ تا ۱۰ رقم وارد کنید:"
        )
        return MANUAL_REGISTRATION_STUDENT_ID
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE student_id = ?", (student_id,))
            user = c.fetchone()
            if not user:
                await update.message.reply_text(
                    f"{user_name} عزیز،\nکاربری با این شماره دانشجویی یافت نشد. 🚫"
                )
                return MANUAL_REGISTRATION_STUDENT_ID
            context.user_data['manual_user_id'] = user['user_id']
            event_id = context.user_data.get('manual_event_id')
            event = get_event(event_id)
            if not event:
                await update.message.reply_text(
                    f"{user_name} عزیز،\nاین رویداد یافت نشد! 📪"
                )
                return EVENT_SELECTION
            await update.message.reply_text(
                f"{user_name} عزیز، اطلاعات ثبت‌نام:\n"
                f"رویداد: {event['type']} {event['title']}\n"
                f"کاربر: {user['full_name']} (شماره دانشجویی: {student_id})\n"
                f"آیا این اطلاعات درست است؟",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("تأیید ✅", callback_data="manual_confirm"),
                     InlineKeyboardButton("لغو ❎", callback_data="manual_cancel")]
                ])
            )
            return MANUAL_REGISTRATION_CONFIRM
    except Exception as e:
        logger.error(f"Error confirming manual registration: {e}")
        await update.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
        return MANUAL_REGISTRATION_STUDENT_ID

async def manual_registration_final(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    if query.data == "manual_cancel":
        await query.message.reply_text(
            f"{user_name} عزیز،\nثبت‌نام دستی لغو شد. 🚫"
        )
        context.user_data.clear()
        return EVENT_SELECTION
    try:
        manual_user_id = context.user_data.get('manual_user_id')
        event_id = context.user_data.get('manual_event_id')
        event = get_event(event_id)
        if not event or not event['is_active']:
            await query.message.reply_text(
                f"{user_name} عزیز،\nاین رویداد دیگر در دسترس نیست. 📪"
            )
            return EVENT_SELECTION
        if event['current_capacity'] >= event['capacity']:
            await query.message.reply_text(
                f"{user_name} عزیز،\nظرفیت این رویداد تکمیل شده است. 🚫"
            )
            return EVENT_SELECTION
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM registrations WHERE user_id = ? AND event_id = ?", (manual_user_id, event_id))
            if c.fetchone():
                await query.message.reply_text(
                    f"{user_name} عزیز،\nاین کاربر قبلاً برای این رویداد ثبت‌نام کرده است! ✅"
                )
                return EVENT_SELECTION
            c.execute(
                "INSERT INTO registrations (user_id, event_id, registered_at) VALUES (?, ?, ?)",
                (manual_user_id, event_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            c.execute("UPDATE events SET current_capacity = current_capacity + 1 WHERE event_id = ?", (event_id,))
            conn.commit()
        manual_user = get_user_profile(manual_user_id)
        message_to_operators = (
            f"ثبت‌نام دستی\n"
            f"#{event['type']} {event['hashtag']}\n"
            f"نام: {manual_user['full_name']}\n"
            f"کد ملی: {manual_user['national_id']}\n"
            f"شماره دانشجویی: {manual_user['student_id']}\n"
            f"شماره تماس: {manual_user['phone']}\n"
            f"توسط: {user_name}"
        )
        sent_message = await context.bot.send_message(chat_id=OPERATOR_GROUP_ID, text=message_to_operators)
        with sqlite3.connect(DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO operator_messages (message_id, chat_id, user_id, event_id, message_type, sent_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (sent_message.message_id, OPERATOR_GROUP_ID, manual_user_id, event_id, "manual_registration", 
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
        await query.message.reply_text(
            f"{user_name} عزیز،\nثبت‌نام دستی برای {manual_user['full_name']} با موفقیت انجام شد! ✅"
        )
        await context.bot.send_message(
            chat_id=manual_user_id,
            text=f"{manual_user['full_name']} عزیز،\nشما با موفقیت در {event['type']} {event['title']} ثبت‌نام شدید! ✅"
        )
        context.user_data.clear()
        return EVENT_SELECTION
    except telegram.error.TelegramError as e:
        logger.error(f"Error in manual registration: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
    except Exception as e:
        logger.error(f"Error in manual_registration_final: {e}")
        await query.message.reply_text(
            f"{user_name} عزیز،\nخطایی رخ داد. لطفاً دوباره تلاش کنید. 🚫"
        )
    return EVENT_SELECTION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_name = get_user_profile(user_id)['full_name'] if get_user_profile(user_id) else update.effective_user.first_name
    await update.message.reply_text(
        f"{user_name} عزیز،\nعملیات لغو شد. برای شروع مجدد از /start استفاده کنید. 🚫",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHECK_CHANNEL: [CallbackQueryHandler(check_channel, pattern="^check_channel$")],
            PROFILE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, profile_name),
                CallbackQueryHandler(confirm_name, pattern="^(confirm_name|retry_name)$")
            ],
            PROFILE_NATIONAL_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, profile_national_id),
                CallbackQueryHandler(confirm_national_id, pattern="^(confirm_national_id|retry_national_id)$")
            ],
            PROFILE_STUDENT_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, profile_student_id),
                CallbackQueryHandler(confirm_student_id, pattern="^(confirm_student_id|retry_student_id)$")
            ],
            PROFILE_CONTACT: [
                MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), profile_contact),
                CallbackQueryHandler(confirm_all, pattern="^(confirm_all|retry_all)$")
            ],
            EVENT_SELECTION: [
                CallbackQueryHandler(view_events, pattern="^view_events$"),
                CallbackQueryHandler(event_details, pattern="^event_"),
                CallbackQueryHandler(check_channel_register, pattern="^check_channel_register$"),
                CallbackQueryHandler(edit_profile, pattern="^edit_profile$"),
                CallbackQueryHandler(support, pattern="^support$"),
                CallbackQueryHandler(main_menu, pattern="^main_menu$"),
                CallbackQueryHandler(faq, pattern="^faq$"),
                CallbackQueryHandler(add_event_type, pattern="^add_event$"),
                CallbackQueryHandler(edit_event, pattern="^edit_event$"),
                CallbackQueryHandler(toggle_event, pattern="^toggle_event$"),
                CallbackQueryHandler(manage_admins, pattern="^manage_admins$"),
                CallbackQueryHandler(admin_message, pattern="^admin_message$"),
                CallbackQueryHandler(reports, pattern="^reports$"),
                CallbackQueryHandler(manual_registration_event, pattern="^manual_registration$"),
                CallbackQueryHandler(no_action, pattern="^no_action$")
            ],
            REGISTRATION: [
                CallbackQueryHandler(register_event, pattern="^register_"),
                CallbackQueryHandler(check_channel_register, pattern="^check_channel_register$")
            ],
            PAYMENT_RECEIPT: [
                MessageHandler(filters.PHOTO, payment_receipt),
                MessageHandler(filters.ALL & ~filters.PHOTO, lambda u, c: u.message.reply_text("لطفاً فقط تصویر رسید را ارسال کنید.")),
                CallbackQueryHandler(confirm_payment, pattern="^confirm_payment_"),
                CallbackQueryHandler(reject_payment, pattern="^reject_payment_"),
                CallbackQueryHandler(unreadable_payment, pattern="^unreadable_payment_")
            ],
            SUPPORT_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, support_message)
            ],
            ADD_EVENT_TYPE: [
                CallbackQueryHandler(add_event_title, pattern="^type_")
            ],
            ADD_EVENT_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_description)
            ],
            ADD_EVENT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_date)
            ],
            ADD_EVENT_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_date)
            ],
            ADD_EVENT_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_location)
            ],
            ADD_EVENT_CAPACITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_capacity)
            ],
            ADD_EVENT_COST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_cost),
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_event)
            ],
            SEND_ADMIN_MESSAGE: [
                CallbackQueryHandler(send_admin_message, pattern="^(message_no_event|message_event_)"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_admin_message)
            ],
            EDIT_EVENT_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_event_text)
            ],
            REPORTS: [
                CallbackQueryHandler(show_report, pattern="^report_")
            ],
            MANUAL_REGISTRATION_EVENT: [
                CallbackQueryHandler(manual_registration_student_id, pattern="^manual_reg_")
            ],
            MANUAL_REGISTRATION_STUDENT_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, manual_registration_confirm)
            ],
            MANUAL_REGISTRATION_CONFIRM: [
                CallbackQueryHandler(manual_registration_final, pattern="^(manual_confirm|manual_cancel)$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(conv_handler)
    application.job_queue.run_daily(
        cleanup_old_messages,
        time=time(hour=0, minute=0),
        days=(0, 1, 2, 3, 4, 5, 6)
    )
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
