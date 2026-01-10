import asyncio
import aiohttp
import asyncpg
from typing import List, Dict, Optional
import logging
from config import DB_CONFIG, SWAPI_BASE_URL, PEOPLE_ENDPOINT, MAX_CONCURRENT_REQUESTS, BATCH_SIZE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StarWarsDataLoader:
    def __init__(self):
        self.base_url = SWAPI_BASE_URL
        self.session = None
        self.db_pool = None
        
    async def init_session(self):
        self.session = aiohttp.ClientSession()
        
    async def init_db_pool(self):
        self.db_pool = await asyncpg.create_pool(**DB_CONFIG, min_size=5, max_size=20)
        
    async def close(self):
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()
            
    async def get_total_count(self) -> int:
        try:
            async with self.session.get(f"{self.base_url}{PEOPLE_ENDPOINT}") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('total_records', 0)
                else:
                    logger.error(f"Ошибка при получении общего количества: {response.status}")
                    return 0
        except Exception as e:
            logger.error(f"Исключение при получении общего количества: {e}")
            return 0
            
    async def fetch_character(self, character_id: int) -> Optional[Dict]:
        url = f"{self.base_url}{PEOPLE_ENDPOINT}/{character_id}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('message') == 'ok':
                        properties = data['result']['properties']
                        
                        character_data = {
                            'id': int(data['result']['uid']),
                            'name': properties.get('name', ''),
                            'birth_year': properties.get('birth_year', ''),
                            'eye_color': properties.get('eye_color', ''),
                            'gender': properties.get('gender', ''),
                            'hair_color': properties.get('hair_color', ''),
                            'homeworld': properties.get('homeworld', ''),
                            'mass': properties.get('mass', ''),
                            'skin_color': properties.get('skin_color', '')
                        }
                        return character_data
                elif response.status == 404:
                    logger.debug(f"Персонаж с ID {character_id} не найден")
                else:
                    logger.warning(f"Ошибка {response.status} для персонажа {character_id}")
                    
        except Exception as e:
            logger.error(f"Ошибка при получении персонажа {character_id}: {e}")
            
        return None
        
    async def save_characters_batch(self, characters: List[Dict]):
        if not characters:
            return
            
        query = """
        INSERT INTO characters 
        (id, name, birth_year, eye_color, gender, hair_color, homeworld, mass, skin_color)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            birth_year = EXCLUDED.birth_year,
            eye_color = EXCLUDED.eye_color,
            gender = EXCLUDED.gender,
            hair_color = EXCLUDED.hair_color,
            homeworld = EXCLUDED.homeworld,
            mass = EXCLUDED.mass,
            skin_color = EXCLUDED.skin_color,
            updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            async with self.db_pool.acquire() as conn:
                records = []
                for char in characters:
                    records.append((
                        char['id'],
                        char['name'],
                        char['birth_year'],
                        char['eye_color'],
                        char['gender'],
                        char['hair_color'],
                        char['homeworld'],
                        char['mass'],
                        char['skin_color']
                    ))
                
                await conn.executemany(query, records)
                logger.info(f"Сохранено {len(characters)} персонажей в базу данных")
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении пачки персонажей: {e}")
            
    async def process_characters(self, start_id: int = 1, end_id: Optional[int] = None):
        if end_id is None:
            end_id = await self.get_total_count()
            if end_id == 0:
                end_id = 100
                
        logger.info(f"Начинаем загрузку персонажей с ID от {start_id} до {end_id}")
        
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        characters_batch = []
        successful_count = 0
        failed_count = 0
        
        async def fetch_with_semaphore(char_id):
            nonlocal successful_count, failed_count
            async with semaphore:
                character = await self.fetch_character(char_id)
                if character:
                    successful_count += 1
                    return character
                else:
                    failed_count += 1
                    return None
                    
        tasks = []
        for char_id in range(start_id, end_id + 1):
            tasks.append(fetch_with_semaphore(char_id))
            
        for i in range(0, len(tasks), BATCH_SIZE):
            batch_tasks = tasks[i:i + BATCH_SIZE]
            batch_results = await asyncio.gather(*batch_tasks)
            
            valid_characters = [char for char in batch_results if char is not None]
            
            if valid_characters:
                await self.save_characters_batch(valid_characters)
                characters_batch.extend(valid_characters)
                

            processed = i + len(batch_tasks)
            logger.info(f"Обработано: {processed}/{len(tasks)}. Успешно: {successful_count}, Ошибок: {failed_count}")
            
        return characters_batch
        
    async def get_all_characters_from_api(self):
        all_characters = []
        page = 1
        
        while True:
            url = f"{self.base_url}{PEOPLE_ENDPOINT}?page={page}&limit=100"
            
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        tasks = []
                        for char_info in data.get('results', []):
                            char_url = char_info.get('url', '')
                            if char_url:
                                char_id = char_url.split('/')[-1]
                                tasks.append(self.fetch_character(char_id))
                                
                        characters = await asyncio.gather(*tasks)
                        valid_characters = [char for char in characters if char is not None]
                        
                        if valid_characters:
                            await self.save_characters_batch(valid_characters)
                            all_characters.extend(valid_characters)
                            
                        logger.info(f"Загружено {len(valid_characters)} персонажей со страницы {page}")
                        
                        if not data.get('next'):
                            break
                        page += 1
                        
                    else:
                        logger.error(f"Ошибка при получении страницы {page}: {response.status}")
                        break
                        
            except Exception as e:
                logger.error(f"Исключение при получении страницы {page}: {e}")
                break
                
        return all_characters
        
    async def run(self, method: str = 'sequential'):
        try:
            await self.init_session()
            await self.init_db_pool()
            
            if method == 'sequential':
                characters = await self.process_characters()
            else:
                characters = await self.get_all_characters_from_api()
                
            logger.info(f"Загрузка завершена. Всего загружено {len(characters)} персонажей")
            
            await self.print_statistics()
            
            return characters
            
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            raise
        finally:
            await self.close()
            
    async def print_statistics(self):
        try:
            async with self.db_pool.acquire() as conn:
                total = await conn.fetchval("SELECT COUNT(*) FROM characters")
                logger.info(f"Всего персонажей в базе: {total}")
                
                gender_stats = await conn.fetch(
                    "SELECT gender, COUNT(*) as count FROM characters GROUP BY gender ORDER BY count DESC"
                )
                logger.info("Статистика по гендерам:")
                for stat in gender_stats:
                    logger.info(f"  {stat['gender']}: {stat['count']}")
                    
                top_names = await conn.fetch(
                    "SELECT name, gender, birth_year FROM characters ORDER BY id LIMIT 10"
                )
                logger.info("Первые 10 персонажей:")
                for char in top_names:
                    logger.info(f"  {char['name']} ({char['gender']}, род. {char['birth_year']})")
                    
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")

async def main():
    loader = StarWarsDataLoader()

    characters = await loader.run(method='pagination')
    
    print(f"\nЗагрузка завершена! Загружено {len(characters)} персонажей.")

if __name__ == "__main__":
    asyncio.run(main())