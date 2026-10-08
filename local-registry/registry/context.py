from django.conf import settings
def site(request):
    return {'hospital_name': settings.HOSPITAL_NAME, 'prototype_mode': settings.PROTOTYPE_MODE}
