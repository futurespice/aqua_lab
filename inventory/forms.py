"""
Формы для работы с данными
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Category, Supplier, Medication, ConsumableMaterial, Transaction


class CategoryForm(forms.ModelForm):
    """Форма категории"""
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название категории'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание категории'}),
        }


class SupplierForm(forms.ModelForm):
    """Форма поставщика"""
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'notes', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название компании'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО контактного лица'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+996 XXX XXX XXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MedicationForm(forms.ModelForm):
    """Форма медикамента"""
    class Meta:
        model = Medication
        fields = [
            'name', 'category', 'manufacturer', 'active_ingredient', 'dosage',
            'unit', 'quantity', 'min_quantity', 'price', 'expiry_date',
            'storage_conditions', 'notes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название медикамента'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Производитель'}),
            'active_ingredient': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Действующее вещество'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: 500мг'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'min_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'storage_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ConsumableMaterialForm(forms.ModelForm):
    """Форма расходного материала"""
    class Meta:
        model = ConsumableMaterial
        fields = [
            'name', 'category', 'description', 'unit',
            'quantity', 'min_quantity', 'price', 'notes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название материала'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Описание'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'min_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TransactionForm(forms.ModelForm):
    """Форма операции"""
    class Meta:
        model = Transaction
        fields = [
            'transaction_type', 'item_type', 'medication', 'consumable',
            'quantity', 'price', 'supplier', 'notes'
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'item_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_item_type'}),
            'medication': forms.Select(attrs={'class': 'form-select', 'id': 'id_medication'}),
            'consumable': forms.Select(attrs={'class': 'form-select', 'id': 'id_consumable'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        item_type = cleaned_data.get('item_type')
        medication = cleaned_data.get('medication')
        consumable = cleaned_data.get('consumable')
        transaction_type = cleaned_data.get('transaction_type')
        quantity = cleaned_data.get('quantity')
        
        # Проверка что выбран либо медикамент либо расходник
        if item_type == 'medication':
            if not medication:
                raise ValidationError('Выберите медикамент')
            if consumable:
                cleaned_data['consumable'] = None
            
            # Проверка достаточности количества при расходе
            if transaction_type in ['out', 'write_off']:
                if medication.quantity < quantity:
                    raise ValidationError(
                        f'Недостаточно товара на складе. Доступно: {medication.quantity} {medication.get_unit_display()}'
                    )
        
        elif item_type == 'consumable':
            if not consumable:
                raise ValidationError('Выберите расходный материал')
            if medication:
                cleaned_data['medication'] = None
            
            # Проверка достаточности количества при расходе
            if transaction_type in ['out', 'write_off']:
                if consumable.quantity < quantity:
                    raise ValidationError(
                        f'Недостаточно материала на складе. Доступно: {consumable.quantity} {consumable.get_unit_display()}'
                    )
        
        return cleaned_data


class DateRangeForm(forms.Form):
    """Форма фильтрации по датам"""
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='От'
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='До'
    )
