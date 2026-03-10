"""
Представления (views) для веб-интерфейса
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import Category, Supplier, Medication, ConsumableMaterial, Transaction
from .forms import (
    CategoryForm, SupplierForm, MedicationForm,
    ConsumableMaterialForm, TransactionForm, DateRangeForm
)


def login_view(request):
    """Страница входа"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    
    return render(request, 'inventory/login.html', {'form': form})


@login_required
def dashboard(request):
    """Главная панель (дашборд)"""
    # Статистика
    total_medications = Medication.objects.filter(is_active=True).count()
    total_consumables = ConsumableMaterial.objects.filter(is_active=True).count()
    
    # Медикаменты с низким остатком
    low_stock_medications = Medication.objects.filter(
        is_active=True,
        quantity__lte=F('min_quantity')
    ).count()
    
    # Расходники с низким остатком
    low_stock_consumables = ConsumableMaterial.objects.filter(
        is_active=True,
        quantity__lte=F('min_quantity')
    ).count()
    
    # Медикаменты с истекающим сроком годности (30 дней)
    expiring_soon = Medication.objects.filter(
        is_active=True,
        expiry_date__lte=timezone.now().date() + timedelta(days=30),
        expiry_date__gte=timezone.now().date()
    ).count()
    
    # Просроченные медикаменты
    expired = Medication.objects.filter(
        is_active=True,
        expiry_date__lt=timezone.now().date()
    ).count()
    
    # Общая стоимость товаров на складе
    medications_value = Medication.objects.filter(is_active=True).aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or 0
    
    consumables_value = ConsumableMaterial.objects.filter(is_active=True).aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or 0
    
    total_inventory_value = medications_value + consumables_value
    
    # Последние операции
    recent_transactions = Transaction.objects.select_related(
        'medication', 'consumable', 'supplier', 'user'
    )[:10]
    
    # Алерты
    alerts = []
    
    if low_stock_medications > 0:
        alerts.append({
            'type': 'warning',
            'icon': '📉',
            'text': f'{low_stock_medications} медикаментов с низким остатком',
            'url': '/medications/?low_stock=1'
        })
    
    if low_stock_consumables > 0:
        alerts.append({
            'type': 'warning',
            'icon': '📉',
            'text': f'{low_stock_consumables} расходников с низким остатком',
            'url': '/consumables/?low_stock=1'
        })
    
    if expiring_soon > 0:
        alerts.append({
            'type': 'info',
            'icon': '⏰',
            'text': f'{expiring_soon} медикаментов истекают в течение 30 дней',
            'url': '/medications/?expiring=1'
        })
    
    if expired > 0:
        alerts.append({
            'type': 'danger',
            'icon': '❌',
            'text': f'{expired} просроченных медикаментов',
            'url': '/medications/?expired=1'
        })
    
    context = {
        'total_medications': total_medications,
        'total_consumables': total_consumables,
        'low_stock_medications': low_stock_medications,
        'low_stock_consumables': low_stock_consumables,
        'expiring_soon': expiring_soon,
        'expired': expired,
        'total_inventory_value': total_inventory_value,
        'recent_transactions': recent_transactions,
        'alerts': alerts,
    }
    
    return render(request, 'inventory/dashboard.html', context)


@login_required
def medication_list(request):
    """Список медикаментов"""
    medications = Medication.objects.filter(is_active=True).select_related('category')
    
    # Фильтры
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    low_stock = request.GET.get('low_stock', '')
    expiring = request.GET.get('expiring', '')
    expired = request.GET.get('expired', '')
    
    if search:
        medications = medications.filter(
            Q(name__icontains=search) |
            Q(manufacturer__icontains=search) |
            Q(active_ingredient__icontains=search)
        )
    
    if category_id:
        medications = medications.filter(category_id=category_id)
    
    if low_stock:
        medications = medications.filter(quantity__lte=F('min_quantity'))
    
    if expiring:
        medications = medications.filter(
            expiry_date__lte=timezone.now().date() + timedelta(days=30),
            expiry_date__gte=timezone.now().date()
        )
    
    if expired:
        medications = medications.filter(expiry_date__lt=timezone.now().date())
    
    categories = Category.objects.all()
    
    context = {
        'medications': medications,
        'categories': categories,
        'search': search,
        'category_id': category_id,
    }
    
    return render(request, 'inventory/medication_list.html', context)


@login_required
def medication_detail(request, pk):
    """Детальная информация о медикаменте"""
    medication = get_object_or_404(Medication, pk=pk)
    transactions = medication.transactions.all()[:20]
    
    context = {
        'medication': medication,
        'transactions': transactions,
    }
    
    return render(request, 'inventory/medication_detail.html', context)


@login_required
def medication_create(request):
    """Создание медикамента"""
    if request.method == 'POST':
        form = MedicationForm(request.POST)
        if form.is_valid():
            medication = form.save()
            messages.success(request, f'Медикамент "{medication.name}" успешно создан')
            return redirect('medication_detail', pk=medication.pk)
    else:
        form = MedicationForm()
    
    return render(request, 'inventory/medication_form.html', {
        'form': form,
        'title': 'Добавить медикамент'
    })


@login_required
def medication_update(request, pk):
    """Редактирование медикамента"""
    medication = get_object_or_404(Medication, pk=pk)
    
    if request.method == 'POST':
        form = MedicationForm(request.POST, instance=medication)
        if form.is_valid():
            form.save()
            messages.success(request, f'Медикамент "{medication.name}" успешно обновлен')
            return redirect('medication_detail', pk=medication.pk)
    else:
        form = MedicationForm(instance=medication)
    
    return render(request, 'inventory/medication_form.html', {
        'form': form,
        'title': 'Редактировать медикамент',
        'medication': medication
    })


@login_required
def medication_delete(request, pk):
    """Удаление (деактивация) медикамента"""
    medication = get_object_or_404(Medication, pk=pk)
    
    if request.method == 'POST':
        medication.is_active = False
        medication.save()
        messages.success(request, f'Медикамент "{medication.name}" успешно удален')
        return redirect('medication_list')
    
    return render(request, 'inventory/medication_confirm_delete.html', {
        'medication': medication
    })


@login_required
def consumable_list(request):
    """Список расходных материалов"""
    consumables = ConsumableMaterial.objects.filter(is_active=True).select_related('category')
    
    # Фильтры
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    low_stock = request.GET.get('low_stock', '')
    
    if search:
        consumables = consumables.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if category_id:
        consumables = consumables.filter(category_id=category_id)
    
    if low_stock:
        consumables = consumables.filter(quantity__lte=F('min_quantity'))
    
    categories = Category.objects.all()
    
    context = {
        'consumables': consumables,
        'categories': categories,
        'search': search,
        'category_id': category_id,
    }
    
    return render(request, 'inventory/consumable_list.html', context)


@login_required
def consumable_detail(request, pk):
    """Детальная информация о расходном материале"""
    consumable = get_object_or_404(ConsumableMaterial, pk=pk)
    transactions = consumable.transactions.all()[:20]
    
    context = {
        'consumable': consumable,
        'transactions': transactions,
    }
    
    return render(request, 'inventory/consumable_detail.html', context)


@login_required
def consumable_create(request):
    """Создание расходного материала"""
    if request.method == 'POST':
        form = ConsumableMaterialForm(request.POST)
        if form.is_valid():
            consumable = form.save()
            messages.success(request, f'Материал "{consumable.name}" успешно создан')
            return redirect('consumable_detail', pk=consumable.pk)
    else:
        form = ConsumableMaterialForm()
    
    return render(request, 'inventory/consumable_form.html', {
        'form': form,
        'title': 'Добавить расходный материал'
    })


@login_required
def consumable_update(request, pk):
    """Редактирование расходного материала"""
    consumable = get_object_or_404(ConsumableMaterial, pk=pk)
    
    if request.method == 'POST':
        form = ConsumableMaterialForm(request.POST, instance=consumable)
        if form.is_valid():
            form.save()
            messages.success(request, f'Материал "{consumable.name}" успешно обновлен')
            return redirect('consumable_detail', pk=consumable.pk)
    else:
        form = ConsumableMaterialForm(instance=consumable)
    
    return render(request, 'inventory/consumable_form.html', {
        'form': form,
        'title': 'Редактировать расходный материал',
        'consumable': consumable
    })


@login_required
def consumable_delete(request, pk):
    """Удаление (деактивация) расходного материала"""
    consumable = get_object_or_404(ConsumableMaterial, pk=pk)
    
    if request.method == 'POST':
        consumable.is_active = False
        consumable.save()
        messages.success(request, f'Материал "{consumable.name}" успешно удален')
        return redirect('consumable_list')
    
    return render(request, 'inventory/consumable_confirm_delete.html', {
        'consumable': consumable
    })


@login_required
def transaction_list(request):
    """Список операций"""
    transactions = Transaction.objects.all().select_related(
        'medication', 'consumable', 'supplier', 'user'
    )
    
    # Фильтры
    transaction_type = request.GET.get('type', '')
    item_type = request.GET.get('item_type', '')
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if item_type:
        transactions = transactions.filter(item_type=item_type)
    
    context = {
        'transactions': transactions,
    }
    
    return render(request, 'inventory/transaction_list.html', context)


@login_required
def transaction_create(request):
    """Создание операции"""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Операция успешно создана')
            return redirect('transaction_list')
    else:
        form = TransactionForm()
    
    return render(request, 'inventory/transaction_form.html', {
        'form': form,
        'title': 'Новая операция'
    })


@login_required
def reports(request):
    """Отчеты"""
    form = DateRangeForm(request.GET or None)
    
    # Общая статистика
    stats = {
        'total_medications': Medication.objects.filter(is_active=True).count(),
        'total_consumables': ConsumableMaterial.objects.filter(is_active=True).count(),
        'total_transactions': Transaction.objects.count(),
        'low_stock_items': (
            Medication.objects.filter(is_active=True, quantity__lte=F('min_quantity')).count() +
            ConsumableMaterial.objects.filter(is_active=True, quantity__lte=F('min_quantity')).count()
        ),
    }
    
    context = {
        'form': form,
        'stats': stats,
    }
    
    return render(request, 'inventory/reports.html', context)
