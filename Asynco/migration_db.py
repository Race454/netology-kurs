import asyncio
import asyncpg
from config import DB_CONFIG

async def create_tables():
    """Создание таблиц в базе данных"""
    
    # SQL для создания таблицы персонажей
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        birth_year VARCHAR(20),
        eye_color VARCHAR(50),
        gender VARCHAR(50),
        hair_color VARCHAR(50),
        homeworld VARCHAR(100),
        mass VARCHAR(20),
        skin_color VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name);
    CREATE INDEX IF NOT EXISTS idx_characters_gender ON characters(gender);
    """
    
    conn = None
    try:
        # Подключаемся к базе данных
        conn = await asyncpg.connect(**DB_CONFIG)
        
        # Создаем таблицу
        await conn.execute(create_table_sql)
        
        print("Таблица 'characters' успешно создана или уже существует")
        
    except Exception as e:
        print(f"Ошибка при создании таблицы: {e}")
        raise
    finally:
        if conn:
            await conn.close()

async def drop_tables():
    """Удаление таблиц (для пересоздания)"""
    
    conn = None
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        await conn.execute("DROP TABLE IF EXISTS characters;")
        print("Таблица 'characters' удалена")
    except Exception as e:
        print(f"Ошибка при удалении таблицы: {e}")
    finally:
        if conn:
            await conn.close()

async def reset_database():
    """Сброс базы данных (удаление и пересоздание таблиц)"""
    await drop_tables()
    await create_tables()

if __name__ == "__main__":
    # Запуск миграции
    asyncio.run(create_tables())
    
    # Для сброса базы данных используйте:
    # asyncio.run(reset_database())