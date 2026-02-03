from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Contact, OrderItem
from rest_framework.authtoken.models import Token


class UserLoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(label='Email')
    first_name = forms.CharField(label='Имя', max_length=30)
    last_name = forms.CharField(label='Фамилия', max_length=30)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
            Token.objects.create(user=user)
        return user


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['type', 'value', 'city', 'street', 'house', 'building', 'apartment']
        widgets = {
            'type': forms.Select(choices=Contact.CONTACT_TYPE_CHOICES)
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'shop', 'quantity']


class OrderForm(forms.Form):
    contact_id = forms.IntegerField(label='ID контакта')