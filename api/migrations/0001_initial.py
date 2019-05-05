# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-04 23:49
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency_name', models.CharField(max_length=60, verbose_name='Название валюты')),
                ('currency', models.CharField(db_index=True, max_length=10, verbose_name='ISO')),
                ('fractional', models.SmallIntegerField(verbose_name='Дробная часть')),
            ],
            options={
                'verbose_name': 'Валюта',
                'ordering': ('pk',),
                'verbose_name_plural': 'Валюты',
            },
        ),
        migrations.CreateModel(
            name='ExchangeRate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.FloatField(verbose_name='Курс валюты к USD')),
                ('created', models.DateTimeField(verbose_name='Дата добавления')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='api.Currency', verbose_name='Валюта')),
            ],
            options={
                'verbose_name': 'Курс валюты',
                'verbose_name_plural': 'Курсы валют',
                'ordering': ('pk',),
            },
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operation', models.CharField(max_length=20, verbose_name='Название операции')),
                ('oper_amount', models.BigIntegerField(verbose_name='Cумма операции в валюте операции')),
                ('usd_amount', models.BigIntegerField(verbose_name='Cумма операции в USD')),
                ('created', models.DateTimeField(verbose_name='Дата операции')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='api.Currency', verbose_name='Идентификатор валюты операции')),
            ],
            options={
                'verbose_name': 'Операция',
                'ordering': ('pk',),
                'verbose_name_plural': 'Операции',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operation', models.CharField(max_length=20, verbose_name='Название операции')),
                ('status', models.CharField(db_index=True, max_length=6, verbose_name='Статус транзакции')),
                ('amount', models.FloatField(verbose_name='Сумма операции')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Дата транзакции')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='api.Currency', verbose_name='Валюта транзакции')),
            ],
            options={
                'verbose_name': 'Транзакция',
                'ordering': ('pk',),
                'verbose_name_plural': 'Транзакции',
            },
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255, unique=True, verbose_name='Имя клиента')),
                ('city', models.CharField(max_length=60, verbose_name='Страна')),
                ('country', models.CharField(max_length=180, verbose_name='Город проживания')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')),
                ('balance', models.BigIntegerField(default=0, verbose_name='Баланс')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='api.Currency', verbose_name='Валюта кошелька')),
            ],
            options={
                'verbose_name': 'Кошелек',
                'ordering': ('pk',),
                'verbose_name_plural': 'Кошельки',
            },
        ),
        migrations.CreateModel(
            name='WalletHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wallet_partner_name', models.CharField(max_length=255, null=True, verbose_name='Имя клиента, с которым проводилась операция')),
                ('oper_date', models.DateTimeField(db_index=True, verbose_name='Дата операции')),
                ('type', models.CharField(max_length=3, verbose_name='Тип операции (списание, пополнение)')),
                ('amount', models.BigIntegerField(verbose_name='Cумма операции в валюте кошелька')),
                ('oper', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='api.Operation', verbose_name='Операция')),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='histories', to='api.Wallet', verbose_name='Кошелек')),
                ('wallet_partner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='partner_histories', to='api.Wallet', verbose_name='Кошелек, с которым проводилась операция')),
            ],
            options={
                'verbose_name': 'История операции по кошельку',
                'ordering': ('pk',),
                'verbose_name_plural': 'История операций по кошелькам',
            },
        ),
        migrations.AddField(
            model_name='transaction',
            name='wallet_from',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='in_transactions', to='api.Wallet', verbose_name='Кошелек, с которого снимают деньги'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='wallet_to',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='out_transactions', to='api.Wallet', verbose_name='Кошелек, на который поступают деньги'),
        ),
        migrations.AlterUniqueTogether(
            name='exchangerate',
            unique_together=set([('currency', 'created')]),
        ),
    ]