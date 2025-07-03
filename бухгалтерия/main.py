from datetime import datetime
from application.salary import calculate_salary
from application.db.people import get_employees

if __name__ == '__main__':
    print(f"Текущая дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    calculate_salary()
    get_employees()