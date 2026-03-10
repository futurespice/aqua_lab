"""
Модели данных для системы учета медикаментов и расходных материалов
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta


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
        """Проверка на приближающийся срок годности (30 дней)"""
        if self.expiry_date:
            return self.expiry_date <= timezone.now().date() + timedelta(days=30)
        return False
    
    @property
    def is_expired(self):
        """Проверка на истекший срок годности"""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False
    
    @property
    def total_value(self):
        """Общая стоимость товара на складе"""
        return self.quantity * self.price


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
        validators=[MinValueValidator(0.01)]
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
    notes = models.TextField('Примечания', blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Пользователь',
        related_name='transactions'
    )
    created_at = models.DateTimeField('Дата операции', default=timezone.now)
    
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
    
    def save(self, *args, **kwargs):
        """Переопределение save для автоматического обновления остатков"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Получаем объект товара
            item = self.medication if self.item_type == 'medication' else self.consumable
            
            if item:
                # Обновляем количество в зависимости от типа операции
                if self.transaction_type == 'in':
                    item.quantity += self.quantity
                elif self.transaction_type in ['out', 'write_off']:
                    item.quantity -= self.quantity
                    if item.quantity < 0:
                        item.quantity = 0
                elif self.transaction_type == 'adjustment':
                    item.quantity = self.quantity
                
                item.save()
