from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import sys


class Command(BaseCommand):
    help = 'Create and apply migrations for the enhanced bot models'

    def handle(self, *args, **options):
        self.stdout.write('Creating migrations for enhanced bot models...')
        
        try:
            # Create migrations
            call_command('makemigrations', 'bot', verbosity=2)
            self.stdout.write(
                self.style.SUCCESS('Successfully created migrations')
            )
            
            # Apply migrations
            call_command('migrate', 'bot', verbosity=2)
            self.stdout.write(
                self.style.SUCCESS('Successfully applied migrations')
            )
            
            # Initialize default categories
            from bot.utils import get_default_expense_categories
            get_default_expense_categories()
            self.stdout.write(
                self.style.SUCCESS('Successfully initialized default categories')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
            sys.exit(1)
