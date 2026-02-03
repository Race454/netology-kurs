import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

class APITester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.test_products = []
        self.test_shops = []
    
    def register_user(self):
        """Регистрация тестового пользователя"""
        print("1. Регистрация пользователя...")
        
        data = {
            "email": "buyer@example.com",
            "first_name": "Покупатель",
            "last_name": "Тестовый",
            "password": "password123",
            "password2": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/user/register/", json=data)
        
        if response.status_code == 201:
            result = response.json()
            self.token = result.get('AuthToken')
            self.user_id = result.get('User', {}).get('id')
            print(f"✓ Регистрация успешна!")
            print(f"  Токен: {self.token[:20]}...")
            print(f"  ID пользователя: {self.user_id}")
            return True
        else:
            print(f"✗ Ошибка регистрации: {response.status_code}")
            print(f"  Ответ: {response.text}")
            return False
    
    def login_user(self):
        """Вход пользователя"""
        print("\n2. Вход пользователя...")
        
        data = {
            "email": "buyer@example.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/user/login/", json=data)
        
        if response.status_code == 200:
            result = response.json()
            self.token = result.get('Token')
            self.user_id = result.get('User', {}).get('id')
            print(f"✓ Вход успешен!")
            print(f"  Токен: {self.token[:20]}...")
            return True
        else:
            print(f"✗ Ошибка входа: {response.status_code}")
            print(f"  Ответ: {response.text}")
            return False
    
    def get_products(self):
        """Получение списка товаров"""
        print("\n3. Получение товаров...")
        
        headers = {"Authorization": f"Token {self.token}"} if self.token else {}
        response = requests.get(f"{BASE_URL}/products/", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            products = result.get('Results', [])
            
            if products:
                # Берем первые 3 товара для теста
                self.test_products = products[:3]
                print(f"✓ Получено {len(products)} товаров")
                print(f"  Для теста выбрано {len(self.test_products)} товаров:")
                
                for i, product in enumerate(self.test_products, 1):
                    print(f"    {i}. {product.get('product', {}).get('name')} - {product.get('price')} руб.")
                
                # Собираем уникальные магазины
                shops = set()
                for product in self.test_products:
                    if product.get('shop'):
                        shops.add((product['shop'], product.get('shop_name', 'Магазин')))
                
                self.test_shops = list(shops)
                print(f"  Магазины: {len(self.test_shops)}")
                
                return True
            else:
                print("✗ Нет товаров в базе данных")
                return False
        else:
            print(f"✗ Ошибка получения товаров: {response.status_code}")
            return False
    
    def get_basket(self):
        """Получение корзины"""
        print("\n4. Получение корзины...")
        
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.get(f"{BASE_URL}/basket/", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Корзина получена")
            
            if result.get('Items'):
                print(f"  В корзине {len(result['Items'])} товаров:")
                for item in result['Items']:
                    print(f"    - {item.get('product_name')} x{item.get('quantity')} = {item.get('total_price')} руб.")
                print(f"  Общая сумма: {result.get('Total', 0)} руб.")
            else:
                print("  Корзина пуста")
            
            return result
        else:
            print(f"✗ Ошибка получения корзины: {response.status_code}")
            print(f"  Ответ: {response.text}")
            return None
    
    def add_to_basket(self, product_id, shop_id, quantity=1):
        """Добавление товара в корзину"""
        print(f"\n5. Добавление товара в корзину...")
        
        data = {
            "product_id": product_id,
            "shop_id": shop_id,
            "quantity": quantity
        }
        
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.post(f"{BASE_URL}/basket/", json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Товар добавлен в корзину")
            print(f"  ID товара в корзине: {result.get('ItemID')}")
            return True
        else:
            print(f"✗ Ошибка добавления в корзину: {response.status_code}")
            print(f"  Ответ: {response.text}")
            return False
    
    def remove_from_basket(self, item_id):
        """Удаление товара из корзины"""
        print(f"\n6. Удаление товара из корзины...")
        
        data = {"item_id": item_id}
        
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.delete(f"{BASE_URL}/basket/", json=data, headers=headers)
        
        if response.status_code == 200:
            print(f"✓ Товар удален из корзины")
            return True
        else:
            print(f"✗ Ошибка удаления: {response.status_code}")
            print(f"  Ответ: {response.text}")
            return False
    
    def create_contact(self):
        """Создание контакта для заказа"""
        print("\n7. Создание контакта...")
        
        data = {
            "type": "address",
            "value": "Домашний адрес",
            "city": "Москва",
            "street": "Тверская",
            "house": "10",
            "apartment": "25"
        }
        
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.post(f"{BASE_URL}/contacts/", json=data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            print(f"✓ Контакт создан")
            print(f"  ID контакта: {result.get('id')}")
            return result.get('id')
        else:
            print(f"✗ Ошибка создания контакта: {response.status_code}")
            print(f"  Ответ: {response.text}")
            return None
    
    def confirm_order(self, order_id, contact_id):
        """Подтверждение заказа"""
        print("\n8. Подтверждение заказа...")
        
        data = {
            "order_id": order_id,
            "contact_id": contact_id
        }
        
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.post(f"{BASE_URL}/order/confirm/", json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Заказ подтвержден!")
            print(f"  Номер заказа: {result.get('Order', {}).get('id')}")
            print(f"  Статус: {result.get('Order', {}).get('status_display')}")
            print(f"  Общая сумма: {result.get('Order', {}).get('total_price')} руб.")
            return True
        else:
            print(f"✗ Ошибка подтверждения заказа: {response.status_code}")
            print(f"  Ответ: {response.text}")
            return False
    
    def get_orders(self):
        """Получение списка заказов"""
        print("\n9. Получение списка заказов...")
        
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.get(f"{BASE_URL}/orders/", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            orders = result.get('Orders', [])
            print(f"✓ Получено {len(orders)} заказов")
            
            for order in orders:
                print(f"  - Заказ #{order.get('id')} от {order.get('dt')}: {order.get('status')}")
            
            return orders
        else:
            print(f"✗ Ошибка получения заказов: {response.status_code}")
            return []
    
    def run_full_test(self):
        """Полный тест корзины"""
        print("="*60)
        print("ПОЛНЫЙ ТЕСТ КОРЗИНЫ И ЗАКАЗОВ")
        print("="*60)
        
        # Шаг 1: Регистрация или вход
        if not self.register_user():
            if not self.login_user():
                print("Не удалось зарегистрироваться или войти")
                return
        
        # Шаг 2: Получение товаров
        if not self.get_products():
            print("Не удалось получить товары")
            return
        
        if not self.test_products:
            print("Нет товаров для тестирования")
            return
        
        # Шаг 3: Проверяем пустую корзину
        basket = self.get_basket()
        
        # Шаг 4: Добавляем товары в корзину
        added_items = []
        for i, product in enumerate(self.test_products[:2], 1):  # Добавляем 2 товара
            product_id = product.get('id')
            shop_id = product.get('shop')
            
            if product_id and shop_id:
                print(f"\nДобавляем товар {i}:")
                print(f"  Товар ID: {product_id}")
                print(f"  Магазин ID: {shop_id}")
                
                if self.add_to_basket(product_id, shop_id, quantity=i):  # Разное количество
                    added_items.append({
                        "product_id": product_id,
                        "shop_id": shop_id,
                        "quantity": i
                    })
        
        # Шаг 5: Проверяем корзину с товарами
        print("\n" + "="*60)
        print("КОРЗИНА ПОСЛЕ ДОБАВЛЕНИЯ ТОВАРОВ")
        print("="*60)
        basket = self.get_basket()
        
        if basket and basket.get('Items'):
            # Шаг 6: Создаем контакт
            contact_id = self.create_contact()
            
            if contact_id and basket.get('OrderID'):
                # Шаг 7: Подтверждаем заказ
                print("\n" + "="*60)
                print("ПОДТВЕРЖДЕНИЕ ЗАКАЗА")
                print("="*60)
                self.confirm_order(basket['OrderID'], contact_id)
                
                # Шаг 8: Проверяем список заказов
                print("\n" + "="*60)
                print("СПИСОК ЗАКАЗОВ ПОСЛЕ ПОДТВЕРЖДЕНИЯ")
                print("="*60)
                self.get_orders()
        
        print("\n" + "="*60)
        print("ТЕСТ ЗАВЕРШЕН")
        print("="*60)

# Запуск теста
if __name__ == "__main__":
    tester = APITester()
    tester.run_full_test()