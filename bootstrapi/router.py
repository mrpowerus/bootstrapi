import json
import typing 

from urllib.parse import unquote

from starlette.responses import Response
from fastapi import APIRouter, Request
from fastapi.routing import APIRoute, APIRouter
from fastapi.encoders import jsonable_encoder

from sqlalchemy.engine import Engine
from sqlalchemy.ext.automap import AutomapBase
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from bootstrapi.sqlalchemy import AutoQuery
from bootstrapi.conversion import sqlalchemy_to_pydantic

class BootstrAPIJSONResponse(Response):
    """Each reponse will be formatted by this class.
    """    
    media_type = "application/json"
    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            separators=(",", ":"),
        ).encode("utf-8")

class BootstrAPIRouter(APIRouter):

    def __init__(self, engine:Engine, Base:AutomapBase,*args, **kwargs):
        self.default_response_class=BootstrAPIJSONResponse
        self.engine = engine
        self.Base = Base
        super(APIRouter).__init__(*args,**kwargs)
    
    def _get(self,id=None, request:Request=None):
        query = self.__get_autoquery_from_request(request)
        url_query = unquote(str(request.query_params)).replace('+',' ')
        result = query.apply_odataquery(url_query,id)
        query.session.close_all()
        return result
    
    def _post(self, type):
        def func(input,request:Request):
            query=self.__get_autoquery_from_request(request)
            output=query.insert(input)
            query.session.close_all()
            return jsonable_encoder(output)
        func.__annotations__['input']= type
        return func

    def _patch(self,type):
        def func(id,input,request:Request):
            query = self.__get_autoquery_from_request(request)
            output=query.patch(input,id)
            query.session.close_all()
            return jsonable_encoder(output)
        func.__annotations__['input'] = type
        return func

    def _put(self,type):
        def func(id,input,request:Request):
            query = self.__get_autoquery_from_request(request)
            output=query.put(input,id)
            query.session.close_all()
            return jsonable_encoder(output)
        func.__annotations__['input'] = type
        return func

    def _delete(self,id,request:Request):
        query = self.__get_autoquery_from_request(request)
        query.remove(id)
        query.session.close_all()

        
    @property
    def routes(self):
        '''
        Overrides the routes property of the `APIRouter`. This will register the routes when the Router is constructed.
        '''
        routes = []
        for name, cls in self.__sqlalchemy_classes():

            pydantic_model= sqlalchemy_to_pydantic(cls,exclude_primary_key=True)

            routes.extend([
                APIRoute(f"/{name}", self._get,methods=['GET'], description=f'Get all {name}',tags=[name]),
                APIRoute(f"/{name}", self._post(pydantic_model),methods=['POST'], description=f'POST {name}',tags=[name]),

                APIRoute(f"/{name}"+"/{id}", self._get,methods=['GET'], description=f'Get {name} by id',tags=[name]),
                APIRoute(f"/{name}"+"/{id}", self._put(pydantic_model),methods=['PUT'], description=f'Put {name} by id',tags=[name]),
                APIRoute(f"/{name}"+"/{id}", self._patch(pydantic_model),methods=['PATCH'], description=f'Patch {name} by id',tags=[name]),
                APIRoute(f"/{name}"+"/{id}", self._delete,methods=['DELETE'], description=f'Delete {name} by id',tags=[name])
            ])
        return routes

    def __sqlalchemy_classes(self, class_name:str=None):
        '''
        Returns a list of all reflected SQLAlchemy classes (when class_name is none)
        '''
        if class_name:
            return [(class_name, cls) for name, cls in list(self.Base.registry._class_registry.items()) if name==class_name][0]
        else:
            return [(name,cls) for name,cls in list(self.Base.registry._class_registry.items()) if name!="_sa_module_registry"]

    def __get_autoquery_from_request(self,request:Request) -> AutoQuery:
        table_name = request.url.path.split('/')[1]
        return Session(self.engine, query_cls=AutoQuery).query(self.__sqlalchemy_classes(table_name)[1])

    @property
    def on_startup(self):
        return []

    @property
    def on_shutdown(self):
        return []

                

    