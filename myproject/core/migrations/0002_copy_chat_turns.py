"""Copy chat history from the per-app ChatTurn tables into core_chatturn.

Raw SQL is used (not the ORM) so the original auto_now_add timestamps are
preserved exactly. The flashcards/gptchat 0009_delete_chatturn migrations
both depend on this one, so the copy provably runs before either drop.
"""
from django.db import migrations


def copy_chat_turns(apps, schema_editor):
    core_table = apps.get_model("core", "ChatTurn")._meta.db_table
    sources = [
        ("flashcards", apps.get_model("flashcards", "ChatTurn")._meta.db_table),
        ("evaluation", apps.get_model("gptchat", "ChatTurn")._meta.db_table),
    ]
    with schema_editor.connection.cursor() as cursor:
        for tool, table in sources:
            cursor.execute(
                f"INSERT INTO {core_table} "
                f"(tool, session_id, role, content, timestamp, user_id) "
                f"SELECT %s, session_id, role, content, timestamp, user_id "
                f"FROM {table} ORDER BY timestamp, id",
                [tool],
            )


def delete_copied_turns(apps, schema_editor):
    apps.get_model("core", "ChatTurn").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("flashcards", "0008_rename_scenarios_scenario_alter_scenario_options"),
        ("gptchat", "0008_trainingsummary_user"),
    ]

    operations = [
        migrations.RunPython(copy_chat_turns, delete_copied_turns),
    ]
