"""
Сериализаторы для REST API
"""
from rest_framework import serializers
from .models import Category, Supplier, Medication, ConsumableMaterial, Transaction


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
    
    class Meta:
        model = Medication
        fields = [
            'id', 'name', 'category', 'category_name', 'manufacturer',
            'active_ingredient', 'dosage', 'unit', 'unit_display',
            'quantity', 'min_quantity', 'price', 'expiry_date',
            'storage_conditions', 'notes', 'is_active',
            'is_low_stock', 'is_expiring_soon', 'is_expired',
            'total_value', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ConsumableMaterialSerializer(serializers.ModelSerializer):
    """Сериализатор расходного материала"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = ConsumableMaterial
        fields = [
            'id', 'name', 'category', 'category_name', 'description',
            'unit', 'unit_display', 'quantity', 'min_quantity', 'price',
            'notes', 'is_active', 'is_low_stock', 'total_value',
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
            'supplier', 'supplier_name', 'notes', 'user', 'user_username',
            'total_amount', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']
    
    def create(self, validated_data):
        """Автоматическое сохранение текущего пользователя"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
