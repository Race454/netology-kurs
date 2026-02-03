from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, Shop, Category, Product, ProductInfo, 
    Parameter, ProductParameter, Contact, Order, 
    OrderItem, ConfirmEmailToken
)
from rest_framework.authtoken.models import Token


# Сначала определим базовые сериализаторы
class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'url', 'state']
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'category']
        read_only_fields = ['id']


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ['id', 'name']
        read_only_fields = ['id']


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ['parameter', 'value']


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    parameters = ProductParameterSerializer(source='product_parameters', many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = ['id', 'external_id', 'model', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'parameters']
        read_only_fields = ['id']


# Теперь сериализаторы для API
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'company', 'position', 'type']
        read_only_fields = ['id']


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'),
                              email=email, password=password)
            if not user:
                raise serializers.ValidationError('Неверные учетные данные')
        else:
            raise serializers.ValidationError('Необходимо указать email и пароль')
        
        attrs['user'] = user
        return attrs


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'password2']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
            username=validated_data['email']  # Используем email как username
        )
        # Создаем токен для нового пользователя
        Token.objects.create(user=user)
        return user


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'type', 'value', 'city', 'street', 'house', 'building', 'apartment', 'user']
        read_only_fields = ['id', 'user']
    
    def create(self, validated_data):
        # Автоматически привязываем контакт к текущему пользователю
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'shop', 'shop_name', 'quantity', 'price', 'total_price']
        read_only_fields = ['id']
    
    def get_price(self, obj):
        try:
            product_info = ProductInfo.objects.get(product=obj.product, shop=obj.shop)
            return product_info.price
        except ProductInfo.DoesNotExist:
            return 0
    
    def get_total_price(self, obj):
        return obj.get_item_price()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'user_email', 'dt', 'status', 'contact', 'items', 'total_price']
        read_only_fields = ['id', 'user', 'dt']
    
    def get_total_price(self, obj):
        return obj.get_total_price()


class BasketItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'shop', 'shop_name', 'quantity', 'price', 'total_price']
    
    def get_price(self, obj):
        try:
            product_info = ProductInfo.objects.get(product=obj.product, shop=obj.shop)
            return product_info.price
        except ProductInfo.DoesNotExist:
            return 0
    
    def get_total_price(self, obj):
        return obj.get_item_price()


class ProductInfoDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    parameters = ProductParameterSerializer(source='product_parameters', many=True, read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    
    class Meta:
        model = ProductInfo
        fields = ['id', 'external_id', 'model', 'product', 'shop', 'shop_name', 
                  'quantity', 'price', 'price_rrc', 'parameters']
        read_only_fields = ['id']