# test_api_simple.py
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoints():
    print("Тестирование API endpoints")
    print("="*60)
    
    # 1. Регистрация
    print("\n1. Регистрация пользователя")
    data = {
        "first_name": "Netology",
        "last_name": "Netolog",
        "email": "netology@diplom.com",
        "password": "net123",
        "password2": "net123"
    }
    response = requests.post(f"{BASE_URL}/user/register/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 201:
        token = response.json().get('Token')
        headers = {"Authorization": f"Token {token}"}
        
        # 2. Просмотр товаров
        print("\n2. Просмотр списка товаров")
        response = requests.get(f"{BASE_URL}/products/")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Найдено товаров: {data.get('Count', 0)}")
        
        if data.get('Results'):
            # 3. Добавление в корзину
            print("\n3. Добавление в корзину")
            first_product = data['Results'][0]
            basket_data = {
                "product_id": first_product['product']['id'],
                "shop_id": first_product['shop'],
                "quantity": 1
            }
            response = requests.post(f"{BASE_URL}/basket/", 
                                     headers=headers, 
                                     json=basket_data)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            # 4. Просмотр корзины
            print("\n4. Просмотр корзины")
            response = requests.get(f"{BASE_URL}/basket/", headers=headers)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            # 5. Добавление контакта
            print("\n5. Добавление контакта")
            contact_data = {
                "type": "phone",
                "value": "+7 (999) 123-45-67"
            }
            response = requests.post(f"{BASE_URL}/contacts/", 
                                     headers=headers, 
                                     json=contact_data)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            # 6. Просмотр заказов
            print("\n6. Просмотр списка заказов")
            response = requests.get(f"{BASE_URL}/orders/", headers=headers)
            print(f"   Status: {response.status_code}")
            print(f"   Найдено заказов: {response.json().get('Count', 0)}")
    
    print("\n" + "="*60)
    print("Тестирование завершено!")

if __name__ == "__main__":
    test_endpoints()