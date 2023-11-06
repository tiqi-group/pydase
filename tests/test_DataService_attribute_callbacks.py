from pytest import LogCaptureFixture

from pydase import DataService


def test_class_attributes(caplog: LogCaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"

    class ServiceClass(DataService):
        attr_1 = SubClass()

    service_instance = ServiceClass()
    service_instance.attr_1.name = "Hi"

    assert "ServiceClass.attr_1.name changed to Hi" in caplog.text


def test_instance_attributes(caplog: LogCaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr_1 = SubClass()
            super().__init__()

    service_instance = ServiceClass()
    service_instance.attr_1.name = "Hi"

    assert "ServiceClass.attr_1.name changed to Hi" in caplog.text


def test_class_attribute(caplog: LogCaptureFixture) -> None:
    class ServiceClass(DataService):
        attr = 0

    service_instance = ServiceClass()

    service_instance.attr = 1
    assert "ServiceClass.attr changed to 1" in caplog.text


def test_instance_attribute(caplog: LogCaptureFixture) -> None:
    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr = "Hello World"
            super().__init__()

    service_instance = ServiceClass()

    service_instance.attr = "Hello"
    assert "ServiceClass.attr changed to Hello" in caplog.text


def test_reused_instance_attributes(caplog: LogCaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"

    subclass_instance = SubClass()

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr_1 = subclass_instance
            self.attr_2 = subclass_instance
            super().__init__()

    service_instance = ServiceClass()
    service_instance.attr_1.name = "Hi"

    assert service_instance.attr_1 == service_instance.attr_2
    assert "ServiceClass.attr_1.name changed to Hi" in caplog.text
    assert "ServiceClass.attr_2.name changed to Hi" in caplog.text


def test_reused_attributes_mixed(caplog: LogCaptureFixture) -> None:
    class SubClass(DataService):
        pass

    subclass_instance = SubClass()

    class ServiceClass(DataService):
        attr_1 = subclass_instance

        def __init__(self) -> None:
            self.attr_2 = subclass_instance
            super().__init__()

    service_instance = ServiceClass()
    service_instance.attr_1.name = "Hi"

    assert service_instance.attr_1 == service_instance.attr_2
    assert "ServiceClass.attr_1.name changed to Hi" in caplog.text
    assert "ServiceClass.attr_2.name changed to Hi" in caplog.text


def test_nested_class_attributes(caplog: LogCaptureFixture) -> None:
    class SubSubSubClass(DataService):
        name = "Hello"

    class SubSubClass(DataService):
        name = "Hello"
        attr = SubSubSubClass()

    class SubClass(DataService):
        name = "Hello"
        attr = SubSubClass()

    class ServiceClass(DataService):
        name = "Hello"
        attr = SubClass()

    service_instance = ServiceClass()
    service_instance.attr.attr.attr.name = "Hi"
    service_instance.attr.attr.name = "Hou"
    service_instance.attr.name = "foo"
    service_instance.name = "bar"

    assert "ServiceClass.attr.attr.attr.name changed to Hi" in caplog.text
    assert "ServiceClass.attr.attr.name changed to Hou" in caplog.text
    assert "ServiceClass.attr.name changed to foo" in caplog.text
    assert "ServiceClass.name changed to bar" in caplog.text


def test_nested_instance_attributes(caplog: LogCaptureFixture) -> None:
    class SubSubSubClass(DataService):
        name = "Hello"

    class SubSubClass(DataService):
        def __init__(self) -> None:
            self.attr = SubSubSubClass()
            self.name = "Hello"
            super().__init__()

    class SubClass(DataService):
        def __init__(self) -> None:
            self.attr = SubSubClass()
            self.name = "Hello"
            super().__init__()

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr = SubClass()
            self.name = "Hello"
            super().__init__()

    service_instance = ServiceClass()
    service_instance.attr.attr.attr.name = "Hi"
    service_instance.attr.attr.name = "Hou"
    service_instance.attr.name = "foo"
    service_instance.name = "bar"

    assert "ServiceClass.attr.attr.attr.name changed to Hi" in caplog.text
    assert "ServiceClass.attr.attr.name changed to Hou" in caplog.text
    assert "ServiceClass.attr.name changed to foo" in caplog.text
    assert "ServiceClass.name changed to bar" in caplog.text


def test_advanced_nested_class_attributes(caplog: LogCaptureFixture) -> None:
    class SubSubSubClass(DataService):
        name = "Hello"

    class SubSubClass(DataService):
        attr = SubSubSubClass()

    class SubClass(DataService):
        attr = SubSubClass()

    class ServiceClass(DataService):
        attr = SubClass()
        subattr = SubSubClass()

    service_instance = ServiceClass()
    service_instance.attr.attr.attr.name = "Hi"

    assert "ServiceClass.attr.attr.attr.name changed to Hi" in caplog.text
    assert "ServiceClass.subattr.attr.name changed to Hi" in caplog.text
    service_instance.subattr.attr.name = "Ho"

    assert "ServiceClass.attr.attr.attr.name changed to Ho" in caplog.text
    assert "ServiceClass.subattr.attr.name changed to Ho" in caplog.text


def test_advanced_nested_instance_attributes(caplog: LogCaptureFixture) -> None:
    class SubSubSubClass(DataService):
        name = "Hello"

    class SubSubClass(DataService):
        def __init__(self) -> None:
            self.attr = SubSubSubClass()
            super().__init__()

    subsubclass_instance = SubSubClass()

    class SubClass(DataService):
        def __init__(self) -> None:
            self.attr = subsubclass_instance
            super().__init__()

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr = SubClass()
            self.subattr = subsubclass_instance
            super().__init__()

    service_instance = ServiceClass()

    service_instance.attr.attr.attr.name = "Hi"
    assert "ServiceClass.attr.attr.attr.name changed to Hi" in caplog.text
    assert "ServiceClass.subattr.attr.name changed to Hi" in caplog.text
    caplog.clear()

    service_instance.subattr.attr.name = "Ho"
    assert "ServiceClass.attr.attr.attr.name changed to Ho" in caplog.text
    assert "ServiceClass.subattr.attr.name changed to Ho" in caplog.text
    caplog.clear()


def test_advanced_nested_attributes_mixed(caplog: LogCaptureFixture) -> None:
    class SubSubClass(DataService):
        name = "Hello"

    class SubClass(DataService):
        class_attr = SubSubClass()

        def __init__(self) -> None:
            self.attr_1 = SubSubClass()
            super().__init__()

    class ServiceClass(DataService):
        class_attr = SubClass()

        def __init__(self) -> None:
            self.attr = SubClass()
            super().__init__()

    service_instance = ServiceClass()
    # Subclass.attr is the same for all instances
    assert service_instance.attr.class_attr == service_instance.class_attr.class_attr

    # attr_1 is different for all instances of SubClass
    assert service_instance.attr.attr_1 != service_instance.class_attr.attr_1

    # instances of SubSubClass are unequal
    assert service_instance.attr.attr_1 != service_instance.class_attr.class_attr

    service_instance.class_attr.class_attr.name = "Ho"
    assert "ServiceClass.class_attr.class_attr.name changed to Ho" in caplog.text
    assert "ServiceClass.attr.class_attr.name changed to Ho" in caplog.text
    caplog.clear()

    service_instance.class_attr.attr_1.name = "Ho"
    assert "ServiceClass.class_attr.attr_1.name changed to Ho" in caplog.text
    assert "ServiceClass.attr.attr_1.name changed to Ho" not in caplog.text
    caplog.clear()

    service_instance.attr.class_attr.name = "Ho"
    assert "ServiceClass.class_attr.class_attr.name changed to Ho" in caplog.text
    assert "ServiceClass.attr.class_attr.name changed to Ho" in caplog.text
    caplog.clear()

    service_instance.attr.attr_1.name = "Ho"
    assert "ServiceClass.attr.attr_1.name changed to Ho" in caplog.text
    assert "ServiceClass.class_attr.attr_1.name changed to Ho" not in caplog.text
    caplog.clear()


def test_class_list_attributes(caplog: LogCaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"

    subclass_instance = SubClass()

    class ServiceClass(DataService):
        attr_list = [SubClass() for _ in range(2)]
        attr_list_2 = [subclass_instance, subclass_instance]
        attr = subclass_instance

    service_instance = ServiceClass()

    assert service_instance.attr_list[0] != service_instance.attr_list[1]

    service_instance.attr_list[0].name = "Ho"
    assert "ServiceClass.attr_list[0].name changed to Ho" in caplog.text
    assert "ServiceClass.attr_list[1].name changed to Ho" not in caplog.text
    caplog.clear()

    service_instance.attr_list[1].name = "Ho"
    assert "ServiceClass.attr_list[0].name changed to Ho" not in caplog.text
    assert "ServiceClass.attr_list[1].name changed to Ho" in caplog.text
    caplog.clear()

    assert service_instance.attr_list_2[0] == service_instance.attr
    assert service_instance.attr_list_2[0] == service_instance.attr_list_2[1]

    service_instance.attr_list_2[0].name = "Ho"
    assert "ServiceClass.attr_list_2[0].name changed to Ho" in caplog.text
    assert "ServiceClass.attr_list_2[1].name changed to Ho" in caplog.text
    assert "ServiceClass.attr.name changed to Ho" in caplog.text
    caplog.clear()

    service_instance.attr_list_2[1].name = "Ho"
    assert "ServiceClass.attr_list_2[0].name changed to Ho" in caplog.text
    assert "ServiceClass.attr_list_2[1].name changed to Ho" in caplog.text
    assert "ServiceClass.attr.name changed to Ho" in caplog.text
    caplog.clear()


def test_nested_class_list_attributes(caplog: LogCaptureFixture) -> None:
    class SubSubClass(DataService):
        name = "Hello"

    subsubclass_instance = SubSubClass()

    class SubClass(DataService):
        attr_list = [subsubclass_instance]

    class ServiceClass(DataService):
        attr = [SubClass()]
        subattr = subsubclass_instance

    service_instance = ServiceClass()

    assert service_instance.attr[0].attr_list[0] == service_instance.subattr

    service_instance.attr[0].attr_list[0].name = "Ho"
    assert "ServiceClass.attr[0].attr_list[0].name changed to Ho" in caplog.text
    assert "ServiceClass.subattr.name changed to Ho" in caplog.text
    caplog.clear()

    service_instance.subattr.name = "Ho"
    assert "ServiceClass.attr[0].attr_list[0].name changed to Ho" in caplog.text
    assert "ServiceClass.subattr.name changed to Ho" in caplog.text
    caplog.clear()


def test_instance_list_attributes(caplog: LogCaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"

    subclass_instance = SubClass()

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr_list = [SubClass() for _ in range(2)]
            self.attr_list_2 = [subclass_instance, subclass_instance]
            self.attr = subclass_instance
            super().__init__()

    service_instance = ServiceClass()

    assert service_instance.attr_list[0] != service_instance.attr_list[1]

    service_instance.attr_list[0].name = "Ho"
    assert "ServiceClass.attr_list[0].name changed to Ho" in caplog.text
    assert "ServiceClass.attr_list[1].name changed to Ho" not in caplog.text
    caplog.clear()

    service_instance.attr_list[1].name = "Ho"
    assert "ServiceClass.attr_list[0].name changed to Ho" not in caplog.text
    assert "ServiceClass.attr_list[1].name changed to Ho" in caplog.text
    caplog.clear()

    assert service_instance.attr_list_2[0] == service_instance.attr
    assert service_instance.attr_list_2[0] == service_instance.attr_list_2[1]

    service_instance.attr_list_2[0].name = "Ho"
    assert "ServiceClass.attr.name changed to Ho" in caplog.text
    assert "ServiceClass.attr_list_2[0].name changed to Ho" in caplog.text
    assert "ServiceClass.attr_list_2[1].name changed to Ho" in caplog.text
    caplog.clear()

    service_instance.attr_list_2[1].name = "Ho"
    assert "ServiceClass.attr.name changed to Ho" in caplog.text
    assert "ServiceClass.attr_list_2[0].name changed to Ho" in caplog.text
    assert "ServiceClass.attr_list_2[1].name changed to Ho" in caplog.text
    caplog.clear()

    service_instance.attr.name = "Ho"
    assert "ServiceClass.attr.name changed to Ho" in caplog.text
    assert "ServiceClass.attr_list_2[0].name changed to Ho" in caplog.text
    assert "ServiceClass.attr_list_2[1].name changed to Ho" in caplog.text
    caplog.clear()


def test_nested_instance_list_attributes(caplog: LogCaptureFixture) -> None:
    class SubSubClass(DataService):
        name = "Hello"

    subsubclass_instance = SubSubClass()

    class SubClass(DataService):
        def __init__(self) -> None:
            self.attr_list = [subsubclass_instance]
            super().__init__()

    class ServiceClass(DataService):
        class_attr = subsubclass_instance

        def __init__(self) -> None:
            self.attr = [SubClass()]
            super().__init__()

    service_instance = ServiceClass()

    assert service_instance.attr[0].attr_list[0] == service_instance.class_attr

    service_instance.attr[0].attr_list[0].name = "Ho"
    assert "ServiceClass.attr[0].attr_list[0].name changed to Ho" in caplog.text
    assert "ServiceClass.class_attr.name changed to Ho" in caplog.text
    caplog.clear()

    service_instance.class_attr.name = "Ho"
    assert "ServiceClass.attr[0].attr_list[0].name changed to Ho" in caplog.text
    assert "ServiceClass.class_attr.name changed to Ho" in caplog.text
    caplog.clear()
