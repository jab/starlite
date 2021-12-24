import os
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    Iterator,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from openapi_schema_pydantic import Header
from pydantic import BaseModel, FilePath, create_model, validator
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import Response as StarletteResponse
from typing_extensions import AsyncIterator, Type

from starlite.exceptions import HTTPException
from starlite.response import Response

try:
    # python 3.9 changed these variable
    from typing import _UnionGenericAlias as GenericAlias  # type: ignore
except ImportError:  # pragma: no cover
    from typing import _GenericAlias as GenericAlias  # type: ignore


EXCEPTION_HANDLER = Callable[
    [Request, Union[HTTPException, StarletteHTTPException]], Union[Response, StarletteResponse]
]
ENDPOINT_HANDLER = Callable[[Request], Awaitable[Union[Response, StarletteResponse]]]

T = TypeVar("T", bound=Type[BaseModel])


class Partial(Generic[T]):
    _models: Dict[T, Any] = {}

    def __class_getitem__(cls, item: T) -> T:
        """
        Modifies a given T subclass of BaseModel to be all optional
        """
        if not cls._models.get(item):
            field_definitions: Dict[str, Tuple[Any, None]] = {}
            for field_name, field_type in item.__annotations__.items():
                # we modify the field annotations to make it optional
                if not isinstance(field_type, GenericAlias) or type(None) not in field_type.__args__:
                    field_definitions[field_name] = (Optional[field_type], None)
                else:
                    field_definitions[field_name] = (field_type, None)
                cls._models[item] = create_model("Partial" + item.__name__, **field_definitions)  # type: ignore
        return cast(T, cls._models.get(item))


class FileData(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    path: FilePath
    filename: str
    stat_result: Optional[os.stat_result] = None

    @validator("stat_result", always=True)
    def validate_status_code(  # pylint: disable=no-self-argument,no-self-use
        cls, value: Optional[os.stat_result], values: Dict[str, Any]
    ) -> os.stat_result:
        """Set the stat_result value for the given filepath"""
        return value or os.stat(cast(str, values.get("path")))


class Redirect(BaseModel):
    path: str


class Stream(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    iterator: Union[Iterator[Any], AsyncIterator[Any]]


class ResponseHeader(Header):  # type: ignore
    value: Any = ...
