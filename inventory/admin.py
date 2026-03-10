"""
Настройка административной панели
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Supplier, Medication, ConsumableMaterial, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'phone', 'email']
    list_filter = ['is_active', 'created_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'contact_person', 'is_active')
        }),
        ('Контактные данные', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Дополнительно', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'manufacturer', 'quantity_display',
        'price', 'expiry_date', 'status_display', 'is_active'
    ]
    search_fields = ['name', 'manufacturer', 'active_ingredient']
    list_filter = ['category', 'is_active', 'expiry_date', 'unit']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'category', 'is_active')
        }),
        ('Детали медикамента', {
            'fields': ('manufacturer', 'active_ingredient', 'dosage', 'unit')
        }),
        ('Остатки и цена', {
            'fields': ('quantity', 'min_quantity', 'price')
        }),
        ('Срок годности и хранение', {
            'fields': ('expiry_date', 'storage_conditions')
        }),
        ('Дополнительно', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def quantity_display(self, obj):
        """Отображение количества с цветовым индикатором"""
        color = 'red' if obj.is_low_stock else 'green'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, obj.quantity, obj.get_unit_display()
        )
    quantity_display.short_description = 'Количество'
    
    def status_display(self, obj):
        """Отображение статуса товара"""
        from django.utils.safestring import mark_safe
        statuses = []
        if obj.is_expired:
            statuses.append('<span style="color: red;">❌ Просрочен</span>')
        elif obj.is_expiring_soon:
            statuses.append('<span style="color: orange;">⚠️ Истекает</span>')
        if obj.is_low_stock:
            statuses.append('<span style="color: red;">📉 Низкий остаток</span>')

        if not statuses:
            return mark_safe('<span style="color: green;">✅ OK</span>')
        return mark_safe(' '.join(statuses))
    status_display.short_description = 'Статус'


@admin.register(ConsumableMaterial)
class ConsumableMaterialAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'quantity_display',
        'price', 'total_value', 'is_active'
    ]
    search_fields = ['name', 'description']
    list_filter = ['category', 'is_active', 'unit']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'category', 'description', 'is_active')
        }),
        ('Остатки и цена', {
            'fields': ('unit', 'quantity', 'min_quantity', 'price')
        }),
        ('Дополнительно', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def quantity_display(self, obj):
        """Отображение количества с цветовым индикатором"""
        color = 'red' if obj.is_low_stock else 'green'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, obj.quantity, obj.get_unit_display()
        )
    quantity_display.short_description = 'Количество'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'transaction_type', 'item_display',
        'quantity', 'price', 'total_amount', 'supplier', 'user'
    ]
    search_fields = ['notes', 'medication__name', 'consumable__name']
    list_filter = ['transaction_type', 'item_type', 'created_at', 'supplier']
    date_hierarchy = 'created_at'
    readonly_fields = ['user', 'created_at']
    
    fieldsets = (
        ('Тип операции', {
            'fields': ('transaction_type', 'item_type')
        }),
        ('Товар', {
            'fields': ('medication', 'consumable')
        }),
        ('Детали операции', {
            'fields': ('quantity', 'price', 'supplier')
        }),
        ('Дополнительно', {
            'fields': ('notes', 'user', 'created_at')
        }),
    )
    
    def item_display(self, obj):
        """Отображение товара"""
        if obj.medication:
            return format_html('<strong>💊</strong> {}', obj.medication.name)
        elif obj.consumable:
            return format_html('<strong>🔬</strong> {}', obj.consumable.name)
        return '-'
    item_display.short_description = 'Товар'
    
    def save_model(self, request, obj, form, change):
        """Автоматическое сохранение пользователя"""
        if not obj.pk:
            obj.user = request.user
        super().save_model(request, obj, form, change)
