# create_test_shop_user.py
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from core.models import User

try:
    user = User.objects.create_user(
        email='netology@diplom.com',
        password='net123',
        first_name='Netology',
        last_name='Diplom',
        type='diplom',
        company='Netology',
        position='diplom'
    )
    print(f"Создан пользователь-магазин: {user.email}")
    print(f"Пароль: net123")
    print(f"Тип: {user.type}")
except Exception as e:
    print(f"Ошибка: {e}")