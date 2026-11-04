from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='moduleaccess',
            name='can_change_author',
            field=models.BooleanField(default=False),
        ),
    ]
