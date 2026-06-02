"""
URL маршруты для веб-интерфейса
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Аутентификация
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Главная страница
    path('', views.dashboard, name='dashboard'),
    
    # Медикаменты
    path('medications/', views.medication_list, name='medication_list'),
    path('medications/<int:pk>/', views.medication_detail, name='medication_detail'),
    path('medications/create/', views.medication_create, name='medication_create'),
    path('medications/<int:pk>/update/', views.medication_update, name='medication_update'),
    path('medications/<int:pk>/delete/', views.medication_delete, name='medication_delete'),
    
    # Расходные материалы
    path('consumables/', views.consumable_list, name='consumable_list'),
    path('consumables/<int:pk>/', views.consumable_detail, name='consumable_detail'),
    path('consumables/create/', views.consumable_create, name='consumable_create'),
    path('consumables/<int:pk>/update/', views.consumable_update, name='consumable_update'),
    path('consumables/<int:pk>/delete/', views.consumable_delete, name='consumable_delete'),
    
    # Категории
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Поставщики
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/update/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),

    # Операции
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/update/', views.transaction_update, name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),

    # Отчеты
    path('reports/', views.reports, name='reports'),
    path('reports/export/excel/', views.reports_export_excel, name='reports_export_excel'),
    path('reports/export/pdf/', views.reports_export_pdf, name='reports_export_pdf'),

    # Об авторе
    path('about/', views.about, name='about'),
]
