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
    
    # Операции
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    
    # Отчеты
    path('reports/', views.reports, name='reports'),
]
