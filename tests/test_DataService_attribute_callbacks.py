from pytest import CaptureFixture

from pyDataService import DataService


def test_class_attributes(capsys: CaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"

    class ServiceClass(DataService):
        attr_1 = SubClass()

    service_instance = ServiceClass()
    _ = capsys.readouterr()
    service_instance.attr_1.name = "Hi"

    captured = capsys.readouterr()
    assert captured.out.strip() == "ServiceClass.attr_1.name = Hi"


def test_instance_attributes(capsys: CaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr_1 = SubClass()
            super().__init__()

    service_instance = ServiceClass()
    _ = capsys.readouterr()
    service_instance.attr_1.name = "Hi"

    captured = capsys.readouterr()
    assert captured.out.strip() == "ServiceClass.attr_1.name = Hi"


def test_class_attribute(capsys: CaptureFixture) -> None:
    class ServiceClass(DataService):
        attr = 0

    service_instance = ServiceClass()

    service_instance.attr = 1
    captured = capsys.readouterr()
    assert captured.out == "ServiceClass.attr = 1\n"


def test_instance_attribute(capsys: CaptureFixture) -> None:
    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr = "Hello World"
            super().__init__()

    service_instance = ServiceClass()

    service_instance.attr = "Hello"
    captured = capsys.readouterr()
    assert captured.out == "ServiceClass.attr = Hello\n"


def test_reused_instance_attributes(capsys: CaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"

    subclass_instance = SubClass()

    class ServiceClass(DataService):
        def __init__(self) -> None:
            self.attr_1 = subclass_instance
            self.attr_2 = subclass_instance
            super().__init__()

    service_instance = ServiceClass()
    _ = capsys.readouterr()
    service_instance.attr_1.name = "Hi"

    captured = capsys.readouterr()
    assert service_instance.attr_1 == service_instance.attr_2
    expected_output = sorted(
        [
            "ServiceClass.attr_1.name = Hi",
            "ServiceClass.attr_2.name = Hi",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_reused_attributes_mixed(capsys: CaptureFixture) -> None:
    class SubClass(DataService):
        pass

    subclass_instance = SubClass()

    class ServiceClass(DataService):
        attr_1 = subclass_instance

        def __init__(self) -> None:
            self.attr_2 = subclass_instance
            super().__init__()

    service_instance = ServiceClass()
    _ = capsys.readouterr()
    service_instance.attr_1.name = "Hi"

    captured = capsys.readouterr()
    assert service_instance.attr_1 == service_instance.attr_2
    expected_output = sorted(
        [
            "ServiceClass.attr_1.name = Hi",
            "ServiceClass.attr_2.name = Hi",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_nested_class_attributes(capsys: CaptureFixture) -> None:
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
    _ = capsys.readouterr()
    service_instance.attr.attr.attr.name = "Hi"
    service_instance.attr.attr.name = "Hou"
    service_instance.attr.name = "foo"
    service_instance.name = "bar"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr.attr.attr.name = Hi",
            "ServiceClass.attr.attr.name = Hou",
            "ServiceClass.attr.name = foo",
            "ServiceClass.name = bar",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_nested_instance_attributes(capsys: CaptureFixture) -> None:
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
    _ = capsys.readouterr()
    service_instance.attr.attr.attr.name = "Hi"
    service_instance.attr.attr.name = "Hou"
    service_instance.attr.name = "foo"
    service_instance.name = "bar"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr.attr.attr.name = Hi",
            "ServiceClass.attr.attr.name = Hou",
            "ServiceClass.attr.name = foo",
            "ServiceClass.name = bar",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_advanced_nested_class_attributes(capsys: CaptureFixture) -> None:
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
    _ = capsys.readouterr()
    service_instance.attr.attr.attr.name = "Hi"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr.attr.attr.name = Hi",
            "ServiceClass.subattr.attr.name = Hi",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output
    service_instance.subattr.attr.name = "Ho"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr.attr.attr.name = Ho",
            "ServiceClass.subattr.attr.name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_advanced_nested_instance_attributes(capsys: CaptureFixture) -> None:
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
    _ = capsys.readouterr()
    service_instance.attr.attr.attr.name = "Hi"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr.attr.attr.name = Hi",
            "ServiceClass.subattr.attr.name = Hi",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output
    service_instance.subattr.attr.name = "Ho"

    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr.attr.attr.name = Ho",
            "ServiceClass.subattr.attr.name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_advanced_nested_attributes_mixed(capsys: CaptureFixture) -> None:
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

    _ = capsys.readouterr()

    service_instance.class_attr.class_attr.name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.class_attr.class_attr.name = Ho",
            "ServiceClass.attr.class_attr.name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    service_instance.class_attr.attr_1.name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(["ServiceClass.class_attr.attr_1.name = Ho"])
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    service_instance.attr.class_attr.name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr.class_attr.name = Ho",
            "ServiceClass.class_attr.class_attr.name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    service_instance.attr.attr_1.name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(["ServiceClass.attr.attr_1.name = Ho"])
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_class_list_attributes(capsys: CaptureFixture) -> None:
    class SubClass(DataService):
        name = "Hello"

    subclass_instance = SubClass()

    class ServiceClass(DataService):
        attr_list = [SubClass() for _ in range(2)]
        attr_list_2 = [subclass_instance, subclass_instance]
        attr = subclass_instance

    service_instance = ServiceClass()
    _ = capsys.readouterr()

    assert service_instance.attr_list[0] != service_instance.attr_list[1]

    service_instance.attr_list[0].name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr_list[0].name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    service_instance.attr_list[1].name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr_list[1].name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    assert service_instance.attr_list_2[0] == service_instance.attr
    assert service_instance.attr_list_2[0] == service_instance.attr_list_2[1]

    service_instance.attr_list_2[0].name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr_list_2[0].name = Ho",
            "ServiceClass.attr_list_2[1].name = Ho",
            "ServiceClass.attr.name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    service_instance.attr_list_2[1].name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr_list_2[0].name = Ho",
            "ServiceClass.attr_list_2[1].name = Ho",
            "ServiceClass.attr.name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_nested_class_list_attributes(capsys: CaptureFixture) -> None:
    class SubSubClass(DataService):
        name = "Hello"

    subsubclass_instance = SubSubClass()

    class SubClass(DataService):
        attr_list = [subsubclass_instance]

    class ServiceClass(DataService):
        attr = [SubClass()]
        subattr = subsubclass_instance

    service_instance = ServiceClass()
    _ = capsys.readouterr()

    assert service_instance.attr[0].attr_list[0] == service_instance.subattr

    service_instance.attr[0].attr_list[0].name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr[0].attr_list[0].name = Ho",
            "ServiceClass.subattr.name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    service_instance.subattr.name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr[0].attr_list[0].name = Ho",
            "ServiceClass.subattr.name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_instance_list_attributes(capsys: CaptureFixture) -> None:
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
    _ = capsys.readouterr()

    assert service_instance.attr_list[0] != service_instance.attr_list[1]

    service_instance.attr_list[0].name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(["ServiceClass.attr_list[0].name = Ho"])
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    service_instance.attr_list[1].name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(["ServiceClass.attr_list[1].name = Ho"])
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    assert service_instance.attr_list_2[0] == service_instance.attr
    assert service_instance.attr_list_2[0] == service_instance.attr_list_2[1]

    service_instance.attr_list_2[0].name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr.name = Ho",
            "ServiceClass.attr_list_2[0].name = Ho",
            "ServiceClass.attr_list_2[1].name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    service_instance.attr_list_2[1].name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr.name = Ho",
            "ServiceClass.attr_list_2[0].name = Ho",
            "ServiceClass.attr_list_2[1].name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    service_instance.attr.name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr.name = Ho",
            "ServiceClass.attr_list_2[0].name = Ho",
            "ServiceClass.attr_list_2[1].name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output


def test_nested_instance_list_attributes(capsys: CaptureFixture) -> None:
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
    _ = capsys.readouterr()

    assert service_instance.attr[0].attr_list[0] == service_instance.class_attr

    service_instance.attr[0].attr_list[0].name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr[0].attr_list[0].name = Ho",
            "ServiceClass.class_attr.name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output

    service_instance.class_attr.name = "Ho"
    captured = capsys.readouterr()
    expected_output = sorted(
        [
            "ServiceClass.attr[0].attr_list[0].name = Ho",
            "ServiceClass.class_attr.name = Ho",
        ]
    )
    actual_output = sorted(captured.out.strip().split("\n"))
    assert actual_output == expected_output
