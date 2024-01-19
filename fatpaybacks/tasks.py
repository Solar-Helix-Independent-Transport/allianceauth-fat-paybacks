from celery import shared_task

from .models import FatPaybackSetup


@shared_task
def credit_each_corp():
    print(FatPaybackSetup.objects.get(id=1).credit_corps())
