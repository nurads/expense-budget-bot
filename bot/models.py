from typing import Any
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    def create(self, **kwargs: Any) -> Any:
        return super().create(**kwargs)

    def create_superuser(self, **kwargs):
        user = self.create(**kwargs)
        user.is_staff = True
        user.is_superuser = True

        user.save()

        return user


class User(AbstractUser):
    phone_number = models.CharField()
    chat_id = models.BigIntegerField(unique=True, null=True, blank=True)
    last_name = models.CharField(null=True, blank=True)
    default_currency = models.CharField(max_length=3, default="ETB")
    timezone = models.CharField(max_length=50, default="UTC")
    streak_count = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    total_earned_from_streaks = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)
    category = models.CharField(max_length=100, default="Other")
    currency = models.CharField(max_length=3, default="ETB")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.reason}: {self.amount} {self.currency}"


class Owe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="debts")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=255)
    currency = models.CharField(max_length=3, default="ETB")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="incomes")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)
    currency = models.CharField(max_length=3, default="ETB")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.reason}: {self.amount} {self.currency}"


class Streak(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="streaks")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    current = models.PositiveIntegerField()
    deadline = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=255)
    currency = models.CharField(max_length=3, default="ETB")
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name}: {self.current}/{self.amount} {self.currency}"


class CurrencyRate(models.Model):
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=10, decimal_places=6)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('from_currency', 'to_currency')

    def __str__(self) -> str:
        return f"{self.from_currency}/{self.to_currency}: {self.rate}"


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    emoji = models.CharField(max_length=5, default="📁")
    description = models.TextField(blank=True)
    
    def __str__(self) -> str:
        return f"{self.emoji} {self.name}"


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="ETB")
    period = models.CharField(max_length=20, choices=[
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ], default='monthly')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.category.name}: {self.amount} {self.currency} ({self.period})"


class SavingsGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="savings_goals")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="ETB")
    target_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name}: {self.current_amount}/{self.target_amount} {self.currency}"

    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.target_amount == 0:
            return 0
        return (self.current_amount / self.target_amount) * 100

    @property
    def remaining_amount(self):
        """Calculate remaining amount to reach goal"""
        return max(0, self.target_amount - self.current_amount)

    @property
    def is_overdue(self):
        """Check if goal is overdue"""
        if not self.target_date:
            return False
        from django.utils import timezone
        return timezone.now().date() > self.target_date and not self.is_completed


class SavingsContribution(models.Model):
    savings_goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name="contributions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.savings_goal.name}: {self.amount} {self.savings_goal.currency}"

    def save(self, *args, **kwargs):
        """Override save to update goal's current amount"""
        super().save(*args, **kwargs)
        # Update the goal's current amount
        total_contributions = self.savings_goal.contributions.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        self.savings_goal.current_amount = total_contributions
        
        # Check if goal is completed
        if self.savings_goal.current_amount >= self.savings_goal.target_amount:
            self.savings_goal.is_completed = True
        else:
            self.savings_goal.is_completed = False
            
        self.savings_goal.save()


class DebtPayment(models.Model):
    """Track payments made towards debts"""
    owe = models.ForeignKey(Owe, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Payment to {self.owe.name}: {self.amount} {self.owe.currency}"

    def save(self, *args, **kwargs):
        """Override save to update debt amount"""
        super().save(*args, **kwargs)
        # Update the debt amount (reduce it by payment)
        self.owe.amount += self.amount  # Since debt amounts are negative, adding payment reduces debt
        self.owe.save()


class OweCollection(models.Model):
    """Track money collected from people who owe you"""
    owe = models.ForeignKey(Owe, on_delete=models.CASCADE, related_name="collections")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Collection from {self.owe.name}: {self.amount} {self.owe.currency}"

    def save(self, *args, **kwargs):
        """Override save to update owe amount"""
        super().save(*args, **kwargs)
        # Update the owe amount (reduce it by collection)
        self.owe.amount -= self.amount  # Since owe amounts are positive, subtracting collection reduces owe
        self.owe.save()
