from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal, TypedDict

if TYPE_CHECKING:
    import pydase.units as u

logger = logging.getLogger(__name__)


class SignatureDict(TypedDict):
    parameters: dict[str, dict[str, Any]]
    return_annotation: dict[str, Any]


class SerializedObjectBase(TypedDict):
    full_access_path: str
    doc: str | None
    readonly: bool


class SerializedInteger(SerializedObjectBase):
    value: int
    type: Literal["int"]


class SerializedFloat(SerializedObjectBase):
    value: float
    type: Literal["float"]


class SerializedQuantity(SerializedObjectBase):
    value: u.QuantityDict
    type: Literal["Quantity"]


class SerializedBool(SerializedObjectBase):
    value: bool
    type: Literal["bool"]


class SerializedString(SerializedObjectBase):
    value: str
    type: Literal["str"]


class SerializedDatetime(SerializedObjectBase):
    type: Literal["datetime"]
    value: str


class SerializedEnum(SerializedObjectBase):
    name: str
    value: str
    type: Literal["Enum", "ColouredEnum"]
    enum: dict[str, Any]


class SerializedList(SerializedObjectBase):
    value: list[SerializedObject]
    type: Literal["list"]


class SerializedDict(SerializedObjectBase):
    value: dict[str, SerializedObject]
    type: Literal["dict"]


class SerializedNoneType(SerializedObjectBase):
    value: None
    type: Literal["NoneType"]


class SerializedNoValue(SerializedObjectBase):
    value: None
    type: Literal["None"]


SerializedMethod = TypedDict(
    "SerializedMethod",
    {
        "full_access_path": str,
        "value": Literal["RUNNING"] | None,
        "type": Literal["method"],
        "doc": str | None,
        "readonly": bool,
        "async": bool,
        "signature": SignatureDict,
        "frontend_render": bool,
    },
)


class SerializedException(SerializedObjectBase):
    name: str
    value: str
    type: Literal["Exception"]


DataServiceTypes = Literal[
    "DataService", "Image", "NumberSlider", "DeviceConnection", "Task"
]


class SerializedDataService(SerializedObjectBase):
    name: str
    value: dict[str, SerializedObject]
    type: DataServiceTypes


SerializedObject = (
    SerializedBool
    | SerializedFloat
    | SerializedInteger
    | SerializedString
    | SerializedDatetime
    | SerializedList
    | SerializedDict
    | SerializedNoneType
    | SerializedMethod
    | SerializedException
    | SerializedDataService
    | SerializedEnum
    | SerializedQuantity
    | SerializedNoValue
)
"""
This type can be any of the following:

- SerializedBool
- SerializedFloat
- SerializedInteger
- SerializedString
- SerializedDatetime
- SerializedList
- SerializedDict
- SerializedNoneType
- SerializedMethod
- SerializedException
- SerializedDataService
- SerializedEnum
- SerializedQuantity
- SerializedNoValue
"""
