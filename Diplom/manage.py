#!/usr/bin/env python
import os
import sys
import json
from datetime import datetime

def load_phones_from_json():
    """Загружает телефоны из phones.json в базу данных"""

    
    # Проверяем, нужно ли загружать данные
    # Только при команде runserver и не при других командах
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        print("АВТОМАТИЧЕСКАЯ ЗАГРУЗКА ТЕЛЕФОНОВ ИЗ JSON")
        try:
            # Проверяем существование файла
            json_file = 'phones.json'
            if not os.path.exists(json_file):
                print(f"Файл {json_file} не найден!")
                print(f"   Создайте файл {json_file} в папке: {os.getcwd()}")
                print("="*60 + "\n")
                return
            
            # Настраиваем Django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
            
            import django
            django.setup()
            
            from phones.models import Phone
            
            # Читаем JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                phones_data = json.load(f)
            
            print(f"📊 Найдено {len(phones_data)} телефонов в JSON")
            
            # Очищаем старые данные
            deleted_count, _ = Phone.objects.all().delete()
            print(f"🗑️  Удалено {deleted_count} старых записей")
            
            # Загружаем новые
            created_count = 0
            for data in phones_data:
                Phone.objects.create(
                    name=data['name'],
                    price=data['price'],
                    image=data['image'],
                    release_date=datetime.strptime(data['release_date'], '%Y-%m-%d').date(),
                    lte_exists=data['lte_exists'],
                    slug=data['slug']
                )
                created_count += 1
            
            print(f"Успешно загружено {created_count} телефонов")
            print(f"Всего в базе: {Phone.objects.count()}")
            
        except json.JSONDecodeError as e:
            print(f"Ошибка в формате JSON: {e}")
        except KeyError as e:
            print(f"Отсутствует поле в JSON: {e}")
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
        
        print("="*60 + "\n")


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Автоматически загружаем данные перед запуском сервера
    load_phones_from_json()
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()