from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

ROLES = {
    'Data Entry': [f'{action}_{model}' for model in ['patient','procedure','assessment','treatment','event'] for action in ['view','add','change']],
    'Analyst': ['view_patient','view_procedure','view_assessment','view_treatment','view_event','export_research'],
    'Identifier Manager': ['view_patient','view_identity','change_identity'],
    'Auditor': ['view_patient','view_audit'],
}
class Command(BaseCommand):
    help='Create the four registry roles. This does not create users or grant identifier access to entry users.'
    def handle(self,*args,**options):
        for name,codes in ROLES.items():
            group,_=Group.objects.get_or_create(name=name)
            group.permissions.set(Permission.objects.filter(content_type__app_label='registry',codename__in=codes))
        self.stdout.write(self.style.SUCCESS('Registry roles configured.'))
