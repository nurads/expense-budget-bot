# Generated by Django 4.2.16 on 2024-09-25 10:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bot", "0002_rename_source_income_reason_delete_expense"),
    ]

    operations = [
        migrations.AlterField(
            model_name="income",
            name="amount",
            field=models.IntegerField(),
        ),
    ]
