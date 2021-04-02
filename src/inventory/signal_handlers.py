from django.dispatch import receiver
from django.db.models import signals
from django.apps import apps

from simple_history.models import HistoricalRecords
from simple_history.signals import (
    pre_create_historical_record,
    post_create_historical_record
)


Inventory = apps.get_model('inventory', 'Inventory')
HistoricalInventory = apps.get_model('inventory', 'HistoricalInventory')

@receiver(pre_create_historical_record, sender=HistoricalInventory)
def add_user_info(sender, **kwargs):
    history_instance = kwargs['history_instance']
    if hasattr(HistoricalRecords, 'thread'):
        history_instance.ip_address = HistoricalRecords.thread.request.META['REMOTE_ADDR']


@receiver(signals.pre_save, sender=Inventory)
def pre_save_inventory(sender, instance, **kwargs):
    """
    Deletes old file.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return
        else:
            od = old_instance.__dict__
            diff = {
                k: (repr(od[k]), repr(v)) if isinstance(od[k], str) else (od[k], v)
                for k, v in instance.__dict__.items()
                if not k.startswith('_') and (od[k] or v) and getattr(old_instance, k, 'a') != getattr(old_instance, k, 'a')
            }
            diff_msg = ''
            for k, v in diff.items():
                diff_msg += f"{k}: {v[0]} to {v[1]}\n"
            instance._change_reason = diff_msg
