from fastapi.applications import FastAPI
from bootstrapi.router import BootstrAPIRouter
import pytest 
import json
from sqlalchemy.ext.automap import automap_base

from tests.test_db import database

@pytest.fixture
def app(engine,database):
    app = FastAPI(title='BootstrAPI')
    Base = automap_base()
    Base.prepare(engine)
    router = BootstrAPIRouter(engine,Base)
    app.include_router(router)
    return app

@pytest.fixture
def engine():
    from sqlalchemy import create_engine
    return create_engine('sqlite:///tests/data.db')

def test_get(app):
    from fastapi.testclient import TestClient
    json.loads(TestClient(app).get('/projects').content) == [
        {'begin_date': '01-01-2020', 'id': 1, 'end_date': '01-01-2030', 'name': 'datahub'}, 
        {'begin_date': '01-01-1990', 'id': 2, 'end_date': '01-01-2008', 'name': 'salesforce'}, 
        {'begin_date': '01-01-2021', 'id': 3, 'end_date': '01-01-2030', 'name': 'mijnapp'}
        ]

def test_get_all_select(app):
    from fastapi.testclient import TestClient
    json.loads(TestClient(app).get('/projects?$select=name,begin_date').content) == [
        {'name': 'datahub', 'begin_date': '01-01-2020'}, 
        {'name': 'salesforce', 'begin_date': '01-01-1990'}, 
        {'name': 'mijnapp', 'begin_date': '01-01-2021'}]

def test_get_all_filter(app):
    from fastapi.testclient import TestClient
    json.loads(TestClient(app).get('/projects?$filter=name eq datahub or name eq salesforce').content) == [
        {'id': 1, 'begin_date': '01-01-2020', 'end_date': '01-01-2030', 'name': 'datahub'}, 
        {'id': 2, 'begin_date': '01-01-1990', 'end_date': '01-01-2008', 'name': 'salesforce'}]


def test_filter_with_spaces(app):
    from fastapi.testclient import TestClient
    assert json.loads(TestClient(app).get('/tasks?$filter=name eq "create datamodel"').content) == [{'name': 'create datamodel', 'status_id': 2, 'begin_date': '01-01-2020', 'id': 2, 'priority': 2, 'project_id': 1, 'end_date': '01-01-2030'}]
    

def test_get_expand_from_projects(app):
    from fastapi.testclient import TestClient
    json.loads(TestClient(app).get('/projects?$expand=tasks').content)
    assert json.loads(TestClient(app).get('/projects?$expand=tasks').content)[0]['tasks_collection']!=[]

def test_get_expand_from_tasks(app):
    from fastapi.testclient import TestClient
    json.loads(TestClient(app).get('/tasks?$expand=projects').content)

def test_get_expand_select(app):
    from fastapi.testclient import TestClient
    json.loads(TestClient(app).get('/projects?$expand=tasks&$select=name').content)
   

def test_get_id(app):
    from fastapi.testclient import TestClient
    json.loads(TestClient(app).get('/projects/1').content)

def test_get_id_select(app):
    from fastapi.testclient import TestClient
    json.loads(TestClient(app).get('/projects/1?$select=name,begin_date').content)

def test_post(app):
    from fastapi.testclient import TestClient
    json.loads(TestClient(app).post('/projects',json = {
        "name": "new_project",
        "begin_date": "2020-01-01",
        "end_date": "2030-02-03"
        }).content) == {'end_date': '2030-02-03', 'name': 'new_project', 'begin_date': '2020-01-01', 'id': 4}

def test_patch(app):
    from fastapi.testclient import TestClient
    json.loads(TestClient(app).patch('/projects/1',json = {
        "name": "renamed",
        }).content) =={'end_date': '01-01-2030', 'name': 'renamed', 'begin_date': '01-01-2020', 'id': 1}

def test_put(app):
    from fastapi.testclient import TestClient
    assert json.loads(TestClient(app).put('/projects/2',json = {
        'end_date': '09-09-2030', 'name': 'second', 'begin_date': '09-09-2020'}
        ).content) == json.loads(TestClient(app).get('/projects/2').content)[0]

def test_put_nonexisting(app):
    from fastapi.testclient import TestClient
    assert json.loads(TestClient(app).put('/projects/4',json = {
        'end_date': '09-09-2030', 'name': 'four', 'begin_date': '09-09-2020'}
        ).content) == json.loads(TestClient(app).get('/projects/4').content)[0]

def test_delete(app):
    from fastapi.testclient import TestClient
    TestClient(app).delete('/projects/2') 
    assert [x['id'] for x in json.loads(TestClient(app).get('/projects').content) if x['id']==2]==[]

def test_delete_nonexisting(app):
    from fastapi.testclient import TestClient
    assert TestClient(app).delete('/projects/25').status_code == 404

