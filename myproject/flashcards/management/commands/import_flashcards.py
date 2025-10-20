from django.core.management.base import BaseCommand
from flashcards.models import Flashcard
import pandas as pd

class Command(BaseCommand):
    help = 'Import or update flashcards from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str, help=r"C:\Users\philc\OneDrive\Desktop\VS Code\VS_Website\myproject\flashcards\Flashcards.xlsx")

    def handle(self, *args, **kwargs):
        filepath = kwargs['filepath']
        df = pd.read_excel(filepath, sheet_name='Flashcards')

        for _, row in df.iterrows():
            Flashcard.objects.update_or_create(
                flashcard_id=row['ID'],
                defaults={
                    'title': row['Title'],
                    'how_to_do_it': row['How To Do it:'],
                    'what_you_need': row['What you need:'],
                    'who_where_when_why': row['Who? Where? When? Why?'],
                    'sort_order': row['Sort Order']
                }
            )
        self.stdout.write(self.style.SUCCESS('Flashcards imported successfully!'))
