#!/usr/bin/env python

# Проверка моделей для Этапа 2

import os
import sys
import django

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Правильное имя модуля настроек - 'myproject'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

try:
    django.setup()
    print("=" * 60)
    print("DJANGO УСПЕШНО НАСТРОЕН!")
    print("=" * 60)
    
    from core.models import *
    
    print("\n1. ПРОВЕРКА ИМПОРТА МОДЕЛЕЙ...")
    models_list = [
        User, Shop, Category, Product, ProductInfo,
        Parameter, ProductParameter, Contact, Order, OrderItem, ConfirmEmailToken
    ]
    print(f"✓ Успешно импортировано {len(models_list)} моделей")
    
    print("\n2. ПРОВЕРКА КОЛИЧЕСТВА ЗАПИСЕЙ...")
    
    # Проверяем каждую модель
    for model in models_list:
        try:
            count = model.objects.count()
            model_name = model.__name__
            print(f"  {model_name:25} - {count:3} записей")
        except Exception as e:
            print(f"  {model.__name__:25} - ОШИБКА: {str(e)[:50]}...")
    
    print("\n3. ПРОВЕРКА СОЗДАНИЯ ТЕСТОВЫХ ДАННЫХ...")
    
    # Создаем тестового пользователя если его нет
    if User.objects.filter(email='test@example.com').count() == 0:
        try:
            user = User.objects.create_user(
                email='test@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User',
                type='buyer'
            )
            print(f"✓ Создан тестовый пользователь: {user.email}")
        except Exception as e:
            print(f"✗ Ошибка при создании пользователя: {e}")
    else:
        print("✓ Тестовый пользователь уже существует")
    
    print("\n4. ПРОВЕРКА СВЯЗЕЙ МЕЖДУ МОДЕЛЯМИ...")
    
    # Получаем или создаем тестового пользователя
    test_user = User.objects.filter(email='test@example.com').first()
    
    if test_user:
        # Создаем тестовый магазин
        if Shop.objects.filter(name='Test Shop').count() == 0:
            shop = Shop.objects.create(
                name='Test Shop',
                url='https://test.example.com',
                user=test_user,
                state=True
            )
            print(f"✓ Создан тестовый магазин: {shop.name}")
        else:
            print("✓ Тестовый магазин уже существует")
        
        # Создаем тестовую категорию
        if Category.objects.filter(name='Test Category').count() == 0:
            category = Category.objects.create(name='Test Category')
            category.shops.add(Shop.objects.first())
            print(f"✓ Создана тестовая категория: {category.name}")
        else:
            print("✓ Тестовая категория уже существует")
    
    print("\n5. ПРОВЕРКА МЕТОДОВ МОДЕЛЕЙ...")
    
    # Проверяем наличие методов
    if hasattr(Order, 'get_total_price'):
        print("✓ У модели Order есть метод get_total_price()")
    else:
        print("✗ У модели Order отсутствует метод get_total_price()")
    
    if hasattr(OrderItem, 'get_item_price'):
        print("✓ У модели OrderItem есть метод get_item_price()")
    else:
        print("✗ У модели OrderItem отсутствует метод get_item_price()")
    
    print("\n" + "=" * 60)
    print("6. ПРОВЕРКА АДМИН-ПАНЕЛИ...")
    
    from django.contrib import admin
    
    admin_models = []
    for model in models_list:
        try:
            if admin.site.is_registered(model):
                admin_models.append(model.__name__)
        except:
            pass
    
    print(f"В админке зарегистрировано {len(admin_models)} моделей:")
    for i, model_name in enumerate(admin_models, 1):
        print(f"  {i:2}. {model_name}")
    
    print("\n" + "=" * 60)
    print("ИТОГОВАЯ СВОДКА:")
    
    # Проверяем основные критерии
    checks = []
    
    # 1. Все ли модели импортируются?
    checks.append(("Импорт всех моделей", len(models_list) == 11))
    
    # 2. Есть ли записи в базе?
    total_records = sum(model.objects.count() for model in models_list)
    checks.append(("Данные в базе", total_records > 0))
    
    # 3. Зарегистрированы ли модели в админке?
    checks.append(("Регистрация в админке", len(admin_models) >= 10))
    
    # 4. Есть ли дополнительные методы?
    has_methods = hasattr(Order, 'get_total_price') and hasattr(OrderItem, 'get_item_price')
    checks.append(("Дополнительные методы", has_methods))
    
    passed = 0
    for check_name, status in checks:
        if status:
            print(f"✓ {check_name}")
            passed += 1
        else:
            print(f"✗ {check_name}")
    
    print(f"\nПройдено {passed} из {len(checks)} проверок")
    
    if passed == len(checks):
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! ЭТАП 2 ВЫПОЛНЕН УСПЕШНО!")
    else:
        print(f"\n⚠️  Пройдено только {passed} из {len(checks)} проверок")
    
except Exception as e:
    print(f"\n✗ ОШИБКА ПРИ ВЫПОЛНЕНИИ ПРОВЕРКИ:")
    print(f"  {type(e).__name__}: {e}")
    print("\nПроверьте настройки Django и корректность установки проекта.")