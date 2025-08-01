# Generated by Django 4.2.7 on 2025-07-24 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('internship', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='internshipapplication',
            name='area_of_interest',
            field=models.CharField(choices=[('Networking', 'Networking'), ('Software Development', 'Software Development'), ('Telecom', 'Telecom'), ('Cyber Security', 'Cyber Security'), ('Other', 'Other')], max_length=100),
        ),
        migrations.AlterField(
            model_name='internshipapplication',
            name='program_year',
            field=models.CharField(choices=[('BE Computer', 'BE Computer'), ('BE Electronics', 'BE Electronics'), ('BSc CSIT', 'BSc CSIT'), ('BCA', 'BCA'), ('BIT', 'BIT'), ('Other', 'Other')], max_length=100),
        ),
        migrations.AlterField(
            model_name='internshipapplication',
            name='university_college',
            field=models.CharField(choices=[('TU', 'Tribhuvan University'), ('KU', 'Kathmandu University'), ('PU', 'Pokhara University'), ('PoU', 'Purbanchal University'), ('Other', 'Other')], max_length=100),
        ),
    ]
