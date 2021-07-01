import sqlite3
import pytest
import os

@pytest.fixture(autouse=True)
def database():
    try:
        os.remove('./tests/data.db')
    except:
        pass
    database = "./tests/data.db"
    sql_create_projects_table = """ CREATE TABLE IF NOT EXISTS projects (
                                        id integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                                        name text NOT NULL,
                                        begin_date text,
                                        end_date text
                                    ); """

    sql_create_tasks_table = """CREATE TABLE IF NOT EXISTS tasks (
                                    id integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                                    name text NOT NULL,
                                    priority integer,
                                    status_id integer NOT NULL,
                                    project_id integer NOT NULL,
                                    begin_date text NOT NULL,
                                    end_date text NOT NULL,
                                    FOREIGN KEY (project_id) REFERENCES projects (id)
                                );"""
    
    projects_data = """INSERT INTO projects (name,begin_date, end_date)
                            VALUES 
                        ("datahub","01-01-2020","01-01-2030"),
                        ("salesforce","01-01-1990","01-01-2008"),
                        ("mijnapp","01-01-2021","01-01-2030");
                    """

    tasks_data = """INSERT INTO tasks (name, priority, status_id, project_id, begin_date, end_date)
                            VALUES 
                        ("create api",1,1,1,"01-01-2020","01-01-2030"),
                        ("create datamodel",2,2,1,"01-01-2020","01-01-2030");
                    """
        

    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(sql_create_projects_table)
    c.execute(sql_create_tasks_table)
    c.execute(projects_data)
    c.execute(tasks_data)
    c.close()
    conn.commit()
    conn.close()
    yield
    try:
        os.remove('./tests/data.db')
    except:
        pass
