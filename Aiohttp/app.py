from aiohttp import web
from aiohttp_cors import setup as setup_cors, ResourceOptions
import asyncio
import logging

from database import db
from routes import AdvertisementRoutes
from config import config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db(app: web.Application):
    logger.info("Инициализация базы данных...")
    await db.init_db()
    logger.info("База данных инициализирована")

async def create_app() -> web.Application:
    app = web.Application()
    
    app.on_startup.append(init_db)
    
    cors = setup_cors(app, defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
    
    routes = AdvertisementRoutes(db)
    routes.setup_routes(app)
    
    for route in list(app.router.routes()):
        cors.add(route)
    
    @web.middleware
    async def error_middleware(request, handler):
        try:
            response = await handler(request)
            return response
        except web.HTTPException as ex:
            return web.json_response(
                {
                    "error": {
                        "message": ex.reason,
                        "status_code": ex.status_code
                    }
                },
                status=ex.status_code
            )
        except Exception as e:
            logger.error(f"Необработанная ошибка: {str(e)}")
            return web.json_response(
                {
                    "error": {
                        "message": "Внутренняя ошибка сервера",
                        "status_code": 500
                    }
                },
                status=500
            )
    
    app.middlewares.append(error_middleware)
    
    return app

async def main():
    app = await create_app()
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, config.HOST, config.PORT)
    
    logger.info(f"Сервер запущен на http://{config.HOST}:{config.PORT}")
    logger.info(f"Документация API доступна по адресу: http://{config.HOST}:{config.PORT}/")
    
    await site.start()
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Остановка сервера...")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())