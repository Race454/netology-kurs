from aiohttp import web
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import json

from models import Advertisement
from utils import (
    AdvertisementCreate,
    AdvertisementUpdate,
    AdvertisementResponse,
    AdvertisementListResponse,
    parse_json_request,
    validate_pagination_params,
    create_error_response
)

class AdvertisementRoutes:
    def __init__(self, db):
        self.db = db
    
    def setup_routes(self, app: web.Application):
        """Настройка маршрутов"""
        app.router.add_get('/api/advertisements', self.get_advertisements)
        app.router.add_get('/api/advertisements/{id}', self.get_advertisement)
        app.router.add_post('/api/advertisements', self.create_advertisement)
        app.router.add_put('/api/advertisements/{id}', self.update_advertisement)
        app.router.add_patch('/api/advertisements/{id}', self.partial_update_advertisement)
        app.router.add_delete('/api/advertisements/{id}', self.delete_advertisement)
        app.router.add_get('/', self.index)
    
    async def index(self, request: web.Request) -> web.Response:
        """Корневой маршрут"""
        response_data = {
            "message": "Добро пожаловать в API для сайта объявлений (aiohttp)",
            "version": "1.0.0",
            "endpoints": {
                "GET /api/advertisements": "Получить все объявления с пагинацией",
                "GET /api/advertisements/{id}": "Получить конкретное объявление",
                "POST /api/advertisements": "Создать новое объявление",
                "PUT /api/advertisements/{id}": "Полное обновление объявления",
                "PATCH /api/advertisements/{id}": "Частичное обновление объявления",
                "DELETE /api/advertisements/{id}": "Удалить объявление"
            },
            "parameters": {
                "page": "Номер страницы (default: 1)",
                "per_page": "Количество элементов на странице (default: 20, max: 100)",
                "owner": "Фильтр по владельцу (опционально)"
            }
        }
        return web.json_response(response_data)
    
    async def get_advertisements(self, request: web.Request) -> web.Response:
        async with self.db.async_session() as session:
            try:
                page = int(request.query.get('page', 1))
                per_page = int(request.query.get('per_page', 20))
                owner = request.query.get('owner')
                
                page, per_page = validate_pagination_params(page, per_page)
                
                query = select(Advertisement).order_by(Advertisement.created_at.desc())
                
                if owner:
                    query = query.where(Advertisement.owner == owner)
                
                result = await session.execute(
                    query.offset((page - 1) * per_page).limit(per_page)
                )
                advertisements = result.scalars().all()
                
                count_query = select(Advertisement)
                if owner:
                    count_query = count_query.where(Advertisement.owner == owner)
                
                total_result = await session.execute(
                    select(Advertisement).where(count_query.whereclause if owner else True)
                )
                total = len(total_result.scalars().all())
                
                response_data = AdvertisementListResponse(
                    advertisements=[
                        AdvertisementResponse(**ad.to_dict()) 
                        for ad in advertisements
                    ],
                    total=total,
                    page=page,
                    per_page=per_page,
                    pages=(total + per_page - 1) // per_page
                )
                
                return web.json_response(response_data.model_dump())
                
            except ValueError as e:
                return web.json_response(
                    create_error_response(str(e)),
                    status=400
                )
            except Exception as e:
                return web.json_response(
                    create_error_response("Внутренняя ошибка сервера", 500),
                    status=500
                )
    
    async def get_advertisement(self, request: web.Request) -> web.Response:
        ad_id = request.match_info['id']
        
        async with self.db.async_session() as session:
            try:
                result = await session.execute(
                    select(Advertisement).where(Advertisement.id == ad_id)
                )
                advertisement = result.scalar_one_or_none()
                
                if not advertisement:
                    return web.json_response(
                        create_error_response("Объявление не найдено", 404),
                        status=404
                    )
                
                response_data = AdvertisementResponse(**advertisement.to_dict())
                return web.json_response(response_data.model_dump())
                
            except Exception as e:
                return web.json_response(
                    create_error_response("Внутренняя ошибка сервера", 500),
                    status=500
                )
    
    async def create_advertisement(self, request: web.Request) -> web.Response:
        try:
            data = await parse_json_request(request)
            
            advertisement_data = AdvertisementCreate(**data)
            
            async with self.db.async_session() as session:
                advertisement = Advertisement(
                    title=advertisement_data.title,
                    description=advertisement_data.description,
                    owner=advertisement_data.owner
                )
                
                session.add(advertisement)
                await session.commit()
                
                await session.refresh(advertisement)
                
                response_data = AdvertisementResponse(**advertisement.to_dict())
                
                return web.json_response(
                    response_data.model_dump(),
                    status=201
                )
                
        except ValueError as e:
            return web.json_response(
                create_error_response(str(e)),
                status=400
            )
        except Exception as e:
            return web.json_response(
                create_error_response(f"Ошибка при создании объявления: {str(e)}", 500),
                status=500
            )
    
    async def update_advertisement(self, request: web.Request) -> web.Response:
        ad_id = request.match_info['id']
        
        try:
            data = await parse_json_request(request)
            
            update_data = AdvertisementCreate(**data)
            
            async with self.db.async_session() as session:
                result = await session.execute(
                    select(Advertisement).where(Advertisement.id == ad_id)
                )
                advertisement = result.scalar_one_or_none()
                
                if not advertisement:
                    return web.json_response(
                        create_error_response("Объявление не найдено", 404),
                        status=404
                    )
                
                advertisement.title = update_data.title
                advertisement.description = update_data.description
                advertisement.owner = update_data.owner
                
                await session.commit()
                await session.refresh(advertisement)
                
                response_data = AdvertisementResponse(**advertisement.to_dict())
                
                return web.json_response(response_data.model_dump())
                
        except ValueError as e:
            return web.json_response(
                create_error_response(str(e)),
                status=400
            )
        except Exception as e:
            return web.json_response(
                create_error_response(f"Ошибка при обновлении объявления: {str(e)}", 500),
                status=500
            )
    
    async def partial_update_advertisement(self, request: web.Request) -> web.Response:
        ad_id = request.match_info['id']
        
        try:
            data = await parse_json_request(request)
            
            update_data = AdvertisementUpdate(**data)
            
            async with self.db.async_session() as session:
                result = await session.execute(
                    select(Advertisement).where(Advertisement.id == ad_id)
                )
                advertisement = result.scalar_one_or_none()
                
                if not advertisement:
                    return web.json_response(
                        create_error_response("Объявление не найдено", 404),
                        status=404
                    )
                
                if update_data.title is not None:
                    advertisement.title = update_data.title
                
                if update_data.description is not None:
                    advertisement.description = update_data.description
                
                if update_data.owner is not None:
                    advertisement.owner = update_data.owner
                
                await session.commit()
                await session.refresh(advertisement)
                
                response_data = AdvertisementResponse(**advertisement.to_dict())
                
                return web.json_response(response_data.model_dump())
                
        except ValueError as e:
            return web.json_response(
                create_error_response(str(e)),
                status=400
            )
        except Exception as e:
            return web.json_response(
                create_error_response(f"Ошибка при обновлении объявления: {str(e)}", 500),
                status=500
            )
    
    async def delete_advertisement(self, request: web.Request) -> web.Response:
        ad_id = request.match_info['id']
        
        async with self.db.async_session() as session:
            try:
                result = await session.execute(
                    select(Advertisement).where(Advertisement.id == ad_id)
                )
                advertisement = result.scalar_one_or_none()
                
                if not advertisement:
                    return web.json_response(
                        create_error_response("Объявление не найдено", 404),
                        status=404
                    )
                
                await session.delete(advertisement)
                await session.commit()
                
                return web.json_response(
                    {"message": "Объявление успешно удалено"},
                    status=200
                )
                
            except Exception as e:
                return web.json_response(
                    create_error_response(f"Ошибка при удалении объявления: {str(e)}", 500),
                    status=500
                )