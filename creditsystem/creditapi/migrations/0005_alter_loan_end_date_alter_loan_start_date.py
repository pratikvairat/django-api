# Generated by Django 5.0 on 2023-12-13 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creditapi', '0004_rename_customer_id_loan_customer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loan',
            name='end_date',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='loan',
            name='start_date',
            field=models.DateTimeField(),
        ),
    ]
