import asyncio
import logging
from copy import copy
from typing import TYPE_CHECKING, Any, cast

import socketio  # type: ignore

import pydase.components
import pydase.data_service
from pydase.utils.serialization.deserializer import loads
from pydase.utils.serialization.serializer import dump
from pydase.utils.serialization.types import SerializedObject

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class ProxyAttributeError(Exception): ...


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

        async def set_result() -> Any:
            return await self._sio.call(
                "update_value",
                {
                    "access_path": full_access_path,
                    "value": dump(value),
                },
            )

        result: SerializedObject | None = asyncio.run_coroutine_threadsafe(
            set_result(),
            loop=self._loop,
        ).result()
        if result is not None:
            ProxyLoader.loads_proxy(
                serialized_object=result, sio_client=self._sio, loop=self._loop
            )


class ProxyClassMixin:
    def __init__(
        self,
        sio_client: socketio.AsyncClient,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self._proxy_getters: dict[str, Callable[..., Any]] = {}
        self._proxy_setters: dict[str, Callable[..., Any]] = {}
        self._proxy_methods: dict[str, Callable[..., Any]] = {}
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
        def add_prefix_to_last_path_element(s: str, prefix: str) -> str:
            parts = s.split(".")
            parts[-1] = f"{prefix}_{parts[-1]}"
            return ".".join(parts)

        if serialized_object["type"] == "method":
            if serialized_object["async"] is True:
                start_method = copy(serialized_object)
                start_method["full_access_path"] = add_prefix_to_last_path_element(
                    start_method["full_access_path"], "start"
                )
                stop_method = copy(serialized_object)
                stop_method["full_access_path"] = add_prefix_to_last_path_element(
                    stop_method["full_access_path"], "stop"
                )
                self._add_method_proxy(f"start_{attr_name}", start_method)
                self._add_method_proxy(f"stop_{attr_name}", stop_method)
            else:
                self._add_method_proxy(attr_name, serialized_object)

    def _add_method_proxy(
        self, attr_name: str, serialized_object: SerializedObject
    ) -> None:
        def method_proxy(*args: Any, **kwargs: Any) -> Any:
            async def trigger_method() -> Any:
                return await self._sio.call(
                    "trigger_method",
                    {
                        "access_path": serialized_object["full_access_path"],
                        "args": dump(list(args)),
                        "kwargs": dump(kwargs),
                    },
                )

            result = asyncio.run_coroutine_threadsafe(
                trigger_method(),
                loop=self._loop,
            ).result()
            return loads(result)

        self._proxy_methods[attr_name] = method_proxy

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
                async def set_result() -> Any:
                    return await self._sio.call(
                        "update_value",
                        {
                            "access_path": serialized_object["full_access_path"],
                            "value": dump(value),
                        },
                    )

                result: SerializedObject | None = asyncio.run_coroutine_threadsafe(
                    set_result(),
                    loop=self._loop,
                ).result()
                if result is not None:
                    ProxyLoader.loads_proxy(result, self._sio, self._loop)

            self._proxy_setters[attr_name] = setter_proxy

    def _add_getattr_proxy(
        self, attr_name: str, serialized_object: SerializedObject
    ) -> None:
        def getter_proxy() -> Any:
            async def get_result() -> Any:
                return await self._sio.call(
                    "get_value", serialized_object["full_access_path"]
                )

            result = asyncio.run_coroutine_threadsafe(
                get_result(),
                loop=self._loop,
            ).result()
            return ProxyLoader.loads_proxy(result, self._sio, self._loop)

        self._proxy_getters[attr_name] = getter_proxy


class ProxyClass(pydase.data_service.DataService, ProxyClassMixin):
    def __init__(
        self,
        sio_client: socketio.AsyncClient,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        # declare before ProxyClassMixin init to avoid warning messaged
        self._observers = {}

        ProxyClassMixin.__init__(self, sio_client=sio_client, loop=loop)
        pydase.DataService.__init__(self)


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
                for item in cast(list[SerializedObject], serialized_object["value"])
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
        return loads(serialized_object)

    @staticmethod
    def update_data_service_proxy(
        proxy_class: ProxyClassMixin,
        serialized_object: SerializedObject,
    ) -> Any:
        proxy_class._proxy_getters.clear()
        proxy_class._proxy_setters.clear()
        proxy_class._proxy_methods.clear()
        for key, value in cast(
            dict[str, SerializedObject], serialized_object["value"]
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
        proxy_class = ProxyClass(sio_client=sio_client, loop=loop)
        ProxyLoader.update_data_service_proxy(
            proxy_class=proxy_class, serialized_object=serialized_object
        )
        return proxy_class

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
