"""
API Views для REST API
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F
from django.utils import timezone
from datetime import timedelta

from .models import Category, Supplier, Medication, ConsumableMaterial, Transaction
from .serializers import (
    CategorySerializer, SupplierSerializer, MedicationSerializer,
    ConsumableMaterialSerializer, TransactionSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """API для категорий"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class SupplierViewSet(viewsets.ModelViewSet):
    """API для поставщиков"""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'contact_person', 'phone', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class MedicationViewSet(viewsets.ModelViewSet):
    """API для медикаментов"""
    queryset = Medication.objects.select_related('category').all()
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active', 'unit']
    search_fields = ['name', 'manufacturer', 'active_ingredient']
    ordering_fields = ['name', 'quantity', 'price', 'expiry_date', 'created_at']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Медикаменты с низким остатком"""
        medications = self.get_queryset().filter(
            is_active=True,
            quantity__lte=F('min_quantity')
        )
        serializer = self.get_serializer(medications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Медикаменты с истекающим сроком годности (30 дней)"""
        medications = self.get_queryset().filter(
            is_active=True,
            expiry_date__lte=timezone.now().date() + timedelta(days=30),
            expiry_date__gte=timezone.now().date()
        )
        serializer = self.get_serializer(medications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Просроченные медикаменты"""
        medications = self.get_queryset().filter(
            is_active=True,
            expiry_date__lt=timezone.now().date()
        )
        serializer = self.get_serializer(medications, many=True)
        return Response(serializer.data)


class ConsumableMaterialViewSet(viewsets.ModelViewSet):
    """API для расходных материалов"""
    queryset = ConsumableMaterial.objects.select_related('category').all()
    serializer_class = ConsumableMaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active', 'unit']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'quantity', 'price', 'created_at']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Расходники с низким остатком"""
        consumables = self.get_queryset().filter(
            is_active=True,
            quantity__lte=F('min_quantity')
        )
        serializer = self.get_serializer(consumables, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ModelViewSet):
    """API для операций"""
    queryset = Transaction.objects.select_related(
        'medication', 'consumable', 'supplier', 'user'
    ).all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'item_type', 'supplier']
    search_fields = ['notes', 'medication__name', 'consumable__name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Автоматическое сохранение пользователя"""
        serializer.save(user=self.request.user)
