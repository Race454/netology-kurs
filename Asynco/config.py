import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'starwars_db')
}

SWAPI_BASE_URL = "https://www.swapi.tech/api"
PEOPLE_ENDPOINT = "/people"

MAX_CONCURRENT_REQUESTS = 10
BATCH_SIZE = 50 