from typing import Container, Optional, Type

from pydantic import BaseConfig, BaseModel, create_model
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty


class OrmConfig(BaseConfig):
    orm_mode = True


def sqlalchemy_to_pydantic(db_model: Type, *, config: Type = OrmConfig, exclude: Container[str] = [], exclude_primary_key:bool=False) -> Type[BaseModel]:
    """Convert an SQLAlchemy class to a Pydantic class.

    This is used within the router to determine the schema of the objects.
    It is based on the code by Tiangolo (https://github.com/tiangolo/pydantic-sqlalchemy)
    """

    mapper = inspect(db_model)
    fields = {}
    resulting_name = db_model.__table__.name 
    for attr in mapper.attrs:
        if isinstance(attr, ColumnProperty):
            if attr.columns:
                name = attr.key
                if name in exclude:
                    continue
                column = attr.columns[0]
                if exclude_primary_key and column.primary_key:
                    continue
                python_type: Optional[type] = None
                if hasattr(column.type, "impl"):
                    if hasattr(column.type.impl, "python_type"):
                        python_type = column.type.impl.python_type
                elif hasattr(column.type, "python_type"):
                    python_type = column.type.python_type
                assert python_type, f"Could not infer python_type for {column}"
                default = None
                if column.default is None and not column.nullable:
                    default = ...
                fields[name] = (python_type, default)
    pydantic_model = create_model(
        str(resulting_name), __config__=config, **fields  # type: ignore
    )
    return pydantic_model