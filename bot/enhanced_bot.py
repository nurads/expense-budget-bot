import time
import re
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from telebot import TeleBot
from telebot.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ChatJoinRequest,
)
from django.db.models import Sum, F, Value, Q
from django.utils import timezone

from .models import *
from .diagrams import *
from .utils import *


bot = TeleBot(settings.BOT_TOKEN, parse_mode="HTML", threaded=False)

# Message constants
msg_spent = "I Spent 😥"
msg_earnt = "I Earnt 😊"
msg_debt = "I am in Debt 😓"
msg_owe = "Someone owes me 🙄"
msg_reports = "📊 Reports"
msg_streaks = "🔥 Streaks"
msg_settings = "⚙️ Settings"
msg_categories = "📁 Categories"
msg_budget = "💰 Budget"

# User states for conversation flow
user_states = {}


def get_main_keyboard():
    """Get main keyboard with all options"""
    keyboard = ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    
    keyboard.add(
        KeyboardButton(msg_spent),
        KeyboardButton(msg_earnt),
        KeyboardButton(msg_debt),
        KeyboardButton(msg_owe),
    ).add(
        KeyboardButton(msg_reports),
        KeyboardButton(msg_streaks),
    ).add(
        KeyboardButton(msg_settings),
        KeyboardButton(msg_categories),
    )
    
    return keyboard


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
    
    return keyboard


def get_category_keyboard():
    """Get expense category keyboard"""
    keyboard = InlineKeyboardMarkup()
    categories = ExpenseCategory.objects.all()
    
    for i in range(0, len(categories), 2):
        row = []
        for j in range(2):
            if i + j < len(categories):
                category = categories[i + j]
                row.append(InlineKeyboardButton(
                    f"{category.emoji} {category.name}",
                    callback_data=f"category_{category.id}"
                ))
        keyboard.add(*row)
    
    return keyboard


def get_common_amount_keyboard():
    """Get common amount selection keyboard"""
    mark = ReplyKeyboardMarkup(
        row_width=3, 
        resize_keyboard=True, 
        one_time_keyboard=True, 
        is_persistent=False
    )
    
    amounts = ["100", "200", "500", "1000", "2000", "5000", "10000", "Custom"]
    for i in range(0, len(amounts), 3):
        row = amounts[i:i+3]
        mark.add(*[KeyboardButton(amount) for amount in row])
    
    return mark


def delete_message(message):
    """Delete a message"""
    try:
        return bot.delete_message(message.chat.id, message.id)
    except:
        pass


def get_user(message, func=None, *args):
    """Get or create user"""
    try:
        from_user = message.from_user
        user = User.objects.get(username=from_user.id)
        return user
    except User.DoesNotExist:
        # Request contact if user doesn't exist
        mark = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        mark.add(KeyboardButton("Share Contact", request_contact=True))
        bot.register_next_step_handler(message, contact_handler, func)
        bot.send_message(message.chat.id, "Please share your contact to get started 📱", reply_markup=mark)
        return None


def contact_handler(message, func=None):
    """Handle contact sharing"""
    try:
        con = message.contact
        data = {
            "username": message.from_user.id,
            "chat_id": message.chat.id,
            "phone_number": con.phone_number.replace("+", ""),
            "first_name": con.first_name,
            "last_name": con.last_name or "",
        }
        
        user, created = User.objects.get_or_create(
            username=message.from_user.id,
            defaults=data
        )
        
        if not created:
            # Update existing user
            for key, value in data.items():
                setattr(user, key, value)
            user.save()
        
        # Initialize default categories
        get_default_expense_categories()
        
        msg = "Contact received ✅ Welcome to your expense tracker!"
        bot.send_message(message.chat.id, msg, reply_markup=get_main_keyboard())
        
        if func:
            func(message)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Error processing contact: {str(e)}")


@bot.message_handler(commands=["start"])
def start(message):
    """Start command handler"""
    user = get_user(message, start)
    if not user:
        return
    
    welcome_msg = f"""
👋 Hello {user.first_name}!

Welcome to your personal expense tracker! 🎯

Here's what you can do:
• 📝 Track expenses and income
• 💰 Manage debts and loans
• 📊 View detailed reports
• 🔥 Build streaks to earn rewards
• 💱 Support multiple currencies
• 📁 Organize by categories

Let's start managing your finances! 💪
    """
    
    bot.send_message(message.chat.id, welcome_msg, reply_markup=get_main_keyboard())


@bot.message_handler(func=lambda msg: msg.text == msg_spent)
def handle_expense(message, amount=None, category_id=None, currency=None, reason=None):
    """Handle expense entry"""
    user = get_user(message, handle_expense)
    if not user:
        return
    
    if not amount:
        user_states[user.chat_id] = {'action': 'expense', 'step': 'amount'}
        bot.register_next_step_handler(message, get_amount_input)
        bot.send_message(
            message.chat.id,
            "💸 How much did you spend?",
            reply_markup=get_common_amount_keyboard()
        )
        return
    
    if not category_id:
        user_states[user.chat_id] = {'action': 'expense', 'step': 'category', 'amount': amount}
        bot.send_message(
            message.chat.id,
            "📁 Select a category:",
            reply_markup=get_category_keyboard()
        )
        return
    
    if not currency:
        user_states[user.chat_id] = {'action': 'expense', 'step': 'currency', 'amount': amount, 'category_id': category_id}
        bot.send_message(
            message.chat.id,
            "💱 Select currency:",
            reply_markup=get_currency_keyboard()
        )
        return
    
    if not reason:
        user_states[user.chat_id] = {'action': 'expense', 'step': 'reason', 'amount': amount, 'category_id': category_id, 'currency': currency}
        bot.register_next_step_handler(message, get_text_input)
        bot.send_message(message.chat.id, "📝 What did you spend on?")
        return
    
    # Create expense
    try:
        category = ExpenseCategory.objects.get(id=category_id)
        expense = Expense.objects.create(
            user=user,
            amount=Decimal(amount),
            reason=reason,
            category=category.name,
            currency=currency
        )
        
        # Update user streak
        update_user_streak(user)
        
        # Convert to user's default currency for display
        converted_amount = convert_currency(expense.amount, currency, user.default_currency)
        
        # Get total expenses for the month
        start_date, end_date = get_date_range('monthly')
        monthly_expenses = user.expenses.filter(
            created_at__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        msg = f"""
💸 **Expense Added Successfully!**

💰 **Amount**: {format_currency(expense.amount, currency)}
🔄 **Converted**: {format_currency(converted_amount, user.default_currency)}
📁 **Category**: {category.emoji} {category.name}
📝 **Reason**: {reason}
📅 **Date**: {expense.created_at.strftime('%Y-%m-%d %H:%M')}

📊 **Monthly Total**: {format_currency(monthly_expenses, user.default_currency)}
        """
        
        bot.send_message(message.chat.id, msg, reply_markup=get_main_keyboard())
        
        # Clear user state
        if user.chat_id in user_states:
            del user_states[user.chat_id]
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error adding expense: {str(e)}")


@bot.message_handler(func=lambda msg: msg.text == msg_earnt)
def handle_income(message, amount=None, currency=None, reason=None):
    """Handle income entry"""
    user = get_user(message, handle_income)
    if not user:
        return
    
    if not amount:
        user_states[user.chat_id] = {'action': 'income', 'step': 'amount'}
        bot.register_next_step_handler(message, get_amount_input)
        bot.send_message(
            message.chat.id,
            "💰 How much did you earn?",
            reply_markup=get_common_amount_keyboard()
        )
        return
    
    if not currency:
        user_states[user.chat_id] = {'action': 'income', 'step': 'currency', 'amount': amount}
        bot.send_message(
            message.chat.id,
            "💱 Select currency:",
            reply_markup=get_currency_keyboard()
        )
        return
    
    if not reason:
        user_states[user.chat_id] = {'action': 'income', 'step': 'reason', 'amount': amount, 'currency': currency}
        bot.register_next_step_handler(message, get_text_input)
        bot.send_message(message.chat.id, "📝 What was the source of income?")
        return
    
    # Create income
    try:
        income = Income.objects.create(
            user=user,
            amount=Decimal(amount),
            reason=reason,
            currency=currency
        )
        
        # Update user streak
        update_user_streak(user)
        
        # Convert to user's default currency for display
        converted_amount = convert_currency(income.amount, currency, user.default_currency)
        
        # Get total income for the month
        start_date, end_date = get_date_range('monthly')
        monthly_income = user.incomes.filter(
            created_at__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        msg = f"""
💰 **Income Added Successfully!**

💵 **Amount**: {format_currency(income.amount, currency)}
🔄 **Converted**: {format_currency(converted_amount, user.default_currency)}
📝 **Source**: {reason}
📅 **Date**: {income.created_at.strftime('%Y-%m-%d %H:%M')}

📊 **Monthly Total**: {format_currency(monthly_income, user.default_currency)}
        """
        
        bot.send_message(message.chat.id, msg, reply_markup=get_main_keyboard())
        
        # Clear user state
        if user.chat_id in user_states:
            del user_states[user.chat_id]
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error adding income: {str(e)}")


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
    )
    
    bot.send_message(message.chat.id, msg, reply_markup=keyboard)


def get_amount_input(message):
    """Handle amount input"""
    user = get_user(message)
    if not user or user.chat_id not in user_states:
        return
    
    state = user_states[user.chat_id]
    delete_message(message)
    
    if message.text == "Custom":
        bot.register_next_step_handler(message, get_custom_amount)
        bot.send_message(message.chat.id, "💵 Enter the amount:")
        return
    
    if not message.text.isdigit():
        bot.register_next_step_handler(message, get_amount_input)
        bot.send_message(message.chat.id, "❌ Please enter only numbers")
        return
    
    amount = message.text
    action = state['action']
    
    if action == 'expense':
        handle_expense(message, amount=amount)
    elif action == 'income':
        handle_income(message, amount=amount)


def get_custom_amount(message):
    """Handle custom amount input"""
    user = get_user(message)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    
    if not message.text.replace('.', '').isdigit():
        bot.register_next_step_handler(message, get_custom_amount)
        bot.send_message(message.chat.id, "❌ Please enter a valid number")
        return
    
    amount = message.text
    state = user_states[user.chat_id]
    action = state['action']
    
    if action == 'expense':
        handle_expense(message, amount=amount)
    elif action == 'income':
        handle_income(message, amount=amount)


def get_text_input(message):
    """Handle text input for reason/description"""
    user = get_user(message)
    if not user or user.chat_id not in user_states:
        return
    
    delete_message(message)
    text = message.text
    state = user_states[user.chat_id]
    action = state['action']
    
    if action == 'expense':
        handle_expense(
            message, 
            amount=state['amount'],
            category_id=state['category_id'],
            currency=state['currency'],
            reason=text
        )
    elif action == 'income':
        handle_income(
            message,
            amount=state['amount'],
            currency=state['currency'],
            reason=text
        )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle callback queries"""
    user = get_user(call.message)
    if not user:
        return
    
    data = call.data
    bot.answer_callback_query(call.id)
    
    if data.startswith('currency_'):
        currency = data.split('_')[1]
        if user.chat_id in user_states:
            state = user_states[user.chat_id]
            state['currency'] = currency
            
            if state['action'] == 'expense':
                handle_expense(
                    call.message,
                    amount=state['amount'],
                    category_id=state['category_id'],
                    currency=currency
                )
            elif state['action'] == 'income':
                handle_income(
                    call.message,
                    amount=state['amount'],
                    currency=currency
                )
    
    elif data.startswith('category_'):
        category_id = int(data.split('_')[1])
        if user.chat_id in user_states:
            state = user_states[user.chat_id]
            state['category_id'] = category_id
            handle_expense(
                call.message,
                amount=state['amount'],
                category_id=category_id
            )
    
    elif data.startswith('report_'):
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


# Legacy handlers for backward compatibility
@bot.message_handler(commands=["spends"])
def legacy_spends(message):
    """Legacy spends command"""
    user = get_user(message, legacy_spends)
    if not user:
        return
    
    # Get expenses from last 30 days
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
    msg = f"💸 Total spent: {format_currency(Decimal(str(total)), user.default_currency)}"
    
    bot.send_photo(message.chat.id, photo=img, caption=msg)


@bot.message_handler(commands=["earnings"])
def legacy_earnings(message):
    """Legacy earnings command"""
    user = get_user(message, legacy_earnings)
    if not user:
        return
    
    # Get income from last 30 days
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
    msg = f"💰 Total earned: {format_currency(Decimal(str(total)), user.default_currency)}"
    
    bot.send_photo(message.chat.id, photo=img, caption=msg)


@bot.message_handler(content_types=["contact"])
def contact_handler_legacy(message):
    """Legacy contact handler"""
    contact_handler(message)
