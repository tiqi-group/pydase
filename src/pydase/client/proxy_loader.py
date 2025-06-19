import asyncio
import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, cast

import socketio  # type: ignore
from typing_extensions import SupportsIndex

from pydase.utils.serialization.deserializer import Deserializer, loads
from pydase.utils.serialization.serializer import dump
from pydase.utils.serialization.types import SerializedObject

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class ProxyAttributeError(Exception): ...


def trigger_method(
    sio_client: socketio.AsyncClient,
    loop: asyncio.AbstractEventLoop,
    access_path: str,
    args: list[Any],
    kwargs: dict[str, Any],
) -> Any:
    async def async_trigger_method() -> Any:
        return await sio_client.call(
            "trigger_method",
            {
                "access_path": access_path,
                "args": dump(args),
                "kwargs": dump(kwargs),
            },
        )

    result: SerializedObject | None = asyncio.run_coroutine_threadsafe(
        async_trigger_method(),
        loop=loop,
    ).result()

    if result is not None:
        return ProxyLoader.loads_proxy(
            serialized_object=result, sio_client=sio_client, loop=loop
        )

    return None


def update_value(
    sio_client: socketio.AsyncClient,
    loop: asyncio.AbstractEventLoop,
    access_path: str,
    value: Any,
) -> Any:
    async def set_result() -> Any:
        return await sio_client.call(
            "update_value",
            {
                "access_path": access_path,
                "value": dump(value),
            },
        )

    result: SerializedObject | None = asyncio.run_coroutine_threadsafe(
        set_result(),
        loop=loop,
    ).result()
    if result is not None:
        ProxyLoader.loads_proxy(
            serialized_object=result, sio_client=sio_client, loop=loop
        )


def get_value(
    sio_client: socketio.AsyncClient,
    loop: asyncio.AbstractEventLoop,
    access_path: str,
) -> Any:
    async def get_result() -> Any:
        return await sio_client.call("get_value", access_path)

    result = asyncio.run_coroutine_threadsafe(
        get_result(),
        loop=loop,
    ).result()
    return ProxyLoader.loads_proxy(result, sio_client, loop)


class ProxyDict(dict[str, Any]):
    def __init__(
        self,
        original_dict: dict[str, Any],
        parent_path: str,
        sio_client: socketio.AsyncClient,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        super().__init__(original_dict)
        self._parent_path = parent_path
        self._loop = loop
        self._sio = sio_client

    def __setitem__(self, key: str, value: Any) -> None:
        observer_key = key
        if isinstance(key, str):
            observer_key = f'"{key}"'

        full_access_path = f"{self._parent_path}[{observer_key}]"

        update_value(self._sio, self._loop, full_access_path, value)

    def pop(self, key: str) -> Any:  # type: ignore
        """Removes the element from the dictionary on the server. It does not return
        any proxy as the corresponding object on the server does not live anymore."""

        full_access_path = f"{self._parent_path}.pop"

        trigger_method(self._sio, self._loop, full_access_path, [key], {})


class ProxyList(list[Any]):
    def __init__(
        self,
        original_list: list[Any],
        parent_path: str,
        sio_client: socketio.AsyncClient,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        super().__init__(original_list)
        self._parent_path = parent_path
        self._loop = loop
        self._sio = sio_client

    def __setitem__(self, key: int, value: Any) -> None:  # type: ignore[override]
        full_access_path = f"{self._parent_path}[{key}]"

        update_value(self._sio, self._loop, full_access_path, value)

    def append(self, object_: Any, /) -> None:
        full_access_path = f"{self._parent_path}.append"

        trigger_method(self._sio, self._loop, full_access_path, [object_], {})

    def clear(self) -> None:
        full_access_path = f"{self._parent_path}.clear"

        trigger_method(self._sio, self._loop, full_access_path, [], {})

    def extend(self, iterable: Iterable[Any], /) -> None:
        full_access_path = f"{self._parent_path}.extend"

        trigger_method(self._sio, self._loop, full_access_path, [iterable], {})

    def insert(self, index: SupportsIndex, object_: Any, /) -> None:
        full_access_path = f"{self._parent_path}.insert"

        trigger_method(self._sio, self._loop, full_access_path, [index, object_], {})

    def pop(self, index: SupportsIndex = -1, /) -> Any:
        full_access_path = f"{self._parent_path}.pop"

        return trigger_method(self._sio, self._loop, full_access_path, [index], {})

    def remove(self, value: Any, /) -> None:
        full_access_path = f"{self._parent_path}.remove"

        trigger_method(self._sio, self._loop, full_access_path, [value], {})


class ProxyClassMixin:
    def __init__(self) -> None:
        # declare before DataService init to avoid warning messaged
        self._observers: dict[str, Any] = {}

        self._proxy_getters: dict[str, Callable[..., Any]] = {}
        self._proxy_setters: dict[str, Callable[..., Any]] = {}
        self._proxy_methods: dict[str, Callable[..., Any]] = {}

    def _initialise(
        self,
        sio_client: socketio.AsyncClient,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self._loop = loop
        self._sio = sio_client

    def __dir__(self) -> list[str]:
        """Used to provide tab completion on CLI / notebook"""
        static_dir = super().__dir__()
        return sorted({*static_dir, *self._proxy_getters, *self._proxy_methods.keys()})

    def __getattribute__(self, name: str) -> Any:
        try:
            if name in super().__getattribute__("_proxy_getters"):
                return super().__getattribute__("_proxy_getters")[name]()
            if name in super().__getattribute__("_proxy_methods"):
                return super().__getattribute__("_proxy_methods")[name]
        except AttributeError:
            pass
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        try:
            if name in super().__getattribute__("_proxy_setters"):
                return super().__getattribute__("_proxy_setters")[name](value)
            if name in super().__getattribute__("_proxy_getters"):
                raise ProxyAttributeError(
                    f"Proxy attribute {name!r} of {type(self).__name__!r} is readonly!"
                )
        except AttributeError:
            pass
        return super().__setattr__(name, value)

    def _handle_serialized_method(
        self, attr_name: str, serialized_object: SerializedObject
    ) -> None:
        if serialized_object["type"] == "method":
            self._add_method_proxy(attr_name, serialized_object)

    def _add_method_proxy(
        self, attr_name: str, serialized_object: SerializedObject
    ) -> None:
        def method_proxy(*args: Any, **kwargs: Any) -> Any:
            return trigger_method(
                self._sio,
                self._loop,
                serialized_object["full_access_path"],
                list(args),
                kwargs,
            )

        dict.__setitem__(self._proxy_methods, attr_name, method_proxy)

    def _add_attr_proxy(
        self, attr_name: str, serialized_object: SerializedObject
    ) -> None:
        self._add_getattr_proxy(attr_name, serialized_object=serialized_object)
        if not serialized_object["readonly"]:
            self._add_setattr_proxy(attr_name, serialized_object=serialized_object)

    def _add_setattr_proxy(
        self, attr_name: str, serialized_object: SerializedObject
    ) -> None:
        self._add_getattr_proxy(attr_name, serialized_object=serialized_object)
        if not serialized_object["readonly"]:

            def setter_proxy(value: Any) -> None:
                update_value(
                    self._sio, self._loop, serialized_object["full_access_path"], value
                )

            dict.__setitem__(self._proxy_setters, attr_name, setter_proxy)  # type: ignore

    def _add_getattr_proxy(
        self, attr_name: str, serialized_object: SerializedObject
    ) -> None:
        def getter_proxy() -> Any:
            return get_value(
                sio_client=self._sio,
                loop=self._loop,
                access_path=serialized_object["full_access_path"],
            )

        dict.__setitem__(self._proxy_getters, attr_name, getter_proxy)  # type: ignore


class ProxyLoader:
    @staticmethod
    def load_list_proxy(
        serialized_object: SerializedObject,
        sio_client: socketio.AsyncClient,
        loop: asyncio.AbstractEventLoop,
    ) -> Any:
        return ProxyList(
            [
                ProxyLoader.loads_proxy(item, sio_client, loop)
                for item in cast("list[SerializedObject]", serialized_object["value"])
            ],
            parent_path=serialized_object["full_access_path"],
            sio_client=sio_client,
            loop=loop,
        )

    @staticmethod
    def load_dict_proxy(
        serialized_object: SerializedObject,
        sio_client: socketio.AsyncClient,
        loop: asyncio.AbstractEventLoop,
    ) -> Any:
        return ProxyDict(
            {
                key: ProxyLoader.loads_proxy(value, sio_client, loop)
                for key, value in cast(
                    "dict[str, SerializedObject]", serialized_object["value"]
                ).items()
            },
            parent_path=serialized_object["full_access_path"],
            sio_client=sio_client,
            loop=loop,
        )

    @staticmethod
    def update_data_service_proxy(
        proxy_class: ProxyClassMixin,
        serialized_object: SerializedObject,
    ) -> Any:
        proxy_class._proxy_getters.clear()
        proxy_class._proxy_setters.clear()
        proxy_class._proxy_methods.clear()
        for key, value in cast(
            "dict[str, SerializedObject]", serialized_object["value"]
        ).items():
            type_handler: dict[str | None, None | Callable[..., Any]] = {
                None: None,
                "int": proxy_class._add_attr_proxy,
                "float": proxy_class._add_attr_proxy,
                "bool": proxy_class._add_attr_proxy,
                "str": proxy_class._add_attr_proxy,
                "NoneType": proxy_class._add_attr_proxy,
                "Quantity": proxy_class._add_attr_proxy,
                "Enum": proxy_class._add_attr_proxy,
                "ColouredEnum": proxy_class._add_attr_proxy,
                "method": proxy_class._handle_serialized_method,
                "list": proxy_class._add_getattr_proxy,
                "dict": proxy_class._add_getattr_proxy,
            }

            # First go through handled types (as ColouredEnum is also within the
            # components)
            handler = type_handler.get(value["type"])
            if handler:
                handler(key, value)
            else:
                proxy_class._add_getattr_proxy(key, value)

    @staticmethod
    def load_data_service_proxy(
        serialized_object: SerializedObject,
        sio_client: socketio.AsyncClient,
        loop: asyncio.AbstractEventLoop,
    ) -> Any:
        # Custom types like Components or DataService classes
        component_class = cast(
            "type", Deserializer.get_service_base_class(serialized_object["type"])
        )
        class_bases = (
            ProxyClassMixin,
            component_class,
        )
        proxy_base_class: type[ProxyClassMixin] = type(
            serialized_object["name"],  # type: ignore
            class_bases,
            {},
        )
        proxy_class_instance = proxy_base_class()
        proxy_class_instance._initialise(sio_client=sio_client, loop=loop)
        ProxyLoader.update_data_service_proxy(
            proxy_class=proxy_class_instance, serialized_object=serialized_object
        )
        return proxy_class_instance

    @staticmethod
    def load_default(
        serialized_object: SerializedObject,
        sio_client: socketio.AsyncClient,
        loop: asyncio.AbstractEventLoop,
    ) -> Any:
        return loads(serialized_object)

    @staticmethod
    def loads_proxy(
        serialized_object: SerializedObject,
        sio_client: socketio.AsyncClient,
        loop: asyncio.AbstractEventLoop,
    ) -> Any:
        type_handler: dict[str | None, None | Callable[..., Any]] = {
            "int": ProxyLoader.load_default,
            "float": ProxyLoader.load_default,
            "bool": ProxyLoader.load_default,
            "str": ProxyLoader.load_default,
            "NoneType": ProxyLoader.load_default,
            "Quantity": ProxyLoader.load_default,
            "Enum": ProxyLoader.load_default,
            "ColouredEnum": ProxyLoader.load_default,
            "Exception": ProxyLoader.load_default,
            "list": ProxyLoader.load_list_proxy,
            "dict": ProxyLoader.load_dict_proxy,
        }

        # First go through handled types (as ColouredEnum is also within the components)
        handler = type_handler.get(serialized_object["type"])
        if handler:
            return handler(
                serialized_object=serialized_object, sio_client=sio_client, loop=loop
            )

        return ProxyLoader.load_data_service_proxy(
            serialized_object=serialized_object, sio_client=sio_client, loop=loop
        )
