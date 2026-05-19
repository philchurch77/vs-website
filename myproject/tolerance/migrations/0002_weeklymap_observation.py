import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tolerance", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WeeklyMap",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pupil_name", models.CharField(max_length=200)),
                ("week_commencing", models.DateField()),
                ("class_or_year_group", models.CharField(blank=True, max_length=100)),
                ("key_adults", models.TextField(blank=True)),
                ("review_date", models.DateField(blank=True, null=True)),
                ("support_plan", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "recorded_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="weekly_maps",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-week_commencing", "pupil_name"],
            },
        ),
        migrations.CreateModel(
            name="Observation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("day_name", models.CharField(max_length=20)),
                ("time_slot", models.CharField(max_length=60)),
                ("state", models.CharField(
                    choices=[
                        ("GREEN", "Within Window (Green)"),
                        ("RED", "Hyper-arousal (Red)"),
                        ("BLUE", "Hypo-arousal (Blue)"),
                        ("GREY", "Not observed (Grey)"),
                    ],
                    default="GREY",
                    max_length=10,
                )),
                ("intensity", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("observed_behaviours", models.JSONField(blank=True, default=list)),
                ("possible_triggers", models.JSONField(blank=True, default=list)),
                ("adult_responses", models.JSONField(blank=True, default=list)),
                ("response_helpfulness", models.CharField(
                    blank=True,
                    choices=[
                        ("YES", "Yes"),
                        ("PARTLY", "Partly"),
                        ("NO", "No"),
                        ("UNKNOWN", "Unknown"),
                    ],
                    max_length=10,
                )),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="observations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "weekly_map",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="observations",
                        to="tolerance.weeklymap",
                    ),
                ),
            ],
            options={
                "ordering": ["day_name", "time_slot"],
                "unique_together": {("weekly_map", "day_name", "time_slot")},
            },
        ),
    ]
