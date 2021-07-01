BootstrAPI
==========

Automatically generate an OpenAPI for your existing database.

Features
--------
- Generates an API for your current database
- Generates OpenAPI docs 
- Supports OData-like queries ($select, $filter, $expand)
- Support all RESTful HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Supports all Databases supported by SQLAlchemy

Requirements
------------
### Python
- Python 3.6+

### Database
- Exactly one primary key per table


Quickstart
----------

There are 3 main ways to run the code. As a standalone Python app, as a package and a Docker container.

### Python App

First clone the code into a folder, then run:

```console
$ pip install -r requirements.txt
$ python -m run connection_string [--title "API"] [--host 0.0.0.0] [--port 8000] [--schema dbo]
```

### Python Package

Install the bootstrapi package

```console
$ pip install bootstrapi
```

Then create an FastAPI app and register the routes.

```python
import uvicorn
from fastapi.applications import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from bootstrapi.router import BootstrAPIRouter

connection_string = "" #Your SQLAlchemy Connection string here

engine = create_engine(connection_string)
app = FastAPI(title='My API')

Base = automap_base()
Base.prepare(engine,schema = schema)

router = BootstrAPIRouter(engine,Base)
app.include_router(router)

uvicorn.run(app, host='127.0.0.1', port=8000)
```

### Docker

```console
$ docker run --env connection="YOUR_CONNECTION_STRING" -p 8000:8000 mrpowerus/bootstrapi
```





