import pytest 
from tests.test_db import database
from bootstrapi.sqlalchemy import AutoQuery

@pytest.fixture
def alchemy_query(database):
    from sqlalchemy import create_engine
    from sqlalchemy.ext.automap import automap_base
    from sqlalchemy.orm import Session

    Base = automap_base()
    engine = create_engine('sqlite:///tests/data.db')
    Base.prepare(engine)
    return Session(engine, query_cls=AutoQuery).query(Base.classes.projects)

@pytest.fixture
def parsed_query():
    from bootstrapi.parser import ODataQuery
    return ODataQuery(("$select=name,begin_date&$expand=tasks($select=name,priority)&$filter=name eq datahub or name eq salesforce&$orderby=name asc"))

def test_get_root_table(alchemy_query:AutoQuery):
    assert alchemy_query.get_root_table()=='projects'

def test_get_all_tables(alchemy_query:AutoQuery):
    tables = alchemy_query.get_all_tables()
    assert not set(tables) ^ {'projects'}

def test_get_table_by_name(alchemy_query:AutoQuery):
    alchemy_query.get_table_by_name('projects')

def test_get_column_by_name(alchemy_query:AutoQuery):
    alchemy_query.get_column_by_name('name',alchemy_query.get_root_table())
    
def test_odata_filter(parsed_query,alchemy_query:AutoQuery):
    assert alchemy_query.odata_filter(parsed_query)