from getpass import getpass
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .setup_roles import ROLES

class Command(BaseCommand):
    help='Create an account with one or more registry roles; password is prompted privately.'
    def add_arguments(self,parser):
        parser.add_argument('username')
        parser.add_argument('--role',action='append',required=True,choices=list(ROLES))
    def handle(self,*args,**options):
        User=get_user_model()
        if User.objects.filter(username=options['username']).exists():raise CommandError('Username already exists.')
        groups=list(Group.objects.filter(name__in=options['role']))
        if len(groups)!=len(set(options['role'])):raise CommandError('Run setup_roles first.')
        user=User(username=options['username'])
        password=getpass('Password (at least 12 characters): ')
        if password!=getpass('Confirm password: '):raise CommandError('Passwords do not match.')
        try:validate_password(password,user)
        except ValidationError as exc:raise CommandError('; '.join(exc.messages))
        user.set_password(password);user.save();user.groups.set(groups)
        self.stdout.write(self.style.SUCCESS('Account created.'))
