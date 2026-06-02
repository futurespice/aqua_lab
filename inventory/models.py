"""
Модели данных для системы учета медикаментов и расходных материалов
"""
from django.db import models, transaction, connection
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


def _lock_qs(queryset):
    """Блокирует строки (SELECT ... FOR UPDATE) там, где БД это поддерживает.

    На PostgreSQL даёт строковые блокировки и защищает пересчёт остатков от гонок
    при одновременных операциях. На SQLite select_for_update не поддерживается —
    тогда возвращаем queryset как есть (запись в SQLite и так сериализуется).
    """
    if connection.features.has_select_for_update:
        return queryset.select_for_update()
    return queryset


class Category(models.Model):
    """Категория товаров"""
    name = models.CharField('Название', max_length=100, unique=True)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Supplier(models.Model):
    """Поставщик"""
    name = models.CharField('Название', max_length=200)
    contact_person = models.CharField('Контактное лицо', max_length=100, blank=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    email = models.EmailField('Email', blank=True)
    address = models.TextField('Адрес', blank=True)
    notes = models.TextField('Примечания', blank=True)
    is_active = models.BooleanField('Активный', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Medication(models.Model):
    """Медикамент"""
    UNIT_CHOICES = [
        ('mg', 'мг'),
        ('g', 'г'),
        ('ml', 'мл'),
        ('l', 'л'),
        ('tablet', 'таблетка'),
        ('ampule', 'ампула'),
        ('vial', 'флакон'),
        ('pack', 'упаковка'),
    ]
    
    name = models.CharField('Название', max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
        related_name='medications'
    )
    manufacturer = models.CharField('Производитель', max_length=200, blank=True)
    active_ingredient = models.CharField('Действующее вещество', max_length=200, blank=True)
    dosage = models.CharField('Дозировка', max_length=100, blank=True)
    unit = models.CharField('Единица измерения', max_length=20, choices=UNIT_CHOICES, default='pack')
    quantity = models.DecimalField(
        'Количество на складе',
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    min_quantity = models.DecimalField(
        'Минимальное количество',
        max_digits=10,
        decimal_places=2,
        default=10,
        validators=[MinValueValidator(0)]
    )
    price = models.DecimalField(
        'Цена за единицу',
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    expiry_date = models.DateField('Срок годности', null=True, blank=True)
    storage_conditions = models.TextField('Условия хранения', blank=True)
    notes = models.TextField('Примечания', blank=True)
    is_active = models.BooleanField('Активный', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Медикамент'
        verbose_name_plural = 'Медикаменты'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"
    
    @property
    def is_low_stock(self):
        """Проверка на низкий остаток"""
        return self.quantity <= self.min_quantity
    
    @property
    def is_expiring_soon(self):
        """Срок годности истекает в течение 30 дней (и ещё не истёк)"""
        if self.expiry_date:
            today = timezone.now().date()
            return today <= self.expiry_date <= today + timedelta(days=30)
        return False
    
    @property
    def is_expired(self):
        """Проверка на истекший срок годности"""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False
    
    @property
    def total_value(self):
        """Стоимость остатка на складе.

        Считается по фактической себестоимости партий (сумма «остаток × цена закупки»),
        что точнее статичной цены позиции. При отсутствии партий — резерв по цене позиции.
        """
        agg = self.batches.aggregate(
            v=models.Sum(models.F('quantity_remaining') * models.F('price'))
        )
        if agg['v'] is not None:
            return agg['v']
        return self.quantity * self.price

    def recalc_from_batches(self):
        """Пересчитывает остаток и ближайший срок годности из партий (FEFO).

        Остаток позиции = сумма остатков партий; срок годности позиции =
        ближайший срок среди непустых партий (для алертов о просрочке).
        """
        agg = self.batches.aggregate(total=models.Sum('quantity_remaining'))
        self.quantity = agg['total'] or Decimal('0')
        nearest = self.batches.filter(
            quantity_remaining__gt=0, expiry_date__isnull=False
        ).order_by('expiry_date').first()
        self.expiry_date = nearest.expiry_date if nearest else None
        self.save(update_fields=['quantity', 'expiry_date', 'updated_at'])


class Batch(models.Model):
    """Партия (лот) медикамента с собственным сроком годности.

    Каждая приёмка (приход) создаёт партию. Расход и списание уменьшают остатки
    партий по принципу FEFO (First-Expired-First-Out — первой расходуется партия
    с ближайшим сроком годности). Так ведут учёт в реальных лабораториях.
    """
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        verbose_name='Медикамент',
        related_name='batches'
    )
    lot_number = models.CharField('Номер партии (лот)', max_length=100, blank=True)
    expiry_date = models.DateField('Срок годности', null=True, blank=True)
    quantity_received = models.DecimalField(
        'Поступило', max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)]
    )
    quantity_remaining = models.DecimalField(
        'Остаток партии', max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)]
    )
    price = models.DecimalField(
        'Цена закупки за единицу', max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)]
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Поставщик', related_name='batches'
    )
    received_at = models.DateTimeField('Дата поступления', default=timezone.now)
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        verbose_name = 'Партия'
        verbose_name_plural = 'Партии'
        # FEFO по умолчанию: ближайший срок первым, партии без срока — в конце
        ordering = [models.F('expiry_date').asc(nulls_last=True), 'received_at', 'id']

    def __str__(self):
        lot = self.lot_number or '—'
        exp = self.expiry_date.strftime('%d.%m.%Y') if self.expiry_date else 'без срока'
        return f"{self.medication.name}: лот {lot} (до {exp}), остаток {self.quantity_remaining}"

    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    @property
    def is_expiring_soon(self):
        if self.expiry_date:
            today = timezone.now().date()
            return today <= self.expiry_date <= today + timedelta(days=30)
        return False

    @property
    def total_value(self):
        return self.quantity_remaining * self.price


class ConsumableMaterial(models.Model):
    """Расходный материал"""
    UNIT_CHOICES = [
        ('piece', 'шт'),
        ('pack', 'упаковка'),
        ('box', 'коробка'),
        ('set', 'набор'),
        ('meter', 'метр'),
        ('roll', 'рулон'),
    ]
    
    name = models.CharField('Название', max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
        related_name='consumables'
    )
    description = models.TextField('Описание', blank=True)
    unit = models.CharField('Единица измерения', max_length=20, choices=UNIT_CHOICES, default='piece')
    quantity = models.DecimalField(
        'Количество на складе',
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    min_quantity = models.DecimalField(
        'Минимальное количество',
        max_digits=10,
        decimal_places=2,
        default=10,
        validators=[MinValueValidator(0)]
    )
    price = models.DecimalField(
        'Цена за единицу',
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    expiry_date = models.DateField('Срок годности', null=True, blank=True)
    notes = models.TextField('Примечания', blank=True)
    is_active = models.BooleanField('Активный', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Расходный материал'
        verbose_name_plural = 'Расходные материалы'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"

    @property
    def is_low_stock(self):
        """Проверка на низкий остаток"""
        return self.quantity <= self.min_quantity

    @property
    def is_expiring_soon(self):
        """Срок годности истекает в течение 30 дней (и ещё не истёк)"""
        if self.expiry_date:
            today = timezone.now().date()
            return today <= self.expiry_date <= today + timedelta(days=30)
        return False

    @property
    def is_expired(self):
        """Срок годности истёк"""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    @property
    def total_value(self):
        """Общая стоимость материала на складе"""
        return self.quantity * self.price


class Transaction(models.Model):
    """Операция прихода/расхода"""
    TRANSACTION_TYPES = [
        ('in', 'Приход'),
        ('out', 'Расход'),
        ('write_off', 'Списание'),
        ('adjustment', 'Корректировка'),
    ]
    
    ITEM_TYPES = [
        ('medication', 'Медикамент'),
        ('consumable', 'Расходный материал'),
    ]
    
    transaction_type = models.CharField('Тип операции', max_length=20, choices=TRANSACTION_TYPES)
    item_type = models.CharField('Тип товара', max_length=20, choices=ITEM_TYPES)
    
    # Связи с товарами
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Медикамент',
        related_name='transactions'
    )
    consumable = models.ForeignKey(
        ConsumableMaterial,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Расходный материал',
        related_name='transactions'
    )
    
    quantity = models.DecimalField(
        'Количество',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    price = models.DecimalField(
        'Цена за единицу',
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Поставщик',
        related_name='transactions'
    )
    # Реквизиты партии — используются при приходе медикамента (создаётся партия/лот)
    lot_number = models.CharField(
        'Номер партии (лот)', max_length=100, blank=True,
        help_text='Только для прихода медикамента: создаётся партия с этим лотом'
    )
    expiry_date = models.DateField(
        'Срок годности партии', null=True, blank=True,
        help_text='Только для прихода медикамента'
    )
    notes = models.TextField('Примечания', blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Пользователь',
        related_name='transactions'
    )
    created_at = models.DateTimeField('Дата операции', default=timezone.now)
    stock_effect = models.DecimalField(
        'Изменение остатка',
        max_digits=10,
        decimal_places=2,
        default=0,
        editable=False,
        help_text='Служебное поле: фактическое изменение остатка этой операцией (для корректного отката)'
    )
    batch_movements = models.JSONField(
        'Движение партий', default=list, blank=True, editable=False,
        help_text='Служебное поле: какие партии и на сколько изменила операция (для отката)'
    )

    class Meta:
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.medication:
            item_name = self.medication.name
        elif self.consumable:
            item_name = self.consumable.name
        else:
            item_name = '—'
        return f"{self.get_transaction_type_display()} - {item_name} ({self.quantity})"
    
    @property
    def total_amount(self):
        """Общая сумма операции"""
        return self.quantity * self.price

    def get_item(self):
        """Связанный товар: медикамент или расходный материал"""
        if self.item_type == 'medication':
            return self.medication
        return self.consumable

    # ----- Простой учёт остатка (расходные материалы) -----
    @staticmethod
    def _apply_simple_delta(item, delta):
        """Изменяет остаток расходника, не допуская отрицательных значений"""
        if item is None or not delta:
            return
        item.quantity = item.quantity + delta
        if item.quantity < 0:
            item.quantity = Decimal('0')
        item.save()

    # ----- Партионный учёт по FEFO (медикаменты) -----
    @staticmethod
    def _consume_fefo(medication, amount):
        """Списывает amount из партий по FEFO (ближайший срок первым).

        Возвращает (фактически_списано, движения, себестоимость). Если остатка
        не хватает, списывает сколько есть (без ухода в минус). Себестоимость —
        сумма «списано × цена закупки партии» (для авто-расчёта стоимости расхода).
        """
        to_consume = amount
        movements = []
        cost = Decimal('0')
        batches = _lock_qs(
            medication.batches.filter(quantity_remaining__gt=0)
        ).order_by(models.F('expiry_date').asc(nulls_last=True), 'received_at', 'id')
        for b in batches:
            if to_consume <= 0:
                break
            take = b.quantity_remaining if b.quantity_remaining < to_consume else to_consume
            b.quantity_remaining = b.quantity_remaining - take
            b.save(update_fields=['quantity_remaining'])
            movements.append([b.pk, str(-take)])
            cost += take * b.price
            to_consume = to_consume - take
        return amount - to_consume, movements, cost

    def _apply_effect(self):
        """Применяет операцию к складу.

        Расходные материалы — простой остаток. Медикаменты — партионный учёт:
        приход создаёт партию, расход/списание уменьшают партии по FEFO,
        корректировка добивает разницу (вниз — FEFO, вверх — новой партией).
        Для расхода/списания цена операции выставляется автоматически по
        себестоимости (FEFO у медикамента, цена позиции у расходника).
        """
        # --- Расходные материалы: простой остаток ---
        if self.item_type == 'consumable':
            item = _lock_qs(
                ConsumableMaterial.objects.filter(pk=self.consumable_id)
            ).first() if self.consumable_id else None
            effect = Decimal('0')
            if item is not None:
                if self.transaction_type == 'in':
                    effect = self.quantity
                elif self.transaction_type in ('out', 'write_off'):
                    effect = -self.quantity
                    self.price = item.price  # авто-себестоимость расхода
                elif self.transaction_type == 'adjustment':
                    effect = self.quantity - item.quantity
                if item.quantity + effect < 0:
                    effect = -item.quantity
                self._apply_simple_delta(item, effect)
            self.batch_movements = []
            self.stock_effect = effect
            return

        # --- Медикаменты: партионный учёт (FEFO) ---
        med = _lock_qs(
            Medication.objects.filter(pk=self.medication_id)
        ).first() if self.medication_id else None
        if med is None:
            self.batch_movements = []
            self.stock_effect = Decimal('0')
            return

        movements = []
        effect = Decimal('0')

        if self.transaction_type == 'in':
            b = Batch.objects.create(
                medication=med, lot_number=self.lot_number or '',
                expiry_date=self.expiry_date, quantity_received=self.quantity,
                quantity_remaining=self.quantity, price=self.price,
                supplier=self.supplier, received_at=self.created_at,
            )
            movements.append([b.pk, str(self.quantity)])
            effect = self.quantity

        elif self.transaction_type in ('out', 'write_off'):
            consumed, movements, cost = self._consume_fefo(med, self.quantity)
            effect = -consumed
            # Авто-себестоимость расхода: средняя цена закупки списанных партий
            if consumed > 0:
                self.price = (cost / consumed).quantize(Decimal('0.01'))

        elif self.transaction_type == 'adjustment':
            current = med.batches.aggregate(t=models.Sum('quantity_remaining'))['t'] or Decimal('0')
            delta = self.quantity - current
            if delta < 0:
                consumed, movements, _cost = self._consume_fefo(med, -delta)
                effect = -consumed
            elif delta > 0:
                b = Batch.objects.create(
                    medication=med, lot_number=self.lot_number or 'КОРР',
                    expiry_date=self.expiry_date, quantity_received=delta,
                    quantity_remaining=delta, price=self.price,
                    supplier=self.supplier, received_at=self.created_at,
                )
                movements.append([b.pk, str(delta)])
                effect = delta

        self.batch_movements = movements
        self.stock_effect = effect
        med.recalc_from_batches()

    def _reverse_effect(self):
        """Откатывает влияние операции (для отката при правке/удалении)."""
        if self.item_type == 'consumable':
            item = _lock_qs(
                ConsumableMaterial.objects.filter(pk=self.consumable_id)
            ).first() if self.consumable_id else None
            if item is not None and self.stock_effect:
                self._apply_simple_delta(item, -self.stock_effect)
            return

        med = _lock_qs(
            Medication.objects.filter(pk=self.medication_id)
        ).first() if self.medication_id else None
        if med is None:
            return

        for batch_id, delta_str in (self.batch_movements or []):
            delta = Decimal(delta_str)
            b = _lock_qs(Batch.objects.filter(pk=batch_id)).first()
            if b is None:
                continue
            if delta < 0:
                # Был расход партии — возвращаем остаток, не превышая поступившее
                restored = b.quantity_remaining - delta  # delta < 0 → прибавляем
                b.quantity_remaining = min(restored, b.quantity_received)
                b.save(update_fields=['quantity_remaining'])
            else:
                # Был приход партии — изымаем поступление, не уходя в минус
                b.quantity_received = max(Decimal('0'), b.quantity_received - delta)
                if b.quantity_remaining > b.quantity_received:
                    b.quantity_remaining = b.quantity_received
                b.save(update_fields=['quantity_received', 'quantity_remaining'])

        med.recalc_from_batches()

    def save(self, *args, **kwargs):
        """Сохранение операции с автоматическим пересчётом остатков и партий.

        Всё выполняется в одной транзакции с блокировкой строк товара и партий
        (на СУБД с поддержкой select_for_update), что защищает остаток от гонок
        при одновременных операциях. При редактировании прежний эффект
        откатывается, затем применяется новый. Медикаменты — по партиям (FEFO),
        расходные материалы — простым остатком.
        """
        with transaction.atomic():
            if self.pk is not None:
                old = type(self).objects.filter(pk=self.pk).select_related(
                    'medication', 'consumable'
                ).first()
                if old is not None:
                    old._reverse_effect()

            self._apply_effect()
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Удаление операции с откатом её влияния на склад (партии/остаток)."""
        with transaction.atomic():
            self._reverse_effect()
            super().delete(*args, **kwargs)
