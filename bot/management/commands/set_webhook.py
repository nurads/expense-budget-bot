from typing import Any
from django.core.management import BaseCommand, CommandError
from django.core.management.base import CommandParser
from bot.bot import bot
from django.conf import settings

class Command(BaseCommand):

    def handle(self, *args: Any, **options: Any):
        print(settings.WEB_HOOK_URL)
        bot.set_webhook(settings.WEB_HOOK_URL)
