import requests
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from django.utils import timezone
from forex_python.converter import CurrencyRates
from .models import CurrencyRate, User, ExpenseCategory
from django.db import models

def get_currency_rate(from_currency, to_currency):
    """Get currency exchange rate, with caching"""
    if from_currency == to_currency:
        return Decimal('1.0')
    
    try:
        # Try to get from database first
        rate_obj = CurrencyRate.objects.get(
            from_currency=from_currency,
            to_currency=to_currency
        )
        
        # Check if rate is older than 1 hour
        if timezone.now() - rate_obj.last_updated > timedelta(hours=1):
            # Update rate
            c = CurrencyRates()
            new_rate = c.get_rate(from_currency, to_currency)
            rate_obj.rate = Decimal(str(new_rate))
            rate_obj.save()
            return rate_obj.rate
        else:
            return rate_obj.rate
            
    except CurrencyRate.DoesNotExist:
        # Create new rate entry
        try:
            c = CurrencyRates()
            rate = c.get_rate(from_currency, to_currency)
            CurrencyRate.objects.create(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=Decimal(str(rate))
            )
            return Decimal(str(rate))
        except Exception as e:
            print(f"Error getting currency rate: {e}")
            return Decimal('1.0')


def convert_currency(amount, from_currency, to_currency):
    """Convert amount from one currency to another"""
    if from_currency == to_currency:
        return amount
    
    rate = get_currency_rate(from_currency, to_currency)
    converted_amount = amount * rate
    return converted_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def format_currency(amount, currency):
    """Format amount with currency symbol"""
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'ETB': 'ETB',
        'JPY': '¥',
        'CAD': 'C$',
        'AUD': 'A$',
        'CHF': 'CHF',
        'CNY': '¥',
        'INR': '₹',
    }
    
    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{float(amount):,.2f}"


def get_default_expense_categories():
    """Get default expense categories"""
    categories = [
        ('🍔', 'Food & Dining'),
        ('🚗', 'Transportation'),
        ('🏠', 'Housing'),
        ('🛒', 'Shopping'),
        ('💊', 'Healthcare'),
        ('🎬', 'Entertainment'),
        ('📚', 'Education'),
        ('⚡', 'Utilities'),
        ('👕', 'Clothing'),
        ('✈️', 'Travel'),
        ('💳', 'Other'),
    ]
    
    for emoji, name in categories:
        ExpenseCategory.objects.get_or_create(
            name=name,
            defaults={'emoji': emoji, 'description': f'Expenses related to {name.lower()}'}
        )


def calculate_streak_reward(streak_count):
    """Calculate reward amount based on streak count"""
    base_reward = Decimal('10.0')  # Base reward in user's default currency
    multiplier = min(streak_count / 7, 5)  # Max 5x multiplier for 35+ day streaks
    return base_reward * Decimal(str(multiplier))


def get_date_range(period):
    """Get date range for different periods"""
    now = timezone.now()
    
    if period == 'daily':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif period == 'weekly':
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(weeks=1)
    elif period == 'monthly':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
    elif period == 'yearly':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(year=start_date.year + 1)
    else:
        start_date = now - timedelta(days=30)
        end_date = now
    
    return start_date, end_date


def update_user_streak(user):
    """Update user's streak count based on activity"""
    today = timezone.now().date()
    
    if user.last_activity_date is None:
        # First time user
        user.streak_count = 1
        user.last_activity_date = today
    elif user.last_activity_date == today:
        # Already updated today
        return
    elif user.last_activity_date == today - timedelta(days=1):
        # Consecutive day
        user.streak_count += 1
        user.last_activity_date = today
    else:
        # Streak broken
        user.streak_count = 1
        user.last_activity_date = today
    
    user.save()


def get_available_currencies():
    """Get list of available currencies"""
    return [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('ETB', 'Ethiopian Birr'),
        ('JPY', 'Japanese Yen'),
        ('CAD', 'Canadian Dollar'),
        ('AUD', 'Australian Dollar'),
        ('CHF', 'Swiss Franc'),
        ('CNY', 'Chinese Yuan'),
        ('INR', 'Indian Rupee'),
    ]


def get_savings_goal_progress_bar(goal):
    """Generate a visual progress bar for savings goal"""
    progress = goal.progress_percentage
    filled_blocks = int(progress / 10)  # 10 blocks total
    empty_blocks = 10 - filled_blocks
    
    bar = "🟩" * filled_blocks + "⬜" * empty_blocks
    return f"{bar} {progress:.1f}%"


def calculate_daily_savings_needed(goal):
    """Calculate daily savings needed to reach goal by target date"""
    if not goal.target_date:
        return None
    
    from django.utils import timezone
    today = timezone.now().date()
    days_remaining = (goal.target_date - today).days
    
    if days_remaining <= 0:
        return 0
    
    return goal.remaining_amount / days_remaining


def get_savings_goal_status_emoji(goal):
    """Get appropriate emoji for goal status"""
    if goal.is_completed:
        return "🎉"
    elif goal.is_overdue:
        return "⚠️"
    elif goal.progress_percentage >= 75:
        return "🔥"
    elif goal.progress_percentage >= 50:
        return "💪"
    elif goal.progress_percentage >= 25:
        return "📈"
    else:
        return "🎯"


def get_total_debt(user):
    """Calculate total debt amount for user"""
    from .models import Owe
    total_debt = Owe.objects.filter(user=user, amount__lt=0).aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0')
    return abs(total_debt)  # Return positive amount


def get_total_owe(user):
    """Calculate total amount owed to user"""
    from .models import Owe
    total_owe = Owe.objects.filter(user=user, amount__gt=0).aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0')
    return total_owe


def get_debt_summary(user):
    """Get detailed debt summary for user"""
    from .models import Owe
    debts = Owe.objects.filter(user=user, amount__lt=0).order_by('amount')
    
    summary = {
        'total_debt': get_total_debt(user),
        'debt_count': debts.count(),
        'debts': debts,
        'currency': user.default_currency
    }
    
    return summary


def get_owe_summary(user):
    """Get detailed owe summary for user"""
    from .models import Owe
    owes = Owe.objects.filter(user=user, amount__gt=0).order_by('-amount')
    
    summary = {
        'total_owe': get_total_owe(user),
        'owe_count': owes.count(),
        'owes': owes,
        'currency': user.default_currency
    }
    
    return summary


def get_debt_progress_bar(debt_amount, original_amount):
    """Generate progress bar for debt payment"""
    if original_amount == 0:
        return "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100%"
    
    paid_percentage = ((original_amount - abs(debt_amount)) / original_amount) * 100
    filled_blocks = int(paid_percentage / 10)
    empty_blocks = 10 - filled_blocks
    
    bar = "🟩" * filled_blocks + "⬜" * empty_blocks
    return f"{bar} {paid_percentage:.1f}%"
