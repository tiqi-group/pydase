# Observer Pattern Implementation in Pydase

## Overview

The [Observer Pattern](https://en.wikipedia.org/wiki/Observer_pattern) is a fundamental design pattern in the `pydase` package, serving as the central communication mechanism for state updates to clients connected to a service.

## How it Works

### The Observable Class

The `Observable` class is at the core of the pattern. It maintains a list of observers and is responsible for notifying them about state changes. It does so by overriding the following methods:

- `__setattr__`: This function emits a notification before and after a new value is set. These two notifications are important to track which attributes are being set to avoid endless recursion (e.g. when accessing a property within another property). Moreover, when setting an attribute to another observable, the former class will add itself as an observer to the latter class, ensuring that nested classes are properly observed.
- `__getattribute__`: This function notifies the observers when a property getter is called, allowing for monitoring state changes in remote devices, as opposed to local instance attributes.

### Custom Collection Classes

To handle collections (like lists and dictionaries), the `Observable` class converts them into custom collection classes `_ObservableList` and `_ObservableDict` that notify observers of any changes in their state. For this, they have to override the methods changing the state, e.g., `__setitem__` or `append` for lists.

### The Observer Class

The `Observer` is the final element in the chain of observers. The notifications of attribute changes it receives include the full access path (in dot-notation) and the new value. It implements logic to handle state changes, like caching, error logging for type changes, etc. This can be extended by custom notification callbacks (implemented using `add_notification_callback` in `DataServiceObserver`). This enables the user to perform specific actions in response to changes. In `pydase`, the web server adds an additional notification callback that emits the websocket events (`sio_callback`).

Furthermore, the `DataServiceObserver` implements logic to reload the values of properties when an attribute change occurs that a property depends on.

- **Dynamic Inspection**: The observer dynamically inspects the observable object (recursively) to create a mapping of properties and their dependencies. This mapping is constructed based on the class or instance attributes used within the source code of the property getters.
- **Dependency Management**: When a change in an attribute occurs, `DataServiceObserver` updates any properties that depend on this attribute. This ensures that the overall state remains consistent and up-to-date, especially in complex scenarios where properties depend on other instance attribute or properties.
