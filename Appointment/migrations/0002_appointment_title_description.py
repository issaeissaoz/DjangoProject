from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Appointment", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="appointment",
            old_name="notes",
            new_name="description",
        ),
        migrations.AddField(
            model_name="appointment",
            name="title",
            field=models.CharField(default="", max_length=120),
            preserve_default=False,
        ),
    ]
