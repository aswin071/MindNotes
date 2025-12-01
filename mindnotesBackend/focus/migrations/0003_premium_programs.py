# Generated manually for Premium Focus Programs

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import utils.model_abstracts


class Migration(migrations.Migration):

    dependencies = [
        ('focus', '0002_remove_focuspause_session_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add new program types to FocusProgram
        migrations.AlterField(
            model_name='focusprogram',
            name='program_type',
            field=models.CharField(
                choices=[
                    ('14_day', '14-Day Program'),
                    ('30_day', '30-Day Program'),
                    ('custom', 'Custom Program'),
                    ('morning_charge', '5-Minute Morning Charge'),
                    ('brain_dump', 'Brain Dump Reset'),
                    ('gratitude_pause', 'Gratitude Pause'),
                ],
                max_length=20
            ),
        ),
        # Create BrainDumpCategory model
        migrations.CreateModel(
            name='BrainDumpCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('icon', models.CharField(blank=True, max_length=50)),
                ('color', models.CharField(default='#3B82F6', max_length=7)),
                ('description', models.TextField(blank=True)),
                ('order', models.IntegerField(default=0)),
                ('is_system', models.BooleanField(default=True, help_text='System-defined category')),
            ],
            options={
                'verbose_name_plural': 'Brain Dump Categories',
                'db_table': 'brain_dump_categories',
                'ordering': ['order', 'name'],
            },
            bases=(utils.model_abstracts.Model, models.Model),
        ),
        # Create PremiumProgramTrial model
        migrations.CreateModel(
            name='PremiumProgramTrial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trial_started_at', models.DateTimeField(auto_now_add=True)),
                ('trial_ends_at', models.DateTimeField(help_text='7 days from start')),
                ('morning_charge_count', models.IntegerField(default=0)),
                ('brain_dump_count', models.IntegerField(default=0)),
                ('gratitude_pause_count', models.IntegerField(default=0)),
                ('trial_expired', models.BooleanField(default=False)),
                ('converted_to_paid', models.BooleanField(default=False)),
                ('converted_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='premium_program_trial', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'premium_program_trials',
            },
            bases=(utils.model_abstracts.Model, models.Model),
        ),
        # Add indexes to PremiumProgramTrial
        migrations.AddIndex(
            model_name='premiumprogramtrial',
            index=models.Index(fields=['user', 'trial_ends_at'], name='premium_pr_user_id_trial_e_idx'),
        ),
        migrations.AddIndex(
            model_name='premiumprogramtrial',
            index=models.Index(fields=['trial_expired'], name='premium_pr_trial_e_idx'),
        ),
    ]
