# Generated by Django 5.0 on 2023-12-13 18:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('creditapi', '0002_rename_current_debt_customer_age_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='loan',
            old_name='customer',
            new_name='customer_id',
        ),
    ]
