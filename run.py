import argparse
import os

import uvicorn
import argparse

from fastapi.applications import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base

from bootstrapi.router import BootstrAPIRouter


class EnvDefault(argparse.Action):
    '''
    This is an helper class for the ArgumentParser.
    It checks whether an environment variable exists and uses this as default argument if it does.
    '''
    def __init__(self, envvar, required=True, default=None, **kwargs):
        if envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required, 
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)

if __name__ == '__main__':
    '''
    Creates an FastAPI instance and starts the Uvicorn server
    '''

    parser = argparse.ArgumentParser(description='Bootstrap an API')
    parser.add_argument("connection", help="SQLAlchemy connection string to a database",action=EnvDefault, envvar='connection',type=str)
    parser.add_argument("--title", help="The title of the API", default="BootstrAPI Instance",action=EnvDefault, envvar='title',type=str)
    parser.add_argument("--host", help="The hostname",default="0.0.0.0",action=EnvDefault, envvar='host',type=str)
    parser.add_argument("--port", help="The port",default="8000",action=EnvDefault, envvar='port',type=int)
    parser.add_argument("--schema", help="The schema of the database",default="#empty#",action=EnvDefault, envvar='schema',type=str)

    args = parser.parse_args()

    engine = create_engine(args.connection)
    app = FastAPI(title=args.title)

    Base = automap_base()

    if args.schema=="#empty#":
        schema = None
    else:
        schema = args.schema

    print(f"""
Starting app with:
Title: {args.title}
Host: {args.host}
Port: {args.port}
Schema: {schema}
    """)

    Base.prepare(engine,schema = schema)

    router = BootstrAPIRouter(engine,Base)
    app.include_router(router)

    uvicorn.run(app, host=args.host, port=args.port)