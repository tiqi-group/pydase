::: pydase.data_service
    handler: python

::: pydase.server.server
    handler: python

::: pydase.server.web_server
    handler: python

::: pydase.client
    handler: python

::: pydase.components
    handler: python

::: pydase.task
    handler: python
    options:
      inherited_members: false
      show_submodules: true

::: pydase.utils.serialization.serializer
    handler: python

::: pydase.utils.serialization.deserializer
    handler: python
    options:
      show_root_heading: true
      show_root_toc_entry: false
      show_symbol_type_heading: true
      show_symbol_type_toc: true

::: pydase.utils.serialization.types
    handler: python

::: pydase.utils.decorators
    handler: python
    options:
      filters: ["!render_in_frontend"]

::: pydase.units
    handler: python

::: pydase.config
    handler: python
