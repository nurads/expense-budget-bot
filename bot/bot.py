import time, re
from decimal import Decimal
from django.conf import settings
from telebot import TeleBot
from .models import *
from .diagrams import *
from .utils import *
from django.db.models import Sum, F, Value
from telebot.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ChatJoinRequest,
)

bot = TeleBot(settings.BOT_TOKEN, threaded=False)

# User states for conversation flow
user_states = {}

msg_spent = "I Spent 😥"
msg_earnt = "I Earnt 😊"
msg_debt = "I am in Debt 😓"
msg_owe = "Someone owes me 🙄"
msg_reports = "📊 Reports"
msg_streaks = "🔥 Streaks"
msg_settings = "⚙️ Settings"
msg_categories = "📁 Categories"
msg_budget = "💰 Budget"
msg_savings = "🎯 Savings Goals"
msg_debt_management = "💳 Debt Management"
msg_owe_management = "💰 Owe Management"
msg_cancel = "❌ Cancel"

"""
start - start the bot
spends - show my spendings
earnings - show my earnings
debts - show my debts
owes - show my owes

"""


def get_keyboard(**kwargs):
    keyboard = ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True,
        one_time_keyboard=kwargs.get("one_time_keyboard") is not None,
    )

    if not kwargs:
        keyboard.add(
            KeyboardButton(msg_spent),
            KeyboardButton(msg_earnt),
            KeyboardButton(msg_debt),
            KeyboardButton(msg_owe),
        ).add(
            KeyboardButton(msg_reports),
            KeyboardButton(msg_streaks),
        ).add(
            KeyboardButton(msg_savings),
            KeyboardButton(msg_debt_management),
        ).add(
            KeyboardButton(msg_owe_management),
            KeyboardButton(msg_settings),
        ).add(
            KeyboardButton(msg_categories),
        )
    else:
        ls = []
        for key, value in kwargs.items():
            ls.append(KeyboardButton(" ".join(key.split("_")), **value))
        keyboard.add(*ls)
    return keyboard


def get_common_amount():
    mark = ReplyKeyboardMarkup(
        row_width=3, resize_keyboard=True, one_time_keyboard=True, is_persistent=False
    )

    mark.add(
        KeyboardButton("100"),
        KeyboardButton("200"),
        KeyboardButton("300"),
        KeyboardButton("400"),
        KeyboardButton("500"),
        KeyboardButton("1000"),
        KeyboardButton("1500"),
        KeyboardButton("2000"),
        KeyboardButton("2500"),
        KeyboardButton("5000"),
        KeyboardButton("10000"),
        KeyboardButton("15000"),
    ).add(
        KeyboardButton("Custom"),
        KeyboardButton(msg_cancel),
    )

    return mark


def delete_message(message):
    return bot.delete_message(message.chat.id, message.id)


def handle_cancel(message, user):
    """Handle cancel action and clear user state"""
    if hasattr(user, 'chat_id') and user.chat_id in user_states:
        del user_states[user.chat_id]
    
    bot.send_message(
        message.chat.id,
        "❌ Action cancelled. You can start over anytime!",
        reply_markup=get_keyboard()
    )


def get_user(message, func, *args):
    try:

        from_user = message.from_user

        contact = User.objects.get(username=from_user.id)

        return contact
    except:
        mark = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        mark.add(KeyboardButton("Share Contact", request_contact=True))
        bot.register_next_step_handler(message, contact_handler,func,*args)
        msg = """
Share your contact
        """
        bot.send_message(message.chat.id, msg, reply_markup=mark)


def get_amount(message, func):
    delete_message(message)
    
    # Handle cancel
    if message.text == msg_cancel:
        user = get_user(message, get_amount, func)
        if user:
            handle_cancel(message, user)
        return
    
    if message.text == msg_spent:
        return spnt(message)
    if message.text == msg_earnt:
        return ernt(message)
    if message.text == msg_owe:
        return ow(message)
    if message.text == msg_debt:
        return debt(message)

    if message.text == "Custom":
        bot.register_next_step_handler(message, get_custom_amount, func)
        bot.send_message(message.chat.id, "💵 Enter the amount (or type 'cancel' to cancel):")
        return

    if not message.text.isdigit():
        bot.register_next_step_handler(message, get_amount, func)
        bot.send_message(message.chat.id, "❌ Please enter only numbers or use 'Cancel' to cancel")
        return
    
    func(message, amount=message.text)


def get_custom_amount(message, func):
    """Handle custom amount input with cancel support"""
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        user = get_user(message, get_custom_amount, func)
        if user:
            handle_cancel(message, user)
        return
    
    if not message.text.replace('.', '').isdigit():
        bot.register_next_step_handler(message, get_custom_amount, func)
        bot.send_message(message.chat.id, "❌ Please enter a valid number or type 'cancel' to cancel")
        return
    
    func(message, amount=message.text)


def get_text(message, func, *args):
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        user = get_user(message, get_text, func, *args)
        if user:
            handle_cancel(message, user)
        return
    
    if message.text == msg_spent:
        return spnt(message)
    if message.text == msg_earnt:
        return ernt(message)
    if message.text == msg_owe:
        return ow(message)
    if message.text == msg_debt:
        return debt(message)

    func(message, text=message.text, *args)


@bot.message_handler(func=lambda msg: msg.text == msg_cancel)
def handle_cancel_message(message):
    """Handle cancel message from main menu"""
    user = get_user(message, handle_cancel_message)
    if user:
        handle_cancel(message, user)


@bot.message_handler(commands=["start"])
def start(message):
    user = get_user(message, start)
    
    if not user:
        return

    bot.send_message(
        message.chat.id, f"Hello {user.first_name}👋", reply_markup=get_keyboard()
    )


@bot.message_handler(func=lambda msg: msg.text == msg_earnt)
def ernt(message, amount=None, text=None):
    user = get_user(message, ernt)
    if not user:
        return
    if not amount:
        bot.register_next_step_handler(message, get_amount, ernt)
        return bot.send_message(
            message.chat.id,
            "Yay 🥳 how much did you earn?",
            reply_markup=get_common_amount(),
        )
    if not text:
        bot.register_next_step_handler(message, get_text, ernt, amount)
        return bot.send_message(message.chat.id, "📝 What was the source of income? (or type 'cancel' to cancel)")

    Income.objects.create(reason=text, amount=Decimal(amount), user=user, currency=user.default_currency)
    total = user.incomes.all().aggregate(total=Sum("amount"))["total"] or 0

    # Update user streak
    update_user_streak(user)

    msg = f"""
💰 **Earnings Summary**

🤑 **Earned Amount**: `{format_currency(amount, user.default_currency)}`

💼 **Total Amount**: `{format_currency(total, user.default_currency)}`
"""

    bot.send_message(
        message.chat.id, msg, reply_markup=get_keyboard()
    )


@bot.message_handler(func=lambda msg: msg.text == msg_spent)
def spnt(message, amount=None, text=None):
    user = get_user(message, spnt)
    if not amount:
        bot.register_next_step_handler(message, get_amount, spnt)
        return bot.send_message(
            message.chat.id,
            "Hmm...🤔 How much did you spend?",
            reply_markup=get_common_amount(),
        )
    if not text:
        bot.register_next_step_handler(message, get_text, spnt, amount)
        return bot.send_message(message.chat.id, "📝 What did you spend on? (or type 'cancel' to cancel)")

    # Create expense using the new Expense model
    Expense.objects.create(user=user, amount=Decimal(amount), reason=text, currency=user.default_currency)
    
    # Get total expenses for the month
    from datetime import datetime, timedelta
    from django.utils import timezone
    start_date = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_expenses = user.expenses.filter(created_at__gte=start_date).aggregate(total=Sum("amount"))["total"] or 0

    # Update user streak
    update_user_streak(user)

    msg = f"""
💰 **Spent Summary**

🤑 **Spent Amount**: `{format_currency(amount, user.default_currency)}`

💼 **Monthly Total**: `{format_currency(monthly_expenses, user.default_currency)}`
"""

    bot.send_message(
        message.chat.id, msg, reply_markup=get_keyboard()
    )


@bot.message_handler(func=lambda msg: msg.text == msg_owe)
def ow(message, amount=None, text=None):
    user = get_user(message, ow, amount, text)
    
    if not user:
        return
    
    if not amount:
        bot.register_next_step_handler(message, get_amount, ow)
        return bot.send_message(
            message.chat.id,
            "Okay go on...how much they take from you?",
            reply_markup=get_common_amount(),
        )
    if not text:
        bot.register_next_step_handler(message, get_text, ow, amount)
        return bot.send_message(message.chat.id, "👤 Who owes you money? (or type 'cancel' to cancel)")

    Owe.objects.create(
        user=user,
        name=text,
        amount=Decimal(amount),
        currency=user.default_currency,
    )
    total = Owe.objects.filter(user=user, amount__gte=0).aggregate(total=Sum("amount"))["total"] or 0
    msg = f"""
💰 You have {format_currency(total, user.default_currency)} from others
    """
    bot.send_message(
        message.chat.id, msg, reply_markup=get_keyboard())



@bot.message_handler(func=lambda msg: msg.text == msg_debt)
def debt(message, amount=None, text=None):
    user = get_user(message, debt, amount, text)
    
    if not user:
        return 
    if not amount:
        bot.register_next_step_handler(message, get_amount, debt)
        return bot.send_message(
            message.chat.id,
            "Seriously...how much debt??",
            reply_markup=get_common_amount(),
        )

    if not text:
        bot.register_next_step_handler(message, get_text, debt, amount)
        return bot.send_message(message.chat.id, "👤 Who do you owe money to? (or type 'cancel' to cancel)")

    Owe.objects.create(
        user=user,
        name=text,
        amount=Decimal(amount) * -1,
        currency=user.default_currency,
    )

    total = Owe.objects.filter(user=user, amount__lte=0).aggregate(total=Sum("amount"))["total"] or 0

    msg = f"""
💰 You are {format_currency(abs(total), user.default_currency)} in debt
    """
    bot.send_message(
        message.chat.id, msg, reply_markup=get_keyboard()
    )


@bot.message_handler(commands=["spends"])
def spens(message):
    user = get_user(message, spens)
    if not user:
        return

    # Get expenses from last 30 days
    from datetime import timedelta
    from django.utils import timezone
    start_date = timezone.now() - timedelta(days=30)
    expenses = user.expenses.filter(created_at__gte=start_date)
    
    if not expenses.exists():
        bot.send_message(message.chat.id, "📊 No expenses found in the last 30 days.")
        return

    expense_breakdown = expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    labels = [item['category'] for item in expense_breakdown]
    sizes = [float(item['total']) for item in expense_breakdown]
    img = get_pie(sizes, labels)
    
    total = sum(sizes)
    msg = f"💸 Total spent: {format_currency(total, user.default_currency)}"
    
    bot.send_photo(message.chat.id, photo=img, caption=msg, )


@bot.message_handler(commands=["earnings"])
def ernings(message):
    user = get_user(message, ernings)
    if not user:
        return

    # Get income from last 30 days
    from datetime import timedelta
    from django.utils import timezone
    start_date = timezone.now() - timedelta(days=30)
    income = user.incomes.filter(created_at__gte=start_date)
    
    if not income.exists():
        bot.send_message(message.chat.id, "📊 No income found in the last 30 days.")
        return

    income_breakdown = income.values('reason').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    labels = [item['reason'] for item in income_breakdown]
    sizes = [float(item['total']) for item in income_breakdown]
    img = get_pie(sizes, labels)
    
    total = sum(sizes)
    msg = f"💰 Total earned: {format_currency(total, user.default_currency)}"
    
    bot.send_photo(message.chat.id, photo=img, caption=msg, )


@bot.message_handler(commands=["debts"])
def mydebts(message):
    user = get_user(message, mydebts)
    if not user:
        return

    total = Owe.objects.filter(user=user, amount__lte=0).aggregate(total=Sum("amount"))["total"] or 0
    debts = Owe.objects.filter(user=user, amount__lte=0)
    tt = "\n".join(
        [f"\t- {ow.name}: `{format_currency(abs(ow.amount), ow.currency)}`" for ow in debts]
    )
    msg = f"""
Debt Summary
{tt}
____________________________________
💰 You are {format_currency(abs(total), user.default_currency)} in debt
    """
    bot.send_message(
        message.chat.id, msg, reply_markup=get_keyboard())


@bot.message_handler(commands=["owes"])
def my_owes(message):
    user = get_user(message, my_owes)
    if not user:
        return

    total = Owe.objects.filter(user=user, amount__gte=0).aggregate(total=Sum("amount"))["total"] or 0
    tt = "\n".join(
        [f"\t- {ow.name}: `{format_currency(ow.amount, ow.currency)}`" for ow in Owe.objects.filter(user=user, amount__gte=0)]
    )
    msg = f"""
Owe Summary
{tt}
____________________________________
💰 You have {format_currency(total, user.default_currency)} from others
    """
    bot.send_message(
        message.chat.id, msg, reply_markup=get_keyboard()
)


@bot.message_handler(func=lambda msg: msg.text == msg_reports)
def handle_reports(message):
    """Handle reports menu"""
    user = get_user(message, handle_reports)
    if not user:
        return
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("📅 Daily Report", callback_data="report_daily"),
        InlineKeyboardButton("📊 Weekly Report", callback_data="report_weekly"),
    ).add(
        InlineKeyboardButton("📈 Monthly Report", callback_data="report_monthly"),
        InlineKeyboardButton("📋 Yearly Report", callback_data="report_yearly"),
    ).add(
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
    )
    
    bot.send_message(
        message.chat.id,
        "📊 **Select Report Period**\n\nChoose the time period for your financial report:",
        reply_markup=keyboard
    )


@bot.message_handler(func=lambda msg: msg.text == msg_streaks)
def handle_streaks(message):
    """Handle streaks menu"""
    user = get_user(message, handle_streaks)
    if not user:
        return
    
    # Get current streak info
    streak_reward = calculate_streak_reward(user.streak_count)
    
    msg = f"""
🔥 **Your Streak Status**

📅 **Current Streak**: {user.streak_count} days
💰 **Next Reward**: {format_currency(streak_reward, user.default_currency)}
💎 **Total Earned**: {format_currency(user.total_earned_from_streaks, user.default_currency)}

🎯 **How it works:**
• Log expenses or income daily to maintain streak
• Earn rewards based on your streak length
• Longer streaks = bigger rewards!
    """
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🎁 Claim Reward", callback_data="claim_reward"),
        InlineKeyboardButton("📊 Streak History", callback_data="streak_history"),
    ).add(
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
    )
    
    bot.send_message(message.chat.id, msg, reply_markup=keyboard)


@bot.message_handler(func=lambda msg: msg.text == msg_settings)
def handle_settings(message):
    """Handle settings menu"""
    user = get_user(message, handle_settings)
    if not user:
        return
    
    msg = f"""
⚙️ **Settings**

💱 **Default Currency**: {user.default_currency}
🌍 **Timezone**: {user.timezone}
📱 **Phone**: {user.phone_number}

Choose what you'd like to change:
    """
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("💱 Change Currency", callback_data="change_currency"),
        InlineKeyboardButton("🌍 Change Timezone", callback_data="change_timezone"),
    ).add(
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
    )
    
    bot.send_message(message.chat.id, msg, reply_markup=keyboard)


@bot.message_handler(func=lambda msg: msg.text == msg_categories)
def handle_categories(message):
    """Handle categories menu"""
    user = get_user(message, handle_categories)
    if not user:
        return
    
    # Initialize default categories if they don't exist
    get_default_expense_categories()
    
    categories = ExpenseCategory.objects.all()
    msg = "📁 **Available Categories**\n\n"
    
    for category in categories:
        msg += f"{category.emoji} {category.name}\n"
    
    bot.send_message(message.chat.id, msg)


@bot.message_handler(func=lambda msg: msg.text == msg_savings)
def handle_savings_goals(message):
    """Handle savings goals menu"""
    user = get_user(message, handle_savings_goals)
    if not user:
        return
    
    # Get user's savings goals
    goals = user.savings_goals.filter(is_active=True).order_by('-created_at')
    
    if not goals.exists():
        msg = """
🎯 **Savings Goals**

You don't have any savings goals yet!

Create your first goal to start saving for something special! 💰
        """
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("➕ Create New Goal", callback_data="create_savings_goal"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
        )
    else:
        msg = "🎯 **Your Savings Goals**\n\n"
        
        for goal in goals:
            status_emoji = get_savings_goal_status_emoji(goal)
            progress_bar = get_savings_goal_progress_bar(goal)
            
            msg += f"{status_emoji} **{goal.name}**\n"
            msg += f"💰 {format_currency(goal.current_amount, goal.currency)} / {format_currency(goal.target_amount, goal.currency)}\n"
            msg += f"{progress_bar}\n"
            
            if goal.target_date:
                msg += f"📅 Target: {goal.target_date.strftime('%Y-%m-%d')}\n"
            
            if goal.is_completed:
                msg += "🎉 **COMPLETED!**\n"
            elif goal.is_overdue:
                msg += "⚠️ **OVERDUE**\n"
            else:
                daily_needed = calculate_daily_savings_needed(goal)
                if daily_needed and daily_needed > 0:
                    msg += f"📊 Daily needed: {format_currency(daily_needed, goal.currency)}\n"
            
            msg += "\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("➕ Create New Goal", callback_data="create_savings_goal"),
            InlineKeyboardButton("💰 Add Contribution", callback_data="add_contribution"),
        ).add(
            InlineKeyboardButton("📊 Goal Details", callback_data="goal_details"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
        )
    
    bot.send_message(message.chat.id, msg, reply_markup=keyboard)


@bot.message_handler(func=lambda msg: msg.text == msg_debt_management)
def handle_debt_management(message):
    """Handle debt management menu"""
    user = get_user(message, handle_debt_management)
    if not user:
        return
    
    debt_summary = get_debt_summary(user)
    
    if debt_summary['debt_count'] == 0:
        msg = """
💳 **Debt Management**

You don't have any debts! 🎉

Keep up the good financial habits! 💪
        """
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("➕ Add New Debt", callback_data="add_new_debt"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
        )
    else:
        msg = f"""
💳 **Debt Management**

📊 **Total Debt**: {format_currency(debt_summary['total_debt'], debt_summary['currency'])}
📋 **Number of Debts**: {debt_summary['debt_count']}

**Your Debts:**
        """
        
        for debt in debt_summary['debts']:
            msg += f"\n💸 **{debt.name}**\n"
            msg += f"💰 Amount: {format_currency(abs(debt.amount), debt.currency)}\n"
            msg += f"📅 Created: {debt.created_at.strftime('%Y-%m-%d')}\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("💳 Pay Debt", callback_data="pay_debt"),
            InlineKeyboardButton("➕ Add New Debt", callback_data="add_new_debt"),
        ).add(
            InlineKeyboardButton("📊 Debt Details", callback_data="debt_details"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
        )
    
    bot.send_message(message.chat.id, msg, reply_markup=keyboard)


@bot.message_handler(func=lambda msg: msg.text == msg_owe_management)
def handle_owe_management(message):
    """Handle owe management menu"""
    user = get_user(message, handle_owe_management)
    if not user:
        return
    
    owe_summary = get_owe_summary(user)
    
    if owe_summary['owe_count'] == 0:
        msg = """
💰 **Owe Management**

No one owes you money right now! 💰

Track money others owe you to stay on top of your finances! 📊
        """
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("➕ Add New Owe", callback_data="add_new_owe"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
        )
    else:
        msg = f"""
💰 **Owe Management**

📊 **Total Owed**: {format_currency(owe_summary['total_owe'], owe_summary['currency'])}
📋 **Number of Owes**: {owe_summary['owe_count']}

**People who owe you:**
        """
        
        for owe in owe_summary['owes']:
            msg += f"\n💵 **{owe.name}**\n"
            msg += f"💰 Amount: {format_currency(owe.amount, owe.currency)}\n"
            msg += f"📅 Created: {owe.created_at.strftime('%Y-%m-%d')}\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("💰 Collect Money", callback_data="collect_owe"),
            InlineKeyboardButton("➕ Add New Owe", callback_data="add_new_owe"),
        ).add(
            InlineKeyboardButton("📊 Owe Details", callback_data="owe_details"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"),
        )
    
    bot.send_message(message.chat.id, msg, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle callback queries"""
    user = get_user(call, handle_callback)
    if not user:
        return
    
    data = call.data
    bot.answer_callback_query(call.id)
    
    if data.startswith('report_'):
        period = data.split('_')[1]
        generate_report(call.message, user, period)
    
    elif data == 'claim_reward':
        claim_streak_reward(call.message, user)
    
    elif data == 'change_currency':
        bot.send_message(
            call.message.chat.id,
            "💱 Select your default currency:",
            reply_markup=get_currency_keyboard()
        )
    
    elif data.startswith('currency_'):
        currency = data.split('_')[1]
        
        # Check if this is for creating a savings goal, debt, or owe
        if user.chat_id in user_states:
            action = user_states[user.chat_id].get('action')
            if action == 'create_savings_goal':
                user_states[user.chat_id]['currency'] = currency
                create_savings_goal_final(call.message, user)
            elif action == 'add_new_debt':
                user_states[user.chat_id]['currency'] = currency
                create_debt_final(call.message, user)
            elif action == 'add_new_owe':
                user_states[user.chat_id]['currency'] = currency
                create_owe_final(call.message, user)
            else:
                # Default currency change
                user.default_currency = currency
                user.save()
                bot.send_message(
                    call.message.chat.id,
                    f"✅ Default currency changed to {currency}",
                    reply_markup=get_keyboard()
                )
        else:
            # Default currency change
            user.default_currency = currency
            user.save()
            bot.send_message(
                call.message.chat.id,
                f"✅ Default currency changed to {currency}",
                reply_markup=get_keyboard()
            )
    
    elif data == 'cancel_action':
        # Clear any pending user state
        if user.chat_id in user_states:
            del user_states[user.chat_id]
        bot.send_message(
            call.message.chat.id,
            "❌ Action cancelled. You can start over anytime!",
            reply_markup=get_keyboard()
        )
    
    elif data == 'create_savings_goal':
        create_savings_goal_step1(call.message, user)
    
    elif data == 'add_contribution':
        add_contribution_step1(call.message, user)
    
    elif data == 'goal_details':
        show_goal_details(call.message, user)
    
    elif data == 'view_goals':
        handle_savings_goals(call.message)
    
    elif data.startswith('goal_'):
        goal_id = data.split('_')[1]
        if data.startswith('goal_select_'):
            handle_goal_selection(call.message, user, goal_id)
        elif data.startswith('goal_contribute_'):
            handle_goal_contribution(call.message, user, goal_id)
    
    elif data == 'pay_debt':
        pay_debt_step1(call.message, user)
    
    elif data == 'collect_owe':
        collect_owe_step1(call.message, user)
    
    elif data == 'debt_details':
        show_debt_details(call.message, user)
    
    elif data == 'owe_details':
        show_owe_details(call.message, user)
    
    elif data == 'add_new_debt':
        add_new_debt_step1(call.message, user)
    
    elif data == 'add_new_owe':
        add_new_owe_step1(call.message, user)
    
    elif data.startswith('debt_'):
        debt_id = data.split('_')[1]
        if data.startswith('debt_pay_'):
            handle_debt_payment(call.message, user, debt_id)
    
    elif data.startswith('owe_'):
        owe_id = data.split('_')[1]
        if data.startswith('owe_collect_'):
            handle_owe_collection(call.message, user, owe_id)


def get_currency_keyboard():
    """Get currency selection keyboard"""
    keyboard = InlineKeyboardMarkup()
    currencies = get_available_currencies()
    
    for i in range(0, len(currencies), 2):
        row = []
        for j in range(2):
            if i + j < len(currencies):
                code, name = currencies[i + j]
                row.append(InlineKeyboardButton(
                    f"{code} - {name}",
                    callback_data=f"currency_{code}"
                ))
        keyboard.add(*row)
    
    # Add cancel button
    keyboard.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
    
    return keyboard


def get_cancel_keyboard():
    """Get a simple cancel keyboard"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
    return keyboard


def get_savings_amount_keyboard(amounts_list):
    """Get a custom amount keyboard for savings goals"""
    keyboard = ReplyKeyboardMarkup(
        row_width=3, 
        resize_keyboard=True, 
        one_time_keyboard=True, 
        is_persistent=False
    )
    
    amounts = amounts_list + ["Custom", msg_cancel]
    for i in range(0, len(amounts), 3):
        row = amounts[i:i+3]
        keyboard.add(*[KeyboardButton(amount) for amount in row])
    
    return keyboard


def create_savings_goal_step1(message, user):
    """Step 1: Get goal name"""
    user_states[user.chat_id] = {
        'action': 'create_savings_goal',
        'step': 'name'
    }
    
    bot.send_message(
        message.chat.id,
        "🎯 **Create New Savings Goal**\n\nWhat would you like to save for?\n\nExample: New Laptop, Vacation, Emergency Fund",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(message, get_savings_goal_name)


def get_savings_goal_name(message):
    """Get savings goal name"""
    user = get_user(message, get_savings_goal_name)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    user_states[user.chat_id]['name'] = message.text
    user_states[user.chat_id]['step'] = 'target_amount'
    
    # Create a custom keyboard for target amount
    keyboard = get_savings_amount_keyboard(["500", "1000", "2000", "5000", "10000", "20000"])
    
    bot.send_message(
        message.chat.id,
        f"💰 **Target Amount**\n\nHow much do you want to save for '{message.text}'?",
        reply_markup=keyboard
    )
    bot.register_next_step_handler(message, get_savings_goal_target_amount)


def get_savings_goal_target_amount(message):
    """Get savings goal target amount"""
    user = get_user(message, get_savings_goal_target_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text == msg_cancel:
        handle_cancel(message, user)
        return
    
    if message.text == "Custom":
        bot.register_next_step_handler(message, get_savings_goal_custom_amount)
        bot.send_message(message.chat.id, "💵 Enter the target amount (or type 'cancel' to cancel):")
        return
    
    if not message.text.isdigit():
        bot.register_next_step_handler(message, get_savings_goal_target_amount)
        bot.send_message(message.chat.id, "❌ Please enter only numbers or use 'Cancel' to cancel")
        return
    
    user_states[user.chat_id]['target_amount'] = message.text
    user_states[user.chat_id]['step'] = 'currency'
    
    bot.send_message(
        message.chat.id,
        "💱 **Select Currency**\n\nChoose the currency for your savings goal:",
        reply_markup=get_currency_keyboard()
    )


def get_savings_goal_custom_amount(message):
    """Get custom target amount"""
    user = get_user(message, get_savings_goal_custom_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    if not message.text.replace('.', '').isdigit():
        bot.register_next_step_handler(message, get_savings_goal_custom_amount)
        bot.send_message(message.chat.id, "❌ Please enter a valid number or type 'cancel' to cancel")
        return
    
    user_states[user.chat_id]['target_amount'] = message.text
    user_states[user.chat_id]['step'] = 'currency'
    
    bot.send_message(
        message.chat.id,
        "💱 **Select Currency**\n\nChoose the currency for your savings goal:",
        reply_markup=get_currency_keyboard()
    )


def add_contribution_step1(message, user):
    """Step 1: Select goal for contribution"""
    goals = user.savings_goals.filter(is_active=True, is_completed=False)
    
    if not goals.exists():
        bot.send_message(
            message.chat.id,
            "❌ You don't have any active savings goals to contribute to.",
            reply_markup=get_keyboard()
        )
        return
    
    keyboard = InlineKeyboardMarkup()
    for goal in goals:
        keyboard.add(InlineKeyboardButton(
            f"🎯 {goal.name} ({format_currency(goal.current_amount, goal.currency)}/{format_currency(goal.target_amount, goal.currency)})",
            callback_data=f"goal_contribute_{goal.id}"
        ))
    keyboard.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
    
    bot.send_message(
        message.chat.id,
        "💰 **Add Contribution**\n\nSelect the goal you want to contribute to:",
        reply_markup=keyboard
    )


def handle_goal_contribution(message, user, goal_id):
    """Handle goal contribution"""
    try:
        goal = user.savings_goals.get(id=goal_id)
        user_states[user.chat_id] = {
            'action': 'add_contribution',
            'goal_id': goal_id,
            'step': 'amount'
        }
        
        # Create a custom keyboard for contribution amount
        keyboard = get_savings_amount_keyboard(["50", "100", "200", "500", "1000", "2000"])
        
        bot.send_message(
            message.chat.id,
            f"💰 **Add to {goal.name}**\n\nHow much do you want to contribute?",
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, get_contribution_amount)
        
    except SavingsGoal.DoesNotExist:
        bot.send_message(
            message.chat.id,
            "❌ Goal not found.",
            reply_markup=get_keyboard()
        )


def get_contribution_amount(message):
    """Get contribution amount"""
    user = get_user(message, get_contribution_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text == msg_cancel:
        handle_cancel(message, user)
        return
    
    if message.text == "Custom":
        bot.register_next_step_handler(message, get_contribution_custom_amount)
        bot.send_message(message.chat.id, "💵 Enter the contribution amount (or type 'cancel' to cancel):")
        return
    
    if not message.text.isdigit():
        bot.register_next_step_handler(message, get_contribution_amount)
        bot.send_message(message.chat.id, "❌ Please enter only numbers or use 'Cancel' to cancel")
        return
    
    user_states[user.chat_id]['amount'] = message.text
    user_states[user.chat_id]['step'] = 'description'
    
    bot.send_message(
        message.chat.id,
        "📝 **Contribution Description** (optional)\n\nAdd a note about this contribution (or type 'skip' to skip):",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(message, get_contribution_description)


def get_contribution_custom_amount(message):
    """Get custom contribution amount"""
    user = get_user(message, get_contribution_custom_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    if not message.text.replace('.', '').isdigit():
        bot.register_next_step_handler(message, get_contribution_custom_amount)
        bot.send_message(message.chat.id, "❌ Please enter a valid number or type 'cancel' to cancel")
        return
    
    user_states[user.chat_id]['amount'] = message.text
    user_states[user.chat_id]['step'] = 'description'
    
    bot.send_message(
        message.chat.id,
        "📝 **Contribution Description** (optional)\n\nAdd a note about this contribution (or type 'skip' to skip):",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(message, get_contribution_description)


def get_contribution_description(message):
    """Get contribution description and save"""
    user = get_user(message, get_contribution_description)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    state = user_states[user.chat_id]
    description = message.text if message.text.lower() != 'skip' else ''
    
    try:
        goal = user.savings_goals.get(id=state['goal_id'])
        
        # Create contribution
        contribution = SavingsContribution.objects.create(
            savings_goal=goal,
            amount=Decimal(state['amount']),
            description=description
        )
        
        # Update user streak
        update_user_streak(user)
        
        # Check if goal is completed
        if goal.is_completed:
            completion_msg = f"\n🎉 **GOAL COMPLETED!** 🎉\nCongratulations! You've reached your savings goal for {goal.name}!"
        else:
            completion_msg = ""
        
        msg = f"""
✅ **Contribution Added Successfully!**

🎯 **Goal**: {goal.name}
💰 **Amount**: {format_currency(contribution.amount, goal.currency)}
📝 **Note**: {description or 'No description'}
📊 **Progress**: {get_savings_goal_progress_bar(goal)}

{completion_msg}
        """
        
        bot.send_message(message.chat.id, msg, reply_markup=get_keyboard())
        
        # Clear user state
        if user.chat_id in user_states:
            del user_states[user.chat_id]
            
    except SavingsGoal.DoesNotExist:
        bot.send_message(message.chat.id, "❌ Goal not found.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error adding contribution: {str(e)}")


def show_goal_details(message, user):
    """Show detailed goal information"""
    goals = user.savings_goals.filter(is_active=True)
    
    if not goals.exists():
        bot.send_message(
            message.chat.id,
            "❌ You don't have any savings goals.",
            reply_markup=get_keyboard()
        )
        return
    
    keyboard = InlineKeyboardMarkup()
    for goal in goals:
        keyboard.add(InlineKeyboardButton(
            f"📊 {goal.name}",
            callback_data=f"goal_select_{goal.id}"
        ))
    keyboard.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
    
    bot.send_message(
        message.chat.id,
        "📊 **Goal Details**\n\nSelect a goal to view detailed information:",
        reply_markup=keyboard
    )


def handle_goal_selection(message, user, goal_id):
    """Handle goal selection for details"""
    try:
        goal = user.savings_goals.get(id=goal_id)
        
        # Get recent contributions
        recent_contributions = goal.contributions.order_by('-created_at')[:5]
        
        msg = f"""
📊 **Goal Details: {goal.name}**

💰 **Target**: {format_currency(goal.target_amount, goal.currency)}
💵 **Current**: {format_currency(goal.current_amount, goal.currency)}
📈 **Progress**: {get_savings_goal_progress_bar(goal)}
🎯 **Remaining**: {format_currency(goal.remaining_amount, goal.currency)}

📅 **Created**: {goal.created_at.strftime('%Y-%m-%d')}
        """
        
        if goal.target_date:
            msg += f"📅 **Target Date**: {goal.target_date.strftime('%Y-%m-%d')}\n"
            
            daily_needed = calculate_daily_savings_needed(goal)
            if daily_needed and daily_needed > 0:
                msg += f"📊 **Daily Needed**: {format_currency(daily_needed, goal.currency)}\n"
        
        if goal.description:
            msg += f"\n📝 **Description**: {goal.description}\n"
        
        if recent_contributions.exists():
            msg += f"\n💰 **Recent Contributions**:\n"
            for contrib in recent_contributions:
                msg += f"• {format_currency(contrib.amount, goal.currency)} - {contrib.created_at.strftime('%Y-%m-%d')}\n"
                if contrib.description:
                    msg += f"  📝 {contrib.description}\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("💰 Add Contribution", callback_data=f"goal_contribute_{goal.id}"),
            InlineKeyboardButton("❌ Close", callback_data="cancel_action"),
        )
        
        bot.send_message(message.chat.id, msg, reply_markup=keyboard)
        
    except SavingsGoal.DoesNotExist:
        bot.send_message(
            message.chat.id,
            "❌ Goal not found.",
            reply_markup=get_keyboard()
        )


def generate_report(message, user, period):
    """Generate financial report for specified period"""
    start_date, end_date = get_date_range(period)
    
    # Get expenses
    expenses = user.expenses.filter(created_at__range=[start_date, end_date])
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Get income
    income = user.incomes.filter(created_at__range=[start_date, end_date])
    total_income = income.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Calculate net
    net_amount = total_income - total_expenses
    
    # Get expense breakdown by category
    expense_breakdown = expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Create pie chart
    if expense_breakdown:
        labels = [item['category'] for item in expense_breakdown]
        sizes = [float(item['total']) for item in expense_breakdown]
        img = get_pie(sizes, labels)
        
        msg = f"""
📊 **{period.title()} Report**

💰 **Total Income**: {format_currency(total_income, user.default_currency)}
💸 **Total Expenses**: {format_currency(total_expenses, user.default_currency)}
📈 **Net Amount**: {format_currency(net_amount, user.default_currency)}

📅 **Period**: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}
        """
        
        bot.send_photo(message.chat.id, photo=img, caption=msg)
    else:
        msg = f"""
📊 **{period.title()} Report**

💰 **Total Income**: {format_currency(total_income, user.default_currency)}
💸 **Total Expenses**: {format_currency(total_expenses, user.default_currency)}
📈 **Net Amount**: {format_currency(net_amount, user.default_currency)}

📅 **Period**: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}

ℹ️ No expenses recorded for this period.
        """
        
        bot.send_message(message.chat.id, msg)


def claim_streak_reward(message, user):
    """Claim streak reward"""
    if user.streak_count < 1:
        bot.send_message(message.chat.id, "❌ You need at least 1 day streak to claim rewards!")
        return
    
    reward = calculate_streak_reward(user.streak_count)
    
    # Add reward as income
    Income.objects.create(
        user=user,
        amount=reward,
        reason=f"Streak Reward ({user.streak_count} days)",
        currency=user.default_currency
    )
    
    # Update user's total earned
    user.total_earned_from_streaks += reward
    user.save()
    
    msg = f"""
🎉 **Reward Claimed!**

💰 **Amount**: {format_currency(reward, user.default_currency)}
🔥 **Streak**: {user.streak_count} days
💎 **Total Earned**: {format_currency(user.total_earned_from_streaks, user.default_currency)}

Keep up the great work! 🚀
    """
    
    bot.send_message(message.chat.id, msg)


######################## Telegram Contact Submit ########################################
@bot.message_handler(content_types=["contact"])
def contact_handler(message, func=None):
    con = message.contact
    data = {
        "username": message.from_user.id,
        "chat_id": message.chat.id,
        "phone_number": con.phone_number.replace("+", ""),
    }
    print(con)

    contact, iscreated = User.objects.get_or_create(**data)
    contact.first_name = con.first_name
    contact.last_name = con.last_name
    contact.save()

    # Initialize default categories
    get_default_expense_categories()

    if iscreated:
        msg1 = bot.send_message(
            message.chat.id, "Contact Received✅ Welcome to your expense tracker!", reply_markup=get_keyboard()
        )
    else:
        msg1 = bot.send_message(
            message.chat.id, "Contact Updated Successfully✅", reply_markup=get_keyboard()
        )

    time.sleep(0.5)

    bot.delete_message(message.chat.id, msg1.id)

    if func:
        func(message)


def create_savings_goal_final(message, user):
    """Create the savings goal after all data is collected"""
    if user.chat_id not in user_states:
        return
    
    state = user_states[user.chat_id]
    
    try:
        # Create the savings goal
        goal = SavingsGoal.objects.create(
            user=user,
            name=state['name'],
            target_amount=Decimal(state['target_amount']),
            currency=state['currency']
        )
        
        # Update user streak
        update_user_streak(user)
        
        msg = f"""
🎉 **Savings Goal Created Successfully!**

🎯 **Goal**: {goal.name}
💰 **Target**: {format_currency(goal.target_amount, goal.currency)}
💵 **Current**: {format_currency(goal.current_amount, goal.currency)}
📈 **Progress**: {get_savings_goal_progress_bar(goal)}

📅 **Created**: {goal.created_at.strftime('%Y-%m-%d')}

Start contributing to reach your goal! 💪
        """
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("💰 Add First Contribution", callback_data=f"goal_contribute_{goal.id}"),
            InlineKeyboardButton("📊 View Goals", callback_data="view_goals"),
        )
        
        bot.send_message(message.chat.id, msg, reply_markup=keyboard)
        
        # Clear user state
        if user.chat_id in user_states:
            del user_states[user.chat_id]
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error creating savings goal: {str(e)}")


def create_debt_final(message, user):
    """Create the debt after all data is collected"""
    if user.chat_id not in user_states:
        return
    
    state = user_states[user.chat_id]
    
    try:
        # Create the debt (negative amount)
        debt = Owe.objects.create(
            user=user,
            name=state['name'],
            amount=Decimal(state['amount']) * -1,  # Negative for debt
            currency=state['currency']
        )
        
        # Update user streak
        update_user_streak(user)
        
        msg = f"""
✅ **Debt Added Successfully!**

💸 **Debt**: {debt.name}
💰 **Amount**: {format_currency(abs(debt.amount), debt.currency)}
📅 **Created**: {debt.created_at.strftime('%Y-%m-%d')}

Start making payments to reduce your debt! 💪
        """
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("💳 Make Payment", callback_data=f"debt_pay_{debt.id}"),
            InlineKeyboardButton("📊 View Debts", callback_data="debt_details"),
        )
        
        bot.send_message(message.chat.id, msg, reply_markup=keyboard)
        
        # Clear user state
        if user.chat_id in user_states:
            del user_states[user.chat_id]
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error creating debt: {str(e)}")


def create_owe_final(message, user):
    """Create the owe after all data is collected"""
    if user.chat_id not in user_states:
        return
    
    state = user_states[user.chat_id]
    
    try:
        # Create the owe (positive amount)
        owe = Owe.objects.create(
            user=user,
            name=state['name'],
            amount=Decimal(state['amount']),  # Positive for owe
            currency=state['currency']
        )
        
        # Update user streak
        update_user_streak(user)
        
        msg = f"""
✅ **Owe Added Successfully!**

💵 **Person**: {owe.name}
💰 **Amount**: {format_currency(owe.amount, owe.currency)}
📅 **Created**: {owe.created_at.strftime('%Y-%m-%d')}

Track when you collect money from them! 💰
        """
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("💰 Collect Money", callback_data=f"owe_collect_{owe.id}"),
            InlineKeyboardButton("📊 View Owes", callback_data="owe_details"),
        )
        
        bot.send_message(message.chat.id, msg, reply_markup=keyboard)
        
        # Clear user state
        if user.chat_id in user_states:
            del user_states[user.chat_id]
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error creating owe: {str(e)}")


def pay_debt_step1(message, user):
    """Step 1: Select debt to pay"""
    debts = user.debts.filter(amount__lt=0)
    
    if not debts.exists():
        bot.send_message(
            message.chat.id,
            "❌ You don't have any debts to pay.",
            reply_markup=get_keyboard()
        )
        return
    
    keyboard = InlineKeyboardMarkup()
    for debt in debts:
        keyboard.add(InlineKeyboardButton(
            f"💸 {debt.name} ({format_currency(abs(debt.amount), debt.currency)})",
            callback_data=f"debt_pay_{debt.id}"
        ))
    keyboard.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
    
    bot.send_message(
        message.chat.id,
        "💳 **Pay Debt**\n\nSelect the debt you want to make a payment for:",
        reply_markup=keyboard
    )


def handle_debt_payment(message, user, debt_id):
    """Handle debt payment"""
    try:
        debt = user.debts.get(id=debt_id)
        user_states[user.chat_id] = {
            'action': 'pay_debt',
            'debt_id': debt_id,
            'step': 'amount'
        }
        
        # Create a custom keyboard for payment amount
        keyboard = get_savings_amount_keyboard(["50", "100", "200", "500", "1000"])
        
        bot.send_message(
            message.chat.id,
            f"💳 **Pay {debt.name}**\n\nHow much do you want to pay?",
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, get_debt_payment_amount)
        
    except Owe.DoesNotExist:
        bot.send_message(
            message.chat.id,
            "❌ Debt not found.",
            reply_markup=get_keyboard()
        )


def get_debt_payment_amount(message):
    """Get debt payment amount"""
    user = get_user(message, get_debt_payment_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text == msg_cancel:
        handle_cancel(message, user)
        return
    
    if message.text == "Custom":
        bot.register_next_step_handler(message, get_debt_payment_custom_amount)
        bot.send_message(message.chat.id, "💵 Enter the payment amount (or type 'cancel' to cancel):")
        return
    
    if not message.text.isdigit():
        bot.register_next_step_handler(message, get_debt_payment_amount)
        bot.send_message(message.chat.id, "❌ Please enter only numbers or use 'Cancel' to cancel")
        return
    
    user_states[user.chat_id]['amount'] = message.text
    user_states[user.chat_id]['step'] = 'description'
    
    bot.send_message(
        message.chat.id,
        "📝 **Payment Description** (optional)\n\nAdd a note about this payment (or type 'skip' to skip):",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(message, get_debt_payment_description)


def get_debt_payment_custom_amount(message):
    """Get custom debt payment amount"""
    user = get_user(message, get_debt_payment_custom_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    if not message.text.replace('.', '').isdigit():
        bot.register_next_step_handler(message, get_debt_payment_custom_amount)
        bot.send_message(message.chat.id, "❌ Please enter a valid number or type 'cancel' to cancel")
        return
    
    user_states[user.chat_id]['amount'] = message.text
    user_states[user.chat_id]['step'] = 'description'
    
    bot.send_message(
        message.chat.id,
        "📝 **Payment Description** (optional)\n\nAdd a note about this payment (or type 'skip' to skip):",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(message, get_debt_payment_description)


def get_debt_payment_description(message):
    """Get debt payment description and save"""
    user = get_user(message, get_debt_payment_description)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    state = user_states[user.chat_id]
    description = message.text if message.text.lower() != 'skip' else ''
    
    try:
        debt = user.debts.get(id=state['debt_id'])
        
        # Create payment
        payment = DebtPayment.objects.create(
            owe=debt,
            amount=Decimal(state['amount']),
            description=description
        )
        
        # Update user streak
        update_user_streak(user)
        
        # Check if debt is fully paid
        if debt.amount >= 0:
            completion_msg = f"\n🎉 **DEBT PAID OFF!** 🎉\nCongratulations! You've fully paid off your debt to {debt.name}!"
        else:
            completion_msg = ""
        
        msg = f"""
✅ **Payment Added Successfully!**

💸 **Debt**: {debt.name}
💰 **Payment**: {format_currency(payment.amount, debt.currency)}
📝 **Note**: {description or 'No description'}
💳 **Remaining**: {format_currency(abs(debt.amount), debt.currency)}

{completion_msg}
        """
        
        bot.send_message(message.chat.id, msg, reply_markup=get_keyboard())
        
        # Clear user state
        if user.chat_id in user_states:
            del user_states[user.chat_id]
            
    except Owe.DoesNotExist:
        bot.send_message(message.chat.id, "❌ Debt not found.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error adding payment: {str(e)}")


def collect_owe_step1(message, user):
    """Step 1: Select owe to collect"""
    owes = user.debts.filter(amount__gt=0)
    
    if not owes.exists():
        bot.send_message(
            message.chat.id,
            "❌ No one owes you money right now.",
            reply_markup=get_keyboard()
        )
        return
    
    keyboard = InlineKeyboardMarkup()
    for owe in owes:
        keyboard.add(InlineKeyboardButton(
            f"💵 {owe.name} ({format_currency(owe.amount, owe.currency)})",
            callback_data=f"owe_collect_{owe.id}"
        ))
    keyboard.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
    
    bot.send_message(
        message.chat.id,
        "💰 **Collect Money**\n\nSelect the person you want to collect money from:",
        reply_markup=keyboard
    )


def handle_owe_collection(message, user, owe_id):
    """Handle owe collection"""
    try:
        owe = user.debts.get(id=owe_id)
        user_states[user.chat_id] = {
            'action': 'collect_owe',
            'owe_id': owe_id,
            'step': 'amount'
        }
        
        # Create a custom keyboard for collection amount
        keyboard = get_savings_amount_keyboard(["50", "100", "200", "500", "1000"])
        
        bot.send_message(
            message.chat.id,
            f"💰 **Collect from {owe.name}**\n\nHow much did you collect?",
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, get_owe_collection_amount)
        
    except Owe.DoesNotExist:
        bot.send_message(
            message.chat.id,
            "❌ Owe not found.",
            reply_markup=get_keyboard()
        )


def get_owe_collection_amount(message):
    """Get owe collection amount"""
    user = get_user(message, get_owe_collection_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text == msg_cancel:
        handle_cancel(message, user)
        return
    
    if message.text == "Custom":
        bot.register_next_step_handler(message, get_owe_collection_custom_amount)
        bot.send_message(message.chat.id, "💵 Enter the collection amount (or type 'cancel' to cancel):")
        return
    
    if not message.text.isdigit():
        bot.register_next_step_handler(message, get_owe_collection_amount)
        bot.send_message(message.chat.id, "❌ Please enter only numbers or use 'Cancel' to cancel")
        return
    
    user_states[user.chat_id]['amount'] = message.text
    user_states[user.chat_id]['step'] = 'description'
    
    bot.send_message(
        message.chat.id,
        "📝 **Collection Description** (optional)\n\nAdd a note about this collection (or type 'skip' to skip):",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(message, get_owe_collection_description)


def get_owe_collection_custom_amount(message):
    """Get custom owe collection amount"""
    user = get_user(message, get_owe_collection_custom_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    if not message.text.replace('.', '').isdigit():
        bot.register_next_step_handler(message, get_owe_collection_custom_amount)
        bot.send_message(message.chat.id, "❌ Please enter a valid number or type 'cancel' to cancel")
        return
    
    user_states[user.chat_id]['amount'] = message.text
    user_states[user.chat_id]['step'] = 'description'
    
    bot.send_message(
        message.chat.id,
        "📝 **Collection Description** (optional)\n\nAdd a note about this collection (or type 'skip' to skip):",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(message, get_owe_collection_description)


def get_owe_collection_description(message):
    """Get owe collection description and save"""
    user = get_user(message, get_owe_collection_description)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    state = user_states[user.chat_id]
    description = message.text if message.text.lower() != 'skip' else ''
    
    try:
        owe = user.debts.get(id=state['owe_id'])
        
        # Create collection
        collection = OweCollection.objects.create(
            owe=owe,
            amount=Decimal(state['amount']),
            description=description
        )
        
        # Update user streak
        update_user_streak(user)
        
        # Check if owe is fully collected
        if owe.amount <= 0:
            completion_msg = f"\n🎉 **FULLY COLLECTED!** 🎉\nCongratulations! You've collected all money from {owe.name}!"
        else:
            completion_msg = ""
        
        msg = f"""
✅ **Collection Added Successfully!**

💵 **From**: {owe.name}
💰 **Collected**: {format_currency(collection.amount, owe.currency)}
📝 **Note**: {description or 'No description'}
💳 **Remaining**: {format_currency(owe.amount, owe.currency)}

{completion_msg}
        """
        
        bot.send_message(message.chat.id, msg, reply_markup=get_keyboard())
        
        # Clear user state
        if user.chat_id in user_states:
            del user_states[user.chat_id]
            
    except Owe.DoesNotExist:
        bot.send_message(message.chat.id, "❌ Owe not found.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error adding collection: {str(e)}")


def show_debt_details(message, user):
    """Show detailed debt information"""
    debts = user.debts.filter(amount__lt=0)
    
    if not debts.exists():
        bot.send_message(
            message.chat.id,
            "❌ You don't have any debts.",
            reply_markup=get_keyboard()
        )
        return
    
    keyboard = InlineKeyboardMarkup()
    for debt in debts:
        keyboard.add(InlineKeyboardButton(
            f"📊 {debt.name}",
            callback_data=f"debt_select_{debt.id}"
        ))
    keyboard.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
    
    bot.send_message(
        message.chat.id,
        "📊 **Debt Details**\n\nSelect a debt to view detailed information:",
        reply_markup=keyboard
    )


def show_owe_details(message, user):
    """Show detailed owe information"""
    owes = user.debts.filter(amount__gt=0)
    
    if not owes.exists():
        bot.send_message(
            message.chat.id,
            "❌ No one owes you money.",
            reply_markup=get_keyboard()
        )
        return
    
    keyboard = InlineKeyboardMarkup()
    for owe in owes:
        keyboard.add(InlineKeyboardButton(
            f"📊 {owe.name}",
            callback_data=f"owe_select_{owe.id}"
        ))
    keyboard.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
    
    bot.send_message(
        message.chat.id,
        "📊 **Owe Details**\n\nSelect a person to view detailed information:",
        reply_markup=keyboard
    )


def add_new_debt_step1(message, user):
    """Step 1: Get debt name"""
    user_states[user.chat_id] = {
        'action': 'add_new_debt',
        'step': 'name'
    }
    
    bot.send_message(
        message.chat.id,
        "💸 **Add New Debt**\n\nWho do you owe money to?\n\nExample: Bank, Credit Card, Friend",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(message, get_new_debt_name)


def add_new_owe_step1(message, user):
    """Step 1: Get owe name"""
    user_states[user.chat_id] = {
        'action': 'add_new_owe',
        'step': 'name'
    }
    
    bot.send_message(
        message.chat.id,
        "💵 **Add New Owe**\n\nWho owes you money?\n\nExample: Friend, Colleague, Family",
        reply_markup=get_cancel_keyboard()
    )
    bot.register_next_step_handler(message, get_new_owe_name)


def get_new_debt_name(message):
    """Get new debt name"""
    user = get_user(message, get_new_debt_name)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    user_states[user.chat_id]['name'] = message.text
    user_states[user.chat_id]['step'] = 'amount'
    
    # Create a custom keyboard for debt amount
    keyboard = get_savings_amount_keyboard(["500", "1000", "2000", "5000", "10000"])
    
    bot.send_message(
        message.chat.id,
        f"💰 **Debt Amount**\n\nHow much do you owe to '{message.text}'?",
        reply_markup=keyboard
    )
    bot.register_next_step_handler(message, get_new_debt_amount)


def get_new_owe_name(message):
    """Get new owe name"""
    user = get_user(message, get_new_owe_name)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    user_states[user.chat_id]['name'] = message.text
    user_states[user.chat_id]['step'] = 'amount'
    
    # Create a custom keyboard for owe amount
    keyboard = get_savings_amount_keyboard(["500", "1000", "2000", "5000", "10000"])
    
    bot.send_message(
        message.chat.id,
        f"💰 **Owe Amount**\n\nHow much does '{message.text}' owe you?",
        reply_markup=keyboard
    )
    bot.register_next_step_handler(message, get_new_owe_amount)


def get_new_debt_amount(message):
    """Get new debt amount"""
    user = get_user(message, get_new_debt_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text == msg_cancel:
        handle_cancel(message, user)
        return
    
    if message.text == "Custom":
        bot.register_next_step_handler(message, get_new_debt_custom_amount)
        bot.send_message(message.chat.id, "💵 Enter the debt amount (or type 'cancel' to cancel):")
        return
    
    if not message.text.isdigit():
        bot.register_next_step_handler(message, get_new_debt_amount)
        bot.send_message(message.chat.id, "❌ Please enter only numbers or use 'Cancel' to cancel")
        return
    
    user_states[user.chat_id]['amount'] = message.text
    user_states[user.chat_id]['step'] = 'currency'
    
    bot.send_message(
        message.chat.id,
        "💱 **Select Currency**\n\nChoose the currency for this debt:",
        reply_markup=get_currency_keyboard()
    )


def get_new_owe_amount(message):
    """Get new owe amount"""
    user = get_user(message, get_new_owe_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text == msg_cancel:
        handle_cancel(message, user)
        return
    
    if message.text == "Custom":
        bot.register_next_step_handler(message, get_new_owe_custom_amount)
        bot.send_message(message.chat.id, "💵 Enter the owe amount (or type 'cancel' to cancel):")
        return
    
    if not message.text.isdigit():
        bot.register_next_step_handler(message, get_new_owe_amount)
        bot.send_message(message.chat.id, "❌ Please enter only numbers or use 'Cancel' to cancel")
        return
    
    user_states[user.chat_id]['amount'] = message.text
    user_states[user.chat_id]['step'] = 'currency'
    
    bot.send_message(
        message.chat.id,
        "💱 **Select Currency**\n\nChoose the currency for this owe:",
        reply_markup=get_currency_keyboard()
    )


def get_new_debt_custom_amount(message):
    """Get custom new debt amount"""
    user = get_user(message, get_new_debt_custom_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    if not message.text.replace('.', '').isdigit():
        bot.register_next_step_handler(message, get_new_debt_custom_amount)
        bot.send_message(message.chat.id, "❌ Please enter a valid number or type 'cancel' to cancel")
        return
    
    user_states[user.chat_id]['amount'] = message.text
    user_states[user.chat_id]['step'] = 'currency'
    
    bot.send_message(
        message.chat.id,
        "💱 **Select Currency**\n\nChoose the currency for this debt:",
        reply_markup=get_currency_keyboard()
    )


def get_new_owe_custom_amount(message):
    """Get custom new owe amount"""
    user = get_user(message, get_new_owe_custom_amount)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    # Handle cancel
    if message.text.lower() in ['cancel', 'c', msg_cancel]:
        handle_cancel(message, user)
        return
    
    if not message.text.replace('.', '').isdigit():
        bot.register_next_step_handler(message, get_new_owe_custom_amount)
        bot.send_message(message.chat.id, "❌ Please enter a valid number or type 'cancel' to cancel")
        return
    
    user_states[user.chat_id]['amount'] = message.text
    user_states[user.chat_id]['step'] = 'currency'
    
    bot.send_message(
        message.chat.id,
        "💱 **Select Currency**\n\nChoose the currency for this owe:",
        reply_markup=get_currency_keyboard()
    )


######################## Telegram Contact Submit ########################################
