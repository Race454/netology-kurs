from django.shortcuts import render, get_object_or_404
from phones.models import Phone

def home(request):
    return render(
        request,
        'home.html'
    )

def show_catalog(request):
    sort = request.GET.get('sort', 'name')
    
    if sort == 'name':
        phones = Phone.objects.all().order_by('name')
    elif sort == 'min_price':
        phones = Phone.objects.all().order_by('price')
    elif sort == 'max_price':
        phones = Phone.objects.all().order_by('-price')
    else:
        phones = Phone.objects.all()
    
    return render(
        request,
        'catalog.html',
        {'phones': phones}
    )

def show_product(request, slug):
    phone = get_object_or_404(Phone, slug=slug)
    return render(
        request,
        'product.html',
        {'phone': phone}
    )