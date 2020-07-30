
"""
All periodic tasks related to integrations. 
"""
from celery.task import periodic_task
from celery.schedules import crontab
from core.celery import app

from inventory.models import (Inventory, )
from labtest.models import (LabTest, )
from .crm import (insert_users, insert_vendors,
                  fetch_labtests, )
from .inventory import (fetch_inventory, )
from .books import (send_estimate_to_sign, )


@periodic_task(run_every=(crontab(hour=[9], minute=0)), options={'queue': 'general'})
def fetch_inventory_efd_on_interval():
    """
    Update inventory on every interval from Zoho Inventory.
    """
    try:
        inventory_before = Inventory.objects.all().delete()
        fetch_labtests(days=150)
        labtests = LabTest.objects.all().count()
        fetch_inventory('inventory_efd', days=150)
        fetch_inventory('inventory_efl', days=150)
        inventory_after = Inventory.objects.all().count()
        return {'status_code': 200,
                'labtest': labtests,
                'deleted': inventory_before[0],
                'inserted': inventory_after}
    except Exception as exc:
        return {'status_code': 400,
                'error': exc}

@app.task(queue="general")
def send_estimate(estimate_id, contact_id):
    """
    Send estimate for sign.
    """
    return send_estimate_to_sign(estimate_id, contact_id)
