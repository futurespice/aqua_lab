"""
Перенос существующих остатков медикаментов в партионную модель.

Для каждого медикамента с остатком создаётся «начальная» партия
(лот OPENING) с текущим остатком, сроком годности и ценой позиции —
так старые данные становятся согласованными с учётом по партиям/FEFO.
"""
from django.db import migrations
from decimal import Decimal


def create_opening_batches(apps, schema_editor):
    Medication = apps.get_model('inventory', 'Medication')
    Batch = apps.get_model('inventory', 'Batch')

    for med in Medication.objects.all():
        # пропускаем, если партии уже есть или остаток нулевой
        if med.quantity is None or med.quantity <= 0:
            continue
        if Batch.objects.filter(medication=med).exists():
            continue
        Batch.objects.create(
            medication=med,
            lot_number='OPENING',
            expiry_date=med.expiry_date,
            quantity_received=med.quantity,
            quantity_remaining=med.quantity,
            price=med.price or Decimal('0'),
            supplier=None,
            received_at=med.created_at,
        )


def remove_opening_batches(apps, schema_editor):
    Batch = apps.get_model('inventory', 'Batch')
    Batch.objects.filter(lot_number='OPENING').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_transaction_batch_movements_transaction_expiry_date_and_more'),
    ]

    operations = [
        migrations.RunPython(create_opening_batches, remove_opening_batches),
    ]
