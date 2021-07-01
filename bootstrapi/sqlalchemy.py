from sqlalchemy.orm.query import Query
import bootstrapi.parser as parser

from typing import List
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

from pydantic import BaseModel

from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.inspection import inspect

class AutoQuery(Query):
    """
    Extends the SQLAlchemy.Query object OData parsing functionality using the parser.ODataQuery parser.
    """
    expandable_columns = []
    filter_result = None

    def apply_odataquery(self,query_str:str,id=None):
        """
        Translates a query string (e.g. $select=first,second&$filter=one eq 'this' and two eq 'that') to a SQLAlchemy.Query
        """
        query=parser.ODataQuery(query_str)
        if '$filter' in query.keys():
            self = self.odata_filter(query)
        if '$expand' in query.keys():
            self = self.odata_expand(query)

        if id:
            primary_key_column = self.get_column_by_name(self.get_primary_key(),self.get_root_table())
            self=self.filter(primary_key_column == id)

        if '$select' in query.keys():
            return self.odata_select(query)
        else:
            return jsonable_encoder(self.all())

    def odata_select(self,query:parser.ODataQuery, force_id_in_select=False):
        """
        Converts the '$select' key in the dictionary of a parser.ODataQuery to a SQLAlchemy.Query
        """
        columns = query['$select'] 
        if force_id_in_select:
            columns.append(self.get_primary_key())
        #Force expandable columns in select 
        if '$expand' in query.keys():
            obj = query['$expand']['object']
            columns.append(f'{obj}_collection')
            columns.append(f'{obj}')
        
        result = jsonable_encoder(self.all())
        
        if type(result)==list:
            out = []
            for row in result:
                out.append({k:v for (k,v) in row.items() if k in columns})
            return out
        if type(result)==dict:
            return {k:v for (k,v) in result.items() if k in columns}

    def odata_filter(self,query:parser.ODataQuery):
        """
        Converts the '$filter' key in the dictionary of a parser.ODataQuery to a SQLAlchemy.Query
        """
        expr = query['$filter']
        func=self.parse_filter(expr,on_table=self.get_root_table())
        return self.filter(func)

    def odata_expand(self,query:parser.ODataQuery):
        expr = query['$expand']
        obj = expr['object']
        try:
            join_column = getattr(self.get_table_by_name(self.get_root_table()),f'{obj}_collection')
        except:
            join_column = getattr(self.get_table_by_name(self.get_root_table()),f'{obj}')
        return self.join(join_column,isouter=True).options(joinedload(join_column))
        

    def parse_filter(self,expr,on_table:str):
        if 'or' in expr.keys():
            functions_to_or = []
            for elem in expr['or']:
                functions_to_or.append(self.parse_filter(elem,on_table))
            return (lambda: or_(*functions_to_or))()

        if 'and' in expr.keys():
            functions_to_and = []
            for elem in expr['and']:
                functions_to_and.append(self.parse_filter(elem,on_table))
            return (lambda: and_(*functions_to_and))()

        if 'left' in expr.keys():
            return self.parse_filter_expression(expr,on_table)
    
    def insert(self,object:BaseModel):
        # Instantiate SQLAlchemy object
        sqlalchemy_class=self.get_table_by_name(self.get_root_table())
        sqlalchemy_obj = sqlalchemy_class(**dict(object))
        # Add the object to the session
        self.session.add(sqlalchemy_obj)
        self.session.commit()
        self.session.refresh(sqlalchemy_obj)
        return sqlalchemy_obj

    def patch(self,object:BaseModel,id):
        id_column = self.get_column_by_name(self.get_primary_key(),self.get_root_table())
        obj=self.filter(id_column == id)
        obj.update({k:v for k,v in dict(object).items() if v is not None},synchronize_session=False)
        self.session.commit()
        return obj.first()


    def put(self,object:BaseModel,id):
        # add id to id column object    
        values_dict = {**dict(object),**{self.get_primary_key():id}}
        sqlalchemy_class=self.get_table_by_name(self.get_root_table())
        obj = sqlalchemy_class(**values_dict)
        self.session.merge(sqlalchemy_class(**values_dict))
        self.session.commit()
        return self.get(id)

    def remove(self,id):
        id_column = self.get_column_by_name(self.get_primary_key(),self.get_root_table())
        obj = self.filter(id_column == id).all()
        if not obj:
            raise HTTPException(404,"Not Found")
        else:
            self.filter(id_column == id).delete()
            self.session.commit()


    def parse_filter_expression(self,expr,on_table:str):
        if expr['operator']=='eq':
            return (lambda: self.get_column_by_name(expr['left'],on_table) == expr['right'])()

    def get_root_table(self)->str:
        return self.column_descriptions[0]['name']

    def get_all_tables(self) -> List[str]:
        return [t.name for t in self._raw_columns]
 
    def get_table_by_name(self, name:str):
        return [t['type'] for t in self.column_descriptions if t['name']==name][0]

    def get_column_by_name(self, name:str, table:str):
        for elem in self._raw_columns: # _raw_columns can both return Tables AND Columns, so lets check
            if elem.__visit_name__=='table':
                if elem.name==table:
                    return [c for c in elem.columns if c.name==name][0]
            else:
                if elem.name==name:
                    return elem
    
    def get_root_relationships(self):
        return inspect(self.get_table_by_name(self.get_root_table())).relationships

    def get_primary_key(self) -> str:
        return inspect(self.get_table_by_name(self.get_root_table())).primary_key[0].name

    def json(self):
        return jsonable_encoder(self.all())
