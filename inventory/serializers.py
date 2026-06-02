"""
Сериализаторы для REST API
"""
from rest_framework import serializers
from .models import Category, Supplier, Medication, ConsumableMaterial, Transaction, Batch


class BatchSerializer(serializers.ModelSerializer):
    """Сериализатор партии (лота) медикамента"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Batch
        fields = [
            'id', 'medication', 'lot_number', 'expiry_date',
            'quantity_received', 'quantity_remaining', 'price',
            'supplier', 'supplier_name', 'received_at',
            'is_expired', 'is_expiring_soon', 'total_value',
        ]


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['created_at']


class SupplierSerializer(serializers.ModelSerializer):
    """Сериализатор поставщика"""
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact_person', 'phone', 'email',
            'address', 'notes', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class MedicationSerializer(serializers.ModelSerializer):
    """Сериализатор медикамента"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    batches = BatchSerializer(many=True, read_only=True)

    class Meta:
        model = Medication
        fields = [
            'id', 'name', 'category', 'category_name', 'manufacturer',
            'active_ingredient', 'dosage', 'unit', 'unit_display',
            'quantity', 'min_quantity', 'price', 'expiry_date',
            'storage_conditions', 'notes', 'is_active',
            'is_low_stock', 'is_expiring_soon', 'is_expired',
            'total_value', 'batches', 'created_at', 'updated_at'
        ]
        # Остаток и срок годности формируются из партий (приходов), не задаются напрямую
        read_only_fields = ['created_at', 'updated_at', 'quantity', 'expiry_date']


class ConsumableMaterialSerializer(serializers.ModelSerializer):
    """Сериализатор расходного материала"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = ConsumableMaterial
        fields = [
            'id', 'name', 'category', 'category_name', 'description',
            'unit', 'unit_display', 'quantity', 'min_quantity', 'price',
            'expiry_date', 'notes', 'is_active', 'is_low_stock',
            'is_expiring_soon', 'is_expired', 'total_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Сериализатор операции"""
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    consumable_name = serializers.CharField(source='consumable.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'transaction_type_display',
            'item_type', 'item_type_display', 'medication', 'medication_name',
            'consumable', 'consumable_name', 'quantity', 'price',
            'lot_number', 'expiry_date',
            'supplier', 'supplier_name', 'notes', 'user', 'user_username',
            'total_amount', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']

    def validate(self, attrs):
        """Валидация операции для API"""
        def current(field):
            return attrs.get(field, getattr(self.instance, field, None))

        transaction_type = current('transaction_type')
        item_type = current('item_type')
        quantity = current('quantity')
        medication = current('medication')
        consumable = current('consumable')

        # Количество > 0 для прихода/расхода/списания (0 допустим лишь для корректировки)
        if transaction_type in ('in', 'out', 'write_off') and (quantity is None or quantity <= 0):
            raise serializers.ValidationError({'quantity': 'Количество должно быть больше нуля'})

        # Товар должен соответствовать выбранному типу
        if item_type == 'medication' and not medication:
            raise serializers.ValidationError({'medication': 'Укажите медикамент для операции с медикаментом'})
        if item_type == 'consumable' and not consumable:
            raise serializers.ValidationError({'consumable': 'Укажите расходный материал для операции с расходником'})

        # Достаточность остатка при списании/расходе (только при создании)
        if self.instance is None and transaction_type in ('out', 'write_off') and quantity:
            item = medication if item_type == 'medication' else consumable
            if item is not None and item.quantity < quantity:
                raise serializers.ValidationError(
                    {'quantity': f'Недостаточно остатка на складе. Доступно: {item.quantity}'}
                )

        return attrs

    def create(self, validated_data):
        """Автоматическое сохранение текущего пользователя"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
