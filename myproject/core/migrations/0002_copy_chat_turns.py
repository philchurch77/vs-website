"""Copy chat history from the per-app ChatTurn tables into core_chatturn.

Raw SQL is used (not the ORM) so the original auto_now_add timestamps are
preserved exactly. The flashcards 0009_delete_chatturn migration depends on
this one, so the copy provably runs before the drop.

Note: this migration originally also copied from the evaluation (``gptchat``)
ChatTurn table. The evaluation app has since been removed; its source line and
dependency were dropped so the migration graph stays valid on a fresh database
(e.g. the test database). On databases where this migration already ran, the
edit has no effect — applied migrations are not re-run.
"""
from django.db import migrations


def copy_chat_turns(apps, schema_editor):
    core_table = apps.get_model("core", "ChatTurn")._meta.db_table
    sources = [
        ("flashcards", apps.get_model("flashcards", "ChatTurn")._meta.db_table),
    ]
    with schema_editor.connection.cursor() as cursor:
        for tool, table in sources:
            # Safety net: snapshot the legacy table into an unmanaged
            # backup table first. The 0009 DeleteModel migrations drop the
            # originals; these snapshots survive, so the copy is fully
            # recoverable without a file-level DB backup. Drop the
            # *_predrop_backup tables manually once the deploy is verified.
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table}_predrop_backup "
                f"AS SELECT * FROM {table}"
            )
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
    ]

    operations = [
        migrations.RunPython(copy_chat_turns, delete_copied_turns),
    ]
