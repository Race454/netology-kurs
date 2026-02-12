# core/tasks.py
from celery import shared_task
from .email_service import DemoEmailService
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_confirm_email_task(user_email, token):
    """
    Асинхронная отправка email с подтверждением регистрации.
    """
    try:
        DemoEmailService.send_confirm_email(user_email, token)
        logger.info(f"Email подтверждения отправлен на {user_email}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки email подтверждения на {user_email}: {e}")
        return False


@shared_task
def send_order_confirmation_task(user_email, order_id):
    """
    Асинхронная отправка email с подтверждением заказа.
    """
    try:
        from .models import Order
        order = Order.objects.get(id=order_id)
        DemoEmailService.send_order_confirmation(user_email, order)
        logger.info(f"Подтверждение заказа {order_id} отправлено на {user_email}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки подтверждения заказа {order_id}: {e}")
        return False
    
@shared_task
def create_product_thumbnails(product_id):
    """Асинхронное создание миниатюр для товара"""
    from .models import Product
    from easy_thumbnails.files import get_thumbnailer
    
    try:
        product = Product.objects.get(id=product_id)
        if product.image:
            # Генерация миниатюр разных размеров
            sizes = [(200, 200), (400, 400), (800, 800)]
            for size in sizes:
                thumb = get_thumbnailer(product.image).get_thumbnail({
                    'size': size,
                    'crop': True,
                    'upscale': True,
                })
                print(f"Создана миниатюра {size}: {thumb.url}")
        return True
    except Exception as e:
        logger.error(f"Ошибка обработки изображения: {e}")
        return False