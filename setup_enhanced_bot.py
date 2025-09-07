#!/usr/bin/env python3
"""
Setup script for the enhanced expense budget bot
This script helps initialize the enhanced features
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command
from bot.utils import get_default_expense_categories


def main():
    print("🚀 Setting up Enhanced Expense Budget Bot...")
    
    try:
        # Create migrations
        print("📝 Creating migrations...")
        call_command('makemigrations', 'bot', verbosity=1)
        
        # Apply migrations
        print("🔄 Applying migrations...")
        call_command('migrate', 'bot', verbosity=1)
        
        # Initialize default categories
        print("📁 Initializing default categories...")
        get_default_expense_categories()
        
        print("✅ Setup completed successfully!")
        print("\n🎯 Enhanced Features Available:")
        print("• 💱 Multiple currency support")
        print("• 🔥 Streak system to earn money")
        print("• 📊 Weekly and monthly reports")
        print("• 📁 Enhanced expense categories")
        print("• ⚙️ Improved settings and user experience")
        
        print("\n📱 To start the bot:")
        print("python manage.py runserver")
        print("\n📖 See ENHANCED_FEATURES.md for detailed documentation")
        
    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
