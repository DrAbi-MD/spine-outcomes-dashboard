import sqlite3
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
class Command(BaseCommand):
    help='Create a consistent SQLite backup outside this source folder. Treat it as confidential.'
    def add_arguments(self,parser):parser.add_argument('destination')
    def handle(self,*args,**options):
        dest=Path(options['destination']).expanduser().resolve()
        if dest.is_relative_to(settings.BASE_DIR.resolve()):raise CommandError('Choose a backup destination outside the project folder.')
        if dest.exists():raise CommandError('Destination already exists; choose a new name.')
        if not dest.parent.exists():raise CommandError('Destination directory does not exist.')
        with sqlite3.connect(settings.DATABASES['default']['NAME']) as source:
            with sqlite3.connect(dest) as target:source.backup(target)
        try:dest.chmod(0o600)
        except OSError:pass
        self.stdout.write(self.style.SUCCESS(f'Backup written: {dest}. Store securely; it includes user password hashes and identifiers.'))
