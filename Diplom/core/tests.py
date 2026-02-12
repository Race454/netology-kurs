from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.cache import cache

class ThrottlingTestCase(APITestCase):
    def setUp(self):
        cache.clear()
    
    def test_register_throttle(self):
        """Тест ограничения регистрации"""
        url = reverse('core:user-register')
        data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'TestPass123',
            'password2': 'TestPass123'
        }
        
        # 5 успешных запросов
        for i in range(5):
            response = self.client.post(url, data, format='json')
            data['email'] = f'test{i}@example.com'  # Меняем email
        
        # 6й запрос должен быть отклонен
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)