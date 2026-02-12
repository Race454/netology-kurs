import yaml
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from requests import get

# Импортируем асинхронные задачи
from .tasks import send_confirm_email_task, send_order_confirmation_task

from .models import (
    User, Shop, Category, Product, ProductInfo, 
    Parameter, ProductParameter, Contact, Order, 
    OrderItem, ConfirmEmailToken
)
from .serializers import (
    UserSerializer, UserLoginSerializer, UserRegistrationSerializer,
    ShopSerializer, CategorySerializer, ProductInfoDetailSerializer,
    ContactSerializer, OrderSerializer, OrderItemSerializer,
    BasketItemSerializer
)
from .forms import UserLoginForm, UserRegistrationForm, ContactForm
from .throttles import RegisterThrottle, BasketThrottle


class UserLoginView(APIView):
    """
    Авторизация пользователя.
    
    Принимает:
        - email: Email пользователя
        - password: Пароль
    
    Возвращает:
        - Token: Токен для авторизации
        - User: Данные пользователя
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Создаем или получаем токен
            try:
                token, created = Token.objects.get_or_create(user=user)
            except Exception as e:
                return Response({
                    'Status': False,
                    'Error': f'Ошибка создания токена: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'Status': True,
                'Token': token.key,
                'User': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'type': user.type
                }
            })
        return Response({'Status': False, 'Errors': serializer.errors}, 
                       status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(generics.CreateAPIView):
    """
    Регистрация нового пользователя.
    
    Принимает:
        - email: Email пользователя
        - first_name: Имя
        - last_name: Фамилия
        - password: Пароль
        - password2: Подтверждение пароля
    
    Возвращает:
        - Status: Статус операции
        - Message: Сообщение
        - User: Данные пользователя
        - ConfirmToken: Токен подтверждения email (в демо-режиме)
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    throttle_classes = [RegisterThrottle]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                # Создаем пользователя
                user = serializer.save()
                
                # Активируем пользователя сразу (для упрощения)
                user.is_active = True
                user.save()
                
                # Создаем токен для подтверждения email
                token = None
                try:
                    token = ConfirmEmailToken.objects.create(user=user)
                    # АСИНХРОННАЯ отправка email с подтверждением
                    send_confirm_email_task.delay(
                        user_email=user.email,
                        token=token.key
                    )
                except Exception as e:
                    print(f"Не удалось создать токен подтверждения: {e}")
                
                # Формируем ответ
                response_data = {
                    'Status': True,
                    'Message': 'Регистрация успешна',
                    'User': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'type': user.type,
                        'is_active': user.is_active
                    }
                }
                
                # Добавляем токен для подтверждения email, если он создан
                if token:
                    response_data['ConfirmToken'] = token.key
                    response_data['Message'] = 'Регистрация успешна. Проверьте email для подтверждения.'
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'Status': False,
                    'Error': f'Ошибка при создании пользователя: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'Status': False, 
            'Errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProductListView(generics.ListAPIView):
    """
    Получение списка товаров с фильтрацией.
    
    Поддерживает фильтрацию по:
    - category_id: ID категории
    - shop_id: ID магазина
    - search: поиск по названию или модели
    - min_price / max_price: диапазон цен
    
    Возвращает:
        Status: статус операции
        Count: количество товаров
        Results: массив товаров с детальной информацией
    """
    serializer_class = ProductInfoDetailSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = ProductInfo.objects.select_related(
            'product', 'shop'
        ).prefetch_related(
            'product_parameters__parameter'
        ).filter(quantity__gt=0)
        
        # Фильтрация по категории
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)
        
        # Фильтрация по магазину
        shop_id = self.request.query_params.get('shop_id')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        
        # Поиск по названию продукта
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(product__name__icontains=search) |
                Q(model__icontains=search)
            )
        
        # Фильтрация по цене
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'Status': True,
            'Count': queryset.count(),
            'Results': serializer.data
        })


class BasketView(APIView):
    """
    Работа с корзиной покупателя.
    
    GET: Получить содержимое корзины
    POST: Добавить товар в корзину
        - product_id: ID товара
        - shop_id: ID магазина
        - quantity: Количество (по умолчанию 1)
    DELETE: Удалить товар из корзины
        - item_id: ID позиции в корзине
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [BasketThrottle]
    
    def get(self, request):
        """Получить содержимое корзины"""
        basket_order = Order.objects.filter(
            user=request.user,
            status='basket'
        ).first()
        
        if not basket_order:
            return Response({
                'Status': True,
                'Message': 'Корзина пуста',
                'Items': [],
                'Total': 0
            })
        
        items = OrderItem.objects.filter(order=basket_order)
        serializer = BasketItemSerializer(items, many=True)
        total = basket_order.get_total_price()
        
        return Response({
            'Status': True,
            'OrderID': basket_order.id,
            'Items': serializer.data,
            'Total': total
        })
    
    def post(self, request):
        """Добавить товар в корзину"""
        product_id = request.data.get('product_id')
        shop_id = request.data.get('shop_id')
        quantity = request.data.get('quantity', 1)
        
        if not all([product_id, shop_id]):
            return Response({
                'Status': False,
                'Error': 'Необходимо указать product_id и shop_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
            shop = Shop.objects.get(id=shop_id)
            
            # Проверяем наличие товара в магазине
            product_info = ProductInfo.objects.filter(product=product, shop=shop).first()
            if not product_info or product_info.quantity < int(quantity):
                return Response({
                    'Status': False,
                    'Error': 'Недостаточно товара в наличии'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем или создаем корзину
            basket_order, created = Order.objects.get_or_create(
                user=request.user,
                status='basket',
                defaults={'status': 'basket'}
            )
            
            # Добавляем товар в корзину
            order_item, created = OrderItem.objects.get_or_create(
                order=basket_order,
                product=product,
                shop=shop,
                defaults={'quantity': quantity}
            )
            
            if not created:
                order_item.quantity += int(quantity)
                order_item.save()
            
            return Response({
                'Status': True,
                'Message': 'Товар добавлен в корзину',
                'ItemID': order_item.id
            })
            
        except Product.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Товар не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except Shop.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Магазин не найден'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request):
        """Удалить товар из корзины"""
        item_id = request.data.get('item_id')
        if not item_id:
            return Response({
                'Status': False,
                'Error': 'Необходимо указать item_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order_item = OrderItem.objects.get(
                id=item_id,
                order__user=request.user,
                order__status='basket'
            )
            order_item.delete()
            
            return Response({
                'Status': True,
                'Message': 'Товар удален из корзины'
            })
            
        except OrderItem.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Товар не найден в корзине'
            }, status=status.HTTP_404_NOT_FOUND)


class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления контактами пользователя.
    
    Предоставляет CRUD операции для контактов:
        - list: список контактов
        - create: создание нового контакта
        - retrieve: получение контакта
        - update: полное обновление
        - partial_update: частичное обновление
        - delete: удаление контакта
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Создание нового контакта"""
        required_fields = ['type', 'value']
        
        # Проверка обязательных полей для адреса
        if 'type' in request.data and request.data['type'] == 'address':
            address_fields = ['city', 'street', 'house']
            for field in address_fields:
                if not request.data.get(field):
                    return Response({
                        'Status': False,
                        'Error': f'Для адреса необходимо указать поле {field}'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        for field in required_fields:
            if not request.data.get(field):
                return Response({
                    'Status': False,
                    'Error': f'Необходимо указать поле {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().create(request, *args, **kwargs)


class OrderConfirmView(APIView):
    """
    Подтверждение заказа.
    
    Переводит заказ из статуса 'basket' в 'new',
    списывает товары со склада и отправляет подтверждение на email.
    
    Принимает:
        - order_id: ID заказа в корзине
        - contact_id: ID контакта для доставки
    
    Возвращает:
        - Status: статус операции
        - Order: детали подтвержденного заказа
        - StockUpdates: информация об обновлении остатков
        - Email: статус отправки email
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        DEBUG = settings.DEBUG
        
        # 1. Проверяем наличие обязательных параметров
        order_id = request.data.get('order_id')
        contact_id = request.data.get('contact_id')
        
        if not all([order_id, contact_id]):
            return Response({
                'Status': False,
                'Error': 'Необходимо указать order_id и contact_id',
                'Required': {
                    'order_id': 'ID заказа в корзине',
                    'contact_id': 'ID контакта для доставки'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 2. Получаем и проверяем заказ
            try:
                order = Order.objects.get(
                    id=order_id,
                    user=request.user,
                    status='basket'
                )
            except Order.DoesNotExist:
                return Response({
                    'Status': False,
                    'Error': f'Заказ с ID {order_id} не найден, или не принадлежит вам, или уже подтвержден',
                    'Suggestions': [
                        'Проверьте правильность ID заказа',
                        'Убедитесь, что заказ еще в корзине (статус "basket")',
                        'Проверьте, что это ваш заказ'
                    ]
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 3. Проверяем, что в заказе есть товары
            order_items = OrderItem.objects.filter(order=order)
            if not order_items.exists():
                return Response({
                    'Status': False,
                    'Error': 'Корзина пуста. Добавьте товары перед подтверждением заказа.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 4. Проверяем наличие контакта
            try:
                contact = Contact.objects.get(
                    id=contact_id,
                    user=request.user
                )
            except Contact.DoesNotExist:
                return Response({
                    'Status': False,
                    'Error': f'Контакт с ID {contact_id} не найден или не принадлежит вам',
                    'Suggestions': [
                        'Проверьте правильность ID контакта',
                        'Создайте новый контакт через /api/v1/contacts/'
                    ]
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 5. Проверяем, что контакт содержит все необходимые поля для адреса доставки
            if contact.type == 'address':
                required_address_fields = ['city', 'street', 'house']
                missing_fields = []
                for field in required_address_fields:
                    if not getattr(contact, field):
                        missing_fields.append(field)
                
                if missing_fields:
                    return Response({
                        'Status': False,
                        'Error': f'Контакт адреса должен содержать поля: {", ".join(missing_fields)}',
                        'Missing': missing_fields
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # 6. Проверяем наличие всех товаров в достаточном количестве
            unavailable_items = []
            for item in order_items:
                try:
                    product_info = ProductInfo.objects.get(
                        product=item.product,
                        shop=item.shop
                    )
                    
                    if product_info.quantity < item.quantity:
                        unavailable_items.append({
                            'product': item.product.name,
                            'shop': item.shop.name,
                            'requested': item.quantity,
                            'available': product_info.quantity
                        })
                        
                except ProductInfo.DoesNotExist:
                    unavailable_items.append({
                        'product': item.product.name,
                        'shop': item.shop.name,
                        'requested': item.quantity,
                        'available': 0,
                        'error': 'Товар не найден в магазине'
                    })
            
            if unavailable_items:
                return Response({
                    'Status': False,
                    'Error': 'Недостаточно товаров в наличии',
                    'UnavailableItems': unavailable_items,
                    'Suggestions': [
                        'Уменьшите количество товаров',
                        'Удалите недоступные товары из корзины',
                        'Попробуйте найти аналогичные товары'
                    ]
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 7. Начинаем транзакцию
            try:
                with transaction.atomic():
                    # 8. Обновляем статус заказа
                    order.status = 'new'
                    order.contact = contact
                    order.save()
                    
                    # 9. Обновляем количество товаров на складах
                    updated_products = []
                    for item in order_items:
                        product_info = ProductInfo.objects.get(
                            product=item.product,
                            shop=item.shop
                        )
                        old_quantity = product_info.quantity
                        product_info.quantity -= item.quantity
                        product_info.save()
                        
                        updated_products.append({
                            'product': item.product.name,
                            'shop': item.shop.name,
                            'ordered': item.quantity,
                            'old_stock': old_quantity,
                            'new_stock': product_info.quantity
                        })
                    
                    # 10. Подготавливаем детали заказа
                    order_details = []
                    total_price = 0
                    
                    for item in order_items:
                        try:
                            product_info = ProductInfo.objects.get(
                                product=item.product,
                                shop=item.shop
                            )
                            item_price = product_info.price * item.quantity
                            total_price += item_price
                            
                            order_details.append({
                                'product_id': item.product.id,
                                'product_name': item.product.name,
                                'shop_id': item.shop.id,
                                'shop_name': item.shop.name,
                                'quantity': item.quantity,
                                'price_per_unit': product_info.price,
                                'item_total': item_price
                            })
                        except ProductInfo.DoesNotExist:
                            pass
                    
                    # 11. АСИНХРОННАЯ отправка email с подтверждением заказа
                    email_status = 'pending'
                    try:
                        send_order_confirmation_task.delay(
                            user_email=request.user.email,
                            order_id=order.id
                        )
                        email_status = 'queued'
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Ошибка постановки задачи отправки email для заказа {order.id}: {e}")
                        email_status = 'failed'
                    
                    # 12. Возвращаем успешный ответ
                    response_data = {
                        'Status': True,
                        'Message': 'Заказ успешно подтвержден!',
                        'Order': {
                            'id': order.id,
                            'status': order.status,
                            'status_display': order.get_status_display(),
                            'date': order.dt.strftime('%Y-%m-%d %H:%M:%S'),
                            'total_price': total_price,
                            'contact': {
                                'id': contact.id,
                                'type': contact.type,
                                'value': contact.value,
                                'full_address': f"{contact.city}, {contact.street}, д. {contact.house}" 
                                                if contact.type == 'address' else contact.value
                            },
                            'items': order_details,
                            'items_count': len(order_details)
                        },
                        'StockUpdates': updated_products,
                        'Email': {
                            'status': email_status,
                            'note': 'Email поставлен в очередь на отправку (асинхронно)'
                        },
                        'Instructions': [
                            f'Заказ №{order.id} переведен в статус "Новый"',
                            'Ожидайте подтверждения от магазина',
                            'Вы можете отслеживать статус заказа через /api/v1/orders/',
                            'Для просмотра деталей заказа используйте /api/v1/order/{id}/'
                        ]
                    }
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                    
            except Exception as e:
                return Response({
                    'Status': False,
                    'Error': f'Ошибка при подтверждении заказа: {str(e)}',
                    'Suggestion': 'Попробуйте позже или обратитесь в поддержку'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            import traceback
            return Response({
                'Status': False,
                'Error': f'Неизвестная ошибка: {str(e)}',
                'Traceback': traceback.format_exc() if DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderListView(generics.ListAPIView):
    """
    Список заказов пользователя (исключая корзину).
    
    Возвращает:
        - Status: статус операции
        - Count: количество заказов
        - Orders: массив заказов с деталями
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).exclude(
            status='basket'
        ).order_by('-dt')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'Status': True,
            'Count': queryset.count(),
            'Orders': serializer.data
        })


class OrderDetailView(generics.RetrieveAPIView):
    """
    Детальная информация о заказе.
    
    Возвращает полную информацию о конкретном заказе пользователя.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class PartnerUpdate(APIView):
    """
    Обновление прайс-листа магазина.
    
    Принимает:
        - url: ссылка на YAML файл с данными
        - или file: загруженный YAML файл
    
    Формат YAML:
        shop: Название магазина
        categories: список категорий
        goods: список товаров
    
    Требует авторизации пользователя с типом 'shop'.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):        
        # 1. Проверка аутентификации
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)
        
        # 2. Проверка типа пользователя
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
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)}, status=400)
            
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
                if not file.name.endswith(('.yaml', '.yml')):
                    return JsonResponse(
                        {'Status': False, 'Error': 'Файл должен быть в формате YAML'}, 
                        status=400
                    )
                
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
        
        # 7. Импорт данных в транзакции
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
                        
                        if category.name != category_data['name']:
                            category.name = category_data['name']
                            category.save()
                        
                        category.shops.add(shop)
                
                # Удаляем старые данные о товарах этого магазина
                ProductInfo.objects.filter(shop=shop).delete()
                
                # Импорт товаров
                if 'goods' in data:
                    for product_data in data['goods']:
                        product, _ = Product.objects.get_or_create(
                            name=product_data['name'],
                            category_id=product_data['category']
                        )
                        
                        product_info = ProductInfo.objects.create(
                            product=product,
                            shop=shop,
                            external_id=product_data['id'],
                            model=product_data.get('model', ''),
                            quantity=product_data['quantity'],
                            price=product_data['price'],
                            price_rrc=product_data['price_rrc']
                        )
                        
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
    """
    Управление статусом магазина.
    
    GET: Получить текущий статус магазина
    POST: Изменить статус магазина
        - state: True/False - активен/неактивен
    
    Требует авторизации пользователя с типом 'shop'.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Получить статус магазина"""
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
        """Изменить статус магазина"""
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
    Получение заказов для магазина-партнера.
    
    Возвращает список заказов, содержащих товары данного магазина.
    
    Требует авторизации пользователя с типом 'shop'.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Получить заказы для магазина"""
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)
        
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        
        try:
            shop = Shop.objects.get(user=request.user)
            
            # Оптимизированный запрос с select_related и annotate
            order_items = OrderItem.objects.filter(
                shop=shop
            ).select_related(
                'order', 
                'order__user', 
                'product'
            ).annotate(
                current_price=models.Subquery(
                    ProductInfo.objects.filter(
                        product=models.OuterRef('product'),
                        shop=shop
                    ).values('price')[:1]
                )
            )
            
            orders_data = []
            for item in order_items:
                price = item.current_price or 0
                item_price = price * item.quantity
                
                orders_data.append({
                    'id': item.order.id,
                    'dt': item.order.dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': item.order.status,
                    'user': item.order.user.email,
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'price': item_price
                })
            
            return JsonResponse({
                'Status': True,
                'Orders': orders_data,
                'Count': len(orders_data)
            })
            
        except Shop.DoesNotExist:
            return JsonResponse({'Status': False, 'Error': 'Магазин не найден'}, status=404)


class ConfirmEmailView(APIView):
    """
    Подтверждение email пользователя.
    
    Принимает:
        - token: токен подтверждения
        - email: email пользователя
    
    Возвращает:
        - Status: статус операции
        - Message: сообщение
        - Token: токен для авторизации
        - User: данные пользователя
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        email = request.data.get('email')
        
        if not all([token, email]):
            return Response({
                'Status': False,
                'Error': 'Необходимо указать token и email'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            confirm_token = ConfirmEmailToken.objects.get(
                user=user,
                key=token
            )
            
            user.is_active = True
            user.save()
            confirm_token.delete()
            
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'Status': True,
                'Message': 'Email успешно подтвержден!',
                'Token': token.key,
                'User': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'type': user.type,
                    'is_active': user.is_active
                }
            })
            
        except User.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Пользователь не найден'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except ConfirmEmailToken.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Неверный токен подтверждения'
            }, status=status.HTTP_400_BAD_REQUEST)


class ViewSentEmailsView(APIView):
    """
    Просмотр отправленных email (только для демо-режима).
    
    Возвращает список всех сохраненных email сообщений.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        emails = DemoEmailService.list_sent_emails()
        
        return Response({
            'Status': True,
            'Count': len(emails),
            'Emails': emails
        })


class TestSentryView(APIView):
    """
    Тестовый эндпоинт для проверки интеграции Sentry.
    
    Намеренно вызывает исключение для отправки в Sentry.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            raise ValueError("Тестовое исключение для Sentry")
        except Exception as e:
            import sentry_sdk
            sentry_sdk.capture_exception(e)
            return Response({
                'Status': False,
                'Error': 'Исключение отправлено в Sentry',
                'Exception': str(e)
            })