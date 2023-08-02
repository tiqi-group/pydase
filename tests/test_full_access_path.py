from pyDataInterface import DataService


def test_class_attributes() -> None:
    class SubClass(DataService):
        pass

    class ServiceClass(DataService):
        attr_1 = SubClass()

    test_service = ServiceClass()
    assert test_service.attr_1._full_access_path == {"ServiceClass.attr_1"}


def test_instance_attributes() -> None:
    class SubClass(DataService):
        pass

    class ServiceClass(DataService):
        def __init__(self):
            self.attr_1 = SubClass()
            super().__init__()

    test_service = ServiceClass()
    assert test_service.attr_1._full_access_path == {"ServiceClass.attr_1"}


def test_reused_instance_attributes() -> None:
    class SubClass(DataService):
        pass

    subclass_instance = SubClass()

    class ServiceClass(DataService):
        def __init__(self):
            self.attr_1 = subclass_instance
            self.attr_2 = subclass_instance
            super().__init__()

    test_service = ServiceClass()
    assert test_service.attr_1._full_access_path == {
        "ServiceClass.attr_1",
        "ServiceClass.attr_2",
    }
    assert test_service.attr_2._full_access_path == {
        "ServiceClass.attr_1",
        "ServiceClass.attr_2",
    }

    assert test_service.attr_1._full_access_path == {
        "ServiceClass.attr_1",
        "ServiceClass.attr_2",
    }


def test_reused_attributes_mixed() -> None:
    class SubClass(DataService):
        pass

    subclass_instance = SubClass()

    class ServiceClass(DataService):
        attr_1 = subclass_instance

        def __init__(self):
            self.attr_2 = subclass_instance
            super().__init__()

    test_service = ServiceClass()
    assert test_service.attr_1._full_access_path == {
        "ServiceClass.attr_1",
        "ServiceClass.attr_2",
    }
    assert test_service.attr_2._full_access_path == {
        "ServiceClass.attr_1",
        "ServiceClass.attr_2",
    }


def test_nested_class_attributes() -> None:
    class SubSubSubClass(DataService):
        pass

    class SubSubClass(DataService):
        attr = SubSubSubClass()

    class SubClass(DataService):
        attr = SubSubClass()

    class ServiceClass(DataService):
        attr = SubClass()

    test_service = ServiceClass()
    assert test_service.attr._full_access_path == {
        "ServiceClass.attr",
    }
    assert test_service.attr.attr._full_access_path == {
        "ServiceClass.attr.attr",
    }
    assert test_service.attr.attr.attr._full_access_path == {
        "ServiceClass.attr.attr.attr",
    }


def test_nested_instance_attributes() -> None:
    class SubSubSubClass(DataService):
        pass

    class SubSubClass(DataService):
        def __init__(self):
            self.attr = SubSubSubClass()
            super().__init__()

    class SubClass(DataService):
        def __init__(self):
            self.attr = SubSubClass()
            super().__init__()

    class ServiceClass(DataService):
        def __init__(self):
            self.attr = SubClass()
            super().__init__()

    test_service = ServiceClass()
    assert test_service.attr._full_access_path == {
        "ServiceClass.attr",
    }
    assert test_service.attr.attr._full_access_path == {
        "ServiceClass.attr.attr",
    }
    assert test_service.attr.attr.attr._full_access_path == {
        "ServiceClass.attr.attr.attr",
    }


def test_advanced_nested_instance_attributes() -> None:
    class SubSubSubClass(DataService):
        pass

    class SubSubClass(DataService):
        def __init__(self):
            self.attr = SubSubSubClass()
            super().__init__()

    subsubclass_instance = SubSubClass()

    class SubClass(DataService):
        def __init__(self):
            self.attr = subsubclass_instance
            super().__init__()

    class ServiceClass(DataService):
        def __init__(self):
            self.attr = SubClass()
            self.subattr = subsubclass_instance
            super().__init__()

    test_service = ServiceClass()
    assert test_service.attr._full_access_path == {
        "ServiceClass.attr",
    }
    assert test_service.attr.attr._full_access_path == {
        "ServiceClass.attr.attr",
        "ServiceClass.subattr",
    }
    assert test_service.attr.attr.attr._full_access_path == {
        "ServiceClass.attr.attr.attr",
        "ServiceClass.subattr.attr",  # as the SubSubSubClass does not implement anything, both subattr.attr and attr.attr.attr refer to the same instance
    }


def test_advanced_nested_class_attributes() -> None:
    class SubSubSubClass(DataService):
        pass

    class SubSubClass(DataService):
        attr = SubSubSubClass()

    class SubClass(DataService):
        attr = SubSubClass()

    class ServiceClass(DataService):
        attr = SubClass()
        subattr = SubSubClass()

    test_service = ServiceClass()
    assert test_service.attr._full_access_path == {
        "ServiceClass.attr",
    }
    assert test_service.subattr._full_access_path == {
        "ServiceClass.subattr",
    }
    assert test_service.attr.attr._full_access_path == {
        "ServiceClass.attr.attr",
    }
    assert test_service.attr.attr.attr._full_access_path == {
        "ServiceClass.attr.attr.attr",
        "ServiceClass.subattr.attr",  # as the SubSubSubClass does not implement anything, both subattr.attr and attr.attr.attr refer to the same instance
    }


def test_advanced_nested_attributes_mixed() -> None:
    class SubSubClass(DataService):
        pass

    class SubClass(DataService):
        attr = SubSubClass()

        def __init__(self):
            self.attr_1 = SubSubClass()
            super().__init__()

    class ServiceClass(DataService):
        subattr = SubClass()

        def __init__(self):
            self.attr = SubClass()
            super().__init__()

    test_service = ServiceClass()
    assert test_service.attr._full_access_path == {
        "ServiceClass.attr",
    }
    assert test_service.subattr._full_access_path == {
        "ServiceClass.subattr",
    }

    # Subclass.attr is the same for all instances
    assert test_service.attr.attr == test_service.subattr.attr
    assert test_service.attr.attr._full_access_path == {
        "ServiceClass.attr.attr",
        "ServiceClass.subattr.attr",
    }
    assert test_service.subattr.attr._full_access_path == {
        "ServiceClass.subattr.attr",
        "ServiceClass.attr.attr",
    }

    # attr_1 is different for all instances of SubClass
    assert test_service.attr.attr_1 != test_service.subattr.attr
    assert test_service.attr.attr_1 != test_service.subattr.attr_1
    assert test_service.subattr.attr_1._full_access_path == {
        "ServiceClass.subattr.attr_1",
    }
    assert test_service.attr.attr_1._full_access_path == {
        "ServiceClass.attr.attr_1",
    }


def test_class_list_attributes() -> None:
    class SubClass(DataService):
        pass

    subclass_instance = SubClass()

    class ServiceClass(DataService):
        attr_list = [SubClass() for _ in range(2)]
        attr_list_2 = [subclass_instance, subclass_instance]
        attr = subclass_instance

    test_service = ServiceClass()
    assert test_service.attr_list[0] != test_service.attr_list[1]
    assert test_service.attr_list[0]._full_access_path == {
        "ServiceClass.attr_list[0]",
    }
    assert test_service.attr_list[1]._full_access_path == {
        "ServiceClass.attr_list[1]",
    }

    assert test_service.attr_list_2[0] == test_service.attr
    assert test_service.attr_list_2[0] == test_service.attr_list_2[1]
    assert test_service.attr_list_2[0]._full_access_path == {
        "ServiceClass.attr",
        "ServiceClass.attr_list_2[0]",
        "ServiceClass.attr_list_2[1]",
    }
    assert test_service.attr_list_2[1]._full_access_path == {
        "ServiceClass.attr",
        "ServiceClass.attr_list_2[0]",
        "ServiceClass.attr_list_2[1]",
    }


def test_nested_class_list_attributes() -> None:
    class SubSubClass(DataService):
        pass

    subsubclass_instance = SubSubClass()

    class SubClass(DataService):
        attr_list = [subsubclass_instance]

    class ServiceClass(DataService):
        attr = [SubClass()]
        subattr = subsubclass_instance

    test_service = ServiceClass()
    assert test_service.attr[0].attr_list[0] == test_service.subattr
    assert test_service.attr[0].attr_list[0]._full_access_path == {
        "ServiceClass.attr[0].attr_list[0]",
        "ServiceClass.subattr",
    }


def test_instance_list_attributes() -> None:
    class SubClass(DataService):
        pass

    subclass_instance = SubClass()

    class ServiceClass(DataService):
        def __init__(self):
            self.attr_list = [SubClass() for _ in range(2)]
            self.attr_list_2 = [subclass_instance, subclass_instance]
            self.attr = subclass_instance
            super().__init__()

    test_service = ServiceClass()
    assert test_service.attr_list[0] != test_service.attr_list[1]
    assert test_service.attr_list[0]._full_access_path == {
        "ServiceClass.attr_list[0]",
    }
    assert test_service.attr_list[1]._full_access_path == {
        "ServiceClass.attr_list[1]",
    }

    assert test_service.attr_list_2[0] == test_service.attr
    assert test_service.attr_list_2[0] == test_service.attr_list_2[1]
    assert test_service.attr_list_2[0]._full_access_path == {
        "ServiceClass.attr",
        "ServiceClass.attr_list_2[0]",
        "ServiceClass.attr_list_2[1]",
    }
    assert test_service.attr_list_2[1]._full_access_path == {
        "ServiceClass.attr",
        "ServiceClass.attr_list_2[0]",
        "ServiceClass.attr_list_2[1]",
    }


def test_nested_instance_list_attributes() -> None:
    class SubSubClass(DataService):
        pass

    subsubclass_instance = SubSubClass()

    class SubClass(DataService):
        def __init__(self):
            self.attr_list = [subsubclass_instance]
            super().__init__()

    class ServiceClass(DataService):
        subattr = subsubclass_instance

        def __init__(self):
            self.attr = [SubClass()]
            super().__init__()

    test_service = ServiceClass()
    assert test_service.attr[0].attr_list[0] == test_service.subattr
    assert test_service.attr[0].attr_list[0]._full_access_path == {
        "ServiceClass.attr[0].attr_list[0]",
        "ServiceClass.subattr",
    }
