import yaml
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from requests import get
from .models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Метод для загрузки данных о товарах от поставщика
        Ожидает YAML файл с данными
        """
        
        # 1. Проверка аутентификации
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)
        
        # 2. Проверка типа пользователя (только магазины могут обновлять прайс)
        if request.user.type != 'shop':
            return JsonResponse(
                {'Status': False, 'Error': 'Только для магазинов'}, 
                status=403
            )
        
        # 3. Получение URL или файла с данными
        url = request.data.get('url')
        file = request.FILES.get('file')
        
        data = None
        
        # 4. Обработка URL
        if url:
            # Валидация URL
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)}, status=400)
            
            # Загрузка данных по URL
            try:
                response = get(url)
                response.raise_for_status()
                data = yaml.safe_load(response.content)
            except Exception as e:
                return JsonResponse(
                    {'Status': False, 'Error': f'Ошибка загрузки данных: {str(e)}'}, 
                    status=400
                )
        
        # 5. Обработка файла
        elif file:
            try:
                # Проверяем тип файла
                if not file.name.endswith(('.yaml', '.yml')):
                    return JsonResponse(
                        {'Status': False, 'Error': 'Файл должен быть в формате YAML'}, 
                        status=400
                    )
                
                # Читаем файл
                data = yaml.safe_load(file.read())
            except yaml.YAMLError as e:
                return JsonResponse(
                    {'Status': False, 'Error': f'Ошибка парсинга YAML: {str(e)}'}, 
                    status=400
                )
            except Exception as e:
                return JsonResponse(
                    {'Status': False, 'Error': f'Ошибка чтения файла: {str(e)}'}, 
                    status=400
                )
        
        else:
            return JsonResponse(
                {'Status': False, 'Error': 'Не указаны данные для импорта (url или file)'}, 
                status=400
            )
        
        # 6. Проверка структуры данных
        if not data or 'shop' not in data:
            return JsonResponse(
                {'Status': False, 'Error': 'Неверный формат данных. Отсутствует поле "shop"'}, 
                status=400
            )
        
        # 7. Импорт данных в транзакции (все или ничего)
        try:
            with transaction.atomic():
                # Получаем или создаем магазин
                shop, created = Shop.objects.get_or_create(
                    name=data['shop'],
                    user=request.user
                )
                
                if created:
                    shop.url = data.get('url', '')
                    shop.save()
                
                # Импорт категорий
                if 'categories' in data:
                    for category_data in data['categories']:
                        category, _ = Category.objects.get_or_create(
                            id=category_data.get('id'),
                            defaults={'name': category_data['name']}
                        )
                        
                        # Обновляем название если изменилось
                        if category.name != category_data['name']:
                            category.name = category_data['name']
                            category.save()
                        
                        # Связываем категорию с магазином
                        category.shops.add(shop)
                
                # Удаляем старые данные о товарах этого магазина
                ProductInfo.objects.filter(shop=shop).delete()
                
                # Импорт товаров
                if 'goods' in data:
                    for product_data in data['goods']:
                        # Получаем или создаем продукт
                        product, _ = Product.objects.get_or_create(
                            name=product_data['name'],
                            category_id=product_data['category']
                        )
                        
                        # Создаем информацию о продукте
                        product_info = ProductInfo.objects.create(
                            product=product,
                            shop=shop,
                            external_id=product_data['id'],
                            model=product_data.get('model', ''),
                            quantity=product_data['quantity'],
                            price=product_data['price'],
                            price_rrc=product_data['price_rrc']
                        )
                        
                        # Импорт параметров товара
                        if 'parameters' in product_data:
                            for param_name, param_value in product_data['parameters'].items():
                                parameter, _ = Parameter.objects.get_or_create(
                                    name=param_name
                                )
                                
                                ProductParameter.objects.create(
                                    product_info=product_info,
                                    parameter=parameter,
                                    value=str(param_value)
                                )
                
                return JsonResponse({
                    'Status': True,
                    'Message': f'Импорт успешно завершен. Магазин: {shop.name}',
                    'Shop': shop.name,
                    'Products': len(data.get('goods', []))
                })
                
        except KeyError as e:
            return JsonResponse(
                {'Status': False, 'Error': f'Отсутствует обязательное поле: {str(e)}'}, 
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'Status': False, 'Error': f'Ошибка при импорте данных: {str(e)}'}, 
                status=400
            )
    
class PartnerState(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Получить статус магазина
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)
        
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        
        try:
            shop = Shop.objects.get(user=request.user)
            return JsonResponse({
                'Status': True,
                'State': shop.state,
                'Name': shop.name
            })
        except Shop.DoesNotExist:
            return JsonResponse({'Status': False, 'Error': 'Магазин не найден'}, status=404)

    def post(self, request, *args, **kwargs):
        """
        Изменить статус магазина
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)
        
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        
        state = request.data.get('state')
        if state is None:
            return JsonResponse({'Status': False, 'Error': 'Не указан статус'}, status=400)
        
        try:
            shop = Shop.objects.get(user=request.user)
            shop.state = bool(state)
            shop.save()
            
            return JsonResponse({
                'Status': True,
                'Message': f'Статус магазина {shop.name} изменен на {"активен" if shop.state else "неактивен"}',
                'State': shop.state
            })
        except Shop.DoesNotExist:
            return JsonResponse({'Status': False, 'Error': 'Магазин не найден'}, status=404)


class PartnerOrders(APIView):
    """
    Класс для получения заказов поставщиками
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Получить заказы для магазина
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)
        
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        
        try:
            shop = Shop.objects.get(user=request.user)
            
            # Получаем заказы, которые содержат товары этого магазина
            from .models import Order, OrderItem
            import json
            from django.core import serializers
            
            # Заказы с товарами нашего магазина
            order_items = OrderItem.objects.filter(shop=shop).select_related(
                'order', 'order__user', 'product'
            )
            
            orders_data = []
            for item in order_items:
                order_data = {
                    'id': item.order.id,
                    'dt': item.order.dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': item.order.status,
                    'user': item.order.user.email,
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'price': item.get_item_price()
                }
                orders_data.append(order_data)
            
            return JsonResponse({
                'Status': True,
                'Orders': orders_data,
                'Count': len(orders_data)
            })
            
        except Shop.DoesNotExist:
            return JsonResponse({'Status': False, 'Error': 'Магазин не найден'}, status=404)