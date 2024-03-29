# Generated by Django 4.2.8 on 2024-01-14 13:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fatpaybacks', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FatPaybackRecord',
            fields=[
                ('id', models.AutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.TextField(blank=True)),
                ('actioned', models.DateTimeField(auto_now=True)),
                ('config', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, to='fatpaybacks.fatpaybacksetup')),
            ],
        ),
    ]
