from aiohttp import web
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import json

from models import Advertisement, User
from utils import (
    AdvertisementCreate,
    AdvertisementUpdate,
    AdvertisementResponse,
    AdvertisementListResponse,
    parse_json_request,
    validate_pagination_params,
    create_error_response,
    get_required_auth,
    get_optional_auth
)
from auth import (
    AuthMiddleware,
    UserRegister,
    UserLogin,
    register_user,
    authenticate_user,
    TokenData
)


class AdvertisementRoutes:
    def __init__(self, db):
        self.db = db
        self.auth_middleware = AuthMiddleware()
    
    def setup_routes(self, app: web.Application):

        app.router.add_post('/api/register', self.register)
        app.router.add_post('/api/login', self.login)
        
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
            "authentication_endpoints": {
                "POST /api/register": "Регистрация нового пользователя",
                "POST /api/login": "Авторизация и получение JWT токена"
            },
            "advertisement_endpoints": {
                "GET /api/advertisements": "Получить все объявления с пагинацией",
                "GET /api/advertisements/{id}": "Получить конкретное объявление",
                "POST /api/advertisements": "Создать новое объявление (требует Bearer токен)",
                "PUT /api/advertisements/{id}": "Полное обновление объявления (только владелец)",
                "PATCH /api/advertisements/{id}": "Частичное обновление объявления (только владелец)",
                "DELETE /api/advertisements/{id}": "Удалить объявление (только владелец)"
            },
            "parameters": {
                "page": "Номер страницы (default: 1)",
                "per_page": "Количество элементов на странице (default: 20, max: 100)",
                "owner_id": "Фильтр по ID владельца (опционально)"
            },
            "authentication": "Используйте Bearer токен в заголовке Authorization для защищенных эндпоинтов"
        }
        return web.json_response(response_data)
    
    
    async def register(self, request: web.Request) -> web.Response:
        try:
            data = await parse_json_request(request)
            user_data = UserRegister(**data)
            
            user = await register_user(user_data.username, user_data.password)
            
            if not user:
                return web.json_response(
                    create_error_response("Пользователь с таким именем уже существует", 409),
                    status=409
                )
            
            return web.json_response({
                "message": "Пользователь успешно зарегистрирован",
                "user": user.to_dict()
            }, status=201)
            
        except ValueError as e:
            return web.json_response(
                create_error_response(str(e)),
                status=400
            )
        except Exception as e:
            return web.json_response(
                create_error_response(f"Ошибка при регистрации: {str(e)}", 500),
                status=500
            )
    
    async def login(self, request: web.Request) -> web.Response:
        try:
            data = await parse_json_request(request)
            login_data = UserLogin(**data)
            
            user = await authenticate_user(login_data.username, login_data.password)
            
            if not user:
                return web.json_response(
                    create_error_response("Неверное имя пользователя или пароль", 401),
                    status=401
                )
            
            token_data = TokenData(user_id=user.id, username=user.username)
            access_token = self.auth_middleware.create_access_token(token_data)
            
            return web.json_response({
                "access_token": access_token,
                "token_type": "bearer",
                "user": user.to_dict()
            })
            
        except ValueError as e:
            return web.json_response(
                create_error_response(str(e)),
                status=400
            )
        except Exception as e:
            return web.json_response(
                create_error_response(f"Ошибка при авторизации: {str(e)}", 500),
                status=500
            )
    
    async def get_advertisements(self, request: web.Request) -> web.Response:
        async with self.db.async_session() as session:
            try:
                page = int(request.query.get('page', 1))
                per_page = int(request.query.get('per_page', 20))
                owner_id = request.query.get('owner_id')
                
                page, per_page = validate_pagination_params(page, per_page)
                
                query = select(Advertisement).order_by(Advertisement.created_at.desc())
                
                if owner_id:
                    query = query.where(Advertisement.owner_id == owner_id)
                
                result = await session.execute(
                    query.offset((page - 1) * per_page).limit(per_page)
                )
                advertisements = result.scalars().all()
                
                count_query = select(func.count()).select_from(Advertisement)
                if owner_id:
                    count_query = count_query.where(Advertisement.owner_id == owner_id)
                
                total_result = await session.execute(count_query)
                total = total_result.scalar()
                
                response_data = AdvertisementListResponse(
                    advertisements=[
                        AdvertisementResponse(**ad.to_dict()) 
                        for ad in advertisements
                    ],
                    total=total,
                    page=page,
                    per_page=per_page,
                    pages=(total + per_page - 1) // per_page if total > 0 else 0
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
            user_data = get_required_auth(request)
            
            data = await parse_json_request(request)
            advertisement_data = AdvertisementCreate(**data)
            
            async with self.db.async_session() as session:
                advertisement = Advertisement(
                    title=advertisement_data.title,
                    description=advertisement_data.description,
                    owner_id=user_data.user_id
                )
                
                session.add(advertisement)
                await session.commit()
                
                await session.refresh(advertisement)
                
                response_data = AdvertisementResponse(**advertisement.to_dict())
                
                return web.json_response(
                    response_data.model_dump(),
                    status=201
                )
                
        except web.HTTPException as e:
            return web.json_response(
                create_error_response(e.reason, e.status_code),
                status=e.status_code
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
            user_data = get_required_auth(request)
            
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
                
                if advertisement.owner_id != user_data.user_id:
                    return web.json_response(
                        create_error_response("Нет прав на изменение этого объявления", 403),
                        status=403
                    )
                
                advertisement.title = update_data.title
                advertisement.description = update_data.description
                
                await session.commit()
                await session.refresh(advertisement)
                
                response_data = AdvertisementResponse(**advertisement.to_dict())
                
                return web.json_response(response_data.model_dump())
                
        except web.HTTPException as e:
            return web.json_response(
                create_error_response(e.reason, e.status_code),
                status=e.status_code
            )
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
            user_data = get_required_auth(request)
            
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
                
                if advertisement.owner_id != user_data.user_id:
                    return web.json_response(
                        create_error_response("Нет прав на изменение этого объявления", 403),
                        status=403
                    )
                
                if update_data.title is not None:
                    advertisement.title = update_data.title
                
                if update_data.description is not None:
                    advertisement.description = update_data.description
                
                await session.commit()
                await session.refresh(advertisement)
                
                response_data = AdvertisementResponse(**advertisement.to_dict())
                
                return web.json_response(response_data.model_dump())
                
        except web.HTTPException as e:
            return web.json_response(
                create_error_response(e.reason, e.status_code),
                status=e.status_code
            )
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
        
        try:
            user_data = get_required_auth(request)
            
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
                
                if advertisement.owner_id != user_data.user_id:
                    return web.json_response(
                        create_error_response("Нет прав на удаление этого объявления", 403),
                        status=403
                    )
                
                await session.delete(advertisement)
                await session.commit()
                
                return web.json_response(
                    {"message": "Объявление успешно удалено"},
                    status=200
                )
                
        except web.HTTPException as e:
            return web.json_response(
                create_error_response(e.reason, e.status_code),
                status=e.status_code
            )
        except Exception as e:
            return web.json_response(
                create_error_response(f"Ошибка при удалении объявления: {str(e)}", 500),
                status=500
            )