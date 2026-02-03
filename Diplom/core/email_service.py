import logging
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class DemoEmailService:
    # Демонстрационный сервис для отправки email
    
    @staticmethod
    def send_confirm_email(user_email, token):
        subject = "Подтверждение регистрации в PhoneStore"
        message = f"""
        Здравствуйте!
        
        Для подтверждения регистрации перейдите по ссылке:
        http://localhost:8000/api/v1/user/confirm-email/
        
        Или используйте токен: {token}
        
        Ваши данные для подтверждения:
        Email: {user_email}
        Токен: {token}
        
        ---
        Это демо-версия. В реальном проекте здесь была бы ссылка для подтверждения.
        """
        
        # Логируем в консоль
        print("\n" + "="*60)
        print("ДЕМО: ОТПРАВКА EMAIL ДЛЯ ПОДТВЕРЖДЕНИЯ РЕГИСТРАЦИИ")
        print("="*60)
        print(f"Кому: {user_email}")
        print(f"Тема: {subject}")
        print(f"Токен: {token}")
        print("="*60 + "\n")
        
        # Сохраняем в файл
        email_data = {
            'type': 'confirm_email',
            'to': user_email,
            'subject': subject,
            'token': token,
            'timestamp': datetime.now().isoformat(),
            'message': message
        }
        
        DemoEmailService._save_to_file(email_data)
        
        return True
    
    @staticmethod
    def send_order_confirmation(user_email, order):
        # Отправка email с подтверждением заказа
        subject = f"Подтверждение заказа №{order.id}"
        
        order_items = []
        total = 0
        for item in order.items.all():
            try:
                product_info = item.product.product_infos.get(shop=item.shop)
                item_price = product_info.price * item.quantity
                total += item_price
                order_items.append({
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'price': item_price
                })
            except:
                pass
        
        message = f"""
        Здравствуйте!
        
        Ваш заказ №{order.id} успешно оформлен.
        
        Детали заказа:
        Дата: {order.dt.strftime('%d.%m.%Y %H:%M')}
        Статус: {order.get_status_display()}
        Общая сумма: {total} руб.
        
        Состав заказа:
        {chr(10).join([f"- {item['product']} x{item['quantity']}: {item['price']} руб." for item in order_items])}
        
        Контактная информация:
        Email: {user_email}
        
        ---
        Это демо-версия. В реальном проекте здесь были бы детали доставки и контакты.
        """
        
        # Логируем в консоль
        print("\n" + "="*60)
        print("ДЕМО: ОТПРАВКА EMAIL ПОДТВЕРЖДЕНИЯ ЗАКАЗА")
        print("="*60)
        print(f"Кому: {user_email}")
        print(f"Тема: {subject}")
        print(f"Заказ №: {order.id}")
        print(f"Сумма: {total} руб.")
        print("="*60 + "\n")
        
        # Сохраняем в файл
        email_data = {
            'type': 'order_confirmation',
            'to': user_email,
            'subject': subject,
            'order_id': order.id,
            'order_total': total,
            'timestamp': datetime.now().isoformat(),
            'message': message
        }
        
        DemoEmailService._save_to_file(email_data)
        
        return True
    
    @staticmethod
    def _save_to_file(email_data):
        #  Сохраняем email данные в JSON файл
        emails_dir = Path('sent_emails')
        emails_dir.mkdir(exist_ok=True)
        
        filename = emails_dir / f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(email_data, f, ensure_ascii=False, indent=2)
        
        print(f"Email данные сохранены в: {filename}")
    
    @staticmethod
    def list_sent_emails():
        # Показывает список отправленных email
        emails_dir = Path('sent_emails')
        if not emails_dir.exists():
            return []
        
        emails = []
        for file in emails_dir.glob('email_*.json'):
            with open(file, 'r', encoding='utf-8') as f:
                emails.append(json.load(f))
        
        return emails