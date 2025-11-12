from django.db import migrations

def add_body_if_missing(apps, schema_editor):
    Topic = apps.get_model("resources", "Topic")
    table = Topic._meta.db_table
    cursor = schema_editor.connection.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    if "body" not in cols:
        schema_editor.execute(f'ALTER TABLE {table} ADD COLUMN body TEXT NULL')

class Migration(migrations.Migration):
    dependencies = [
        ("resources", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(add_body_if_missing, migrations.RunPython.noop),
    ]
