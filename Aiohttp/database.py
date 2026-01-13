from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from models import Base
from config import config

class Database:
    def __init__(self):
        self.engine = create_async_engine(
            config.DATABASE_URL,
            echo=config.DEBUG,
            future=True
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def init_db(self):
        async with self.engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='advertisements'")
            )
            table_exists = result.fetchone()
            
            if not table_exists:
                await conn.run_sync(Base.metadata.create_all)
                print("База данных создана")
            else:
                print("База данных уже существует")
    
    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            yield session

db = Database()