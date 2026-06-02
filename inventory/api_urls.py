"""
URL маршруты для REST API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    CategoryViewSet, SupplierViewSet, MedicationViewSet,
    ConsumableMaterialViewSet, TransactionViewSet, BatchViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'medications', MedicationViewSet)
router.register(r'batches', BatchViewSet)
router.register(r'consumables', ConsumableMaterialViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
