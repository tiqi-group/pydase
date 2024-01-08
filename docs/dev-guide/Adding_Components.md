# Adding Components to `pydase`

This guide provides a step-by-step process for adding new components to the `pydase` package. Components in `pydase` consist of both backend (Python) and frontend (React) parts. They work together to create interactive and dynamic data services.

## Overview

A component in `pydase` is a unique combination of a backend class (e.g., `Image`) and its corresponding frontend React component. The backend class stores the attributes needed for the component, and possibly methods for setting those in the backend, while the frontend part is responsible for rendering and interacting with the component.

## Adding a Backend Component to `pydase`

Backend components belong in the `src/pydase/components` directory.

### Step 1: Create a New Python File in the Components Directory

Navigate to the `src/pydase/components` directory and create a new Python file for your component. The name of the file should be descriptive of the component's functionality.

For example, for a `Image` component, create a file named `image.py`.

### Step 2: Define the Backend Class

Within the newly created file, define a Python class representing the component. This class should inherit from `DataService` and contains the attributes that the frontend needs to render the component. Every public attribute defined in this class will synchronise across the clients. It can also contain methods which can be used to interact with the component from the backend.

For the `Image` component, the class may look like this:

```python
# file: pydase/components/image.py

from pydase.data_service.data_service import DataService


class Image(DataService):
    def __init__(
        self,
        image_representation: bytes = b"",
    ) -> None:
        self.image_representation = image_representation
        super().__init__()

    # need to decode the bytes
    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "value":
            if isinstance(__value, bytes):
                __value = __value.decode()
        return super().__setattr__(__name, __value)

```

So, changing the `image_representation` will push the updated value to the browsers connected to the service.

### Step 3: Register the Backend Class

The component should be added to the `__init__.py` file to ensure `pydase` handles them properly:

```python
# file: pydase/components/__init__.py

from pydase.components.image import Image
from pydase.components.number_slider import NumberSlider

__all__ = [
    "NumberSlider",
    "Image",  # add the new components here
]

```

### Step 4: Implement Necessary Methods (Optional)

If your component requires specific logic or methods, implement them within the class. Document any public methods or attributes to ensure that other developers understand their purpose and usage.

### Step 5: Write Tests for the Component (Recommended)

Consider writing unit tests for the component to verify its behavior. Place the tests in the appropriate directory within the `tests` folder.

For example, a test for the `Image` component could look like this:

```python
from pytest import CaptureFixture

from pydase.components.image import Image
from pydase.data_service.data_service import DataService


def test_Image(capsys: CaptureFixture) -> None:
    class ServiceClass(DataService):
        image = Image()

    service = ServiceClass()
    # ...
```


## Adding a Frontend Component to `pydase`

Frontend components in `pydase` live in the `frontend/src/components/` directory. Follow these steps to create and add a new frontend component:

### Step 1: Create a New React Component File in the Components Directory

Navigate to the `frontend/src/components/` directory and create a new React component file for your component. The name of the file should be descriptive of the component's functionality and reflect the naming conventions used in your project.

For example, for an `Image` component, create a file named `ImageComponent.tsx`.

### Step 2: Write the React Component Code

Write the React component code, following the structure and patterns used in existing components. Make sure to import necessary libraries and dependencies.

For example, for the `Image` component, a template could look like this:

```tsx
import { setAttribute, runMethod } from '../socket';  // use this when your component should sets values of attributes
                                                      // or runs a method, respectively
import { DocStringComponent } from './DocStringComponent';
import React, { useEffect, useRef, useState } from 'react';
import { WebSettingsContext } from '../WebSettings';
import { Card, Collapse, Image } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { ChevronDown, ChevronRight } from 'react-bootstrap-icons';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
import { LevelName } from './NotificationsComponent';

interface ImageComponentProps {
  name: string;
  parentPath?: string;
  readOnly: boolean;
  docString: string;
  addNotification: (message: string, levelname?: LevelName) => void;
  // Define your component specific props here
  value: string;
  format: string;
}

export const ImageComponent = React.memo((props: ImageComponentProps) => {
  const { name, parentPath, value, docString, format, addNotification } = props;

  const renderCount = useRef(0);
  const [open, setOpen] = useState(true);  // add this if you want to expand/collapse your component
  const fullAccessPath = [parentPath, name].filter((element) => element).join('.');
  const id = getIdFromFullAccessPath(fullAccessPath);

  // Web settings contain the user-defined display name of the components (and possibly more later)
  const webSettings = useContext(WebSettingsContext);
  let displayName = name;

  if (webSettings[fullAccessPath] && webSettings[fullAccessPath].displayName) {
    displayName = webSettings[fullAccessPath].displayName;
  }

  useEffect(() => {
    renderCount.current++;
  });

  // This will trigger a notification if notifications are enabled.
  useEffect(() => {
    addNotification(`${parentPath}.${name} changed to ${value}.`);
  }, [props.value]);

  // Your component logic here

  return (
    <div className={'imageComponent'} id={id}>
      {/* Add the Card and Collapse components here if you want to be able to expand and
       collapse your component.  */}
      <Card>
        <Card.Header
          onClick={() => setOpen(!open)}
          style={{ cursor: 'pointer' }} // Change cursor style on hover
        >
          {displayName} {open ? <ChevronDown /> : <ChevronRight />}
        </Card.Header>
        <Collapse in={open}>
          <Card.Body>
            {process.env.NODE_ENV === 'development' && (
              <p>Render count: {renderCount.current}</p>
            )}
            <DocStringComponent docString={docString} />
            {/* Your component TSX here */}
          </Card.Body>
        </Collapse>
      </Card>
    </div>
  );
});
```

### Step 3: Emitting Updates to the Backend

React components in the frontend often need to send updates to the backend, particularly when user interactions modify the component's state or data. In `pydase`, we use `socketio` for smooth communication of these changes. To handle updates, we primarily use two events: `setAttribute` for updating attributes, and `runMethod` for executing backend methods. Below is a detailed guide on how to emit these events from your frontend component:

1. **Setup for emitting events**:
    First, ensure you've imported the necessary functions from the `socket` module for both updating attributes and executing methods:

    ```tsx
    import { setAttribute, runMethod } from '../socket';
    ```

2. **Event Parameters**:

    - When using **`setAttribute`**, we send three main pieces of data:
        - `name`: The name of the attribute within the `DataService` instance to update.
        - `parentPath`: The access path for the parent object of the attribute to be updated.
        - `value`: The new value for the attribute, which must match the backend attribute type.
    - For **`runMethod`**, the parameters are slightly different:
        - `name`: The name of the method to be executed in the backend.
        - `parentPath`: Similar to `setAttribute`, it's the access path to the object containing the method.
        - `kwargs`: A dictionary of keyword arguments that the method requires.

3. **Implementation**:

    For illustation, take the `ButtonComponent`. When the button state changes, we want to send this update to the backend:

    ```tsx
    import { setAttribute } from '../socket';
    // ... (other imports)
    
    export const ButtonComponent = React.memo((props: ButtonComponentProps) => {
      // ... 
      const { name, parentPath, value } = props;
      let displayName = ...  // to access the user-defined display name

      const setChecked = (checked: boolean) => {
        setAttribute(name, parentPath, checked);
      };

      return (
        <ToggleButton
          checked={value}
          value={parentPath}
          // ... other props
          onChange={(e) => setChecked(e.currentTarget.checked)}>
          {displayName}
        </ToggleButton>
      );
    });
    ```

    In this example, whenever the button's checked state changes (`onChange` event), we invoke the `setChecked` method, which in turn emits the new state to the backend using `setAttribute`.


### Step 4: Add the New Component to the GenericComponent

The `GenericComponent` is responsible for rendering different types of components based on the attribute type. You can add the new `ImageComponent` to the `GenericComponent` by following these sub-steps:

#### 1. Import the New Component

At the beginning of the `GenericComponent` file, import the newly created `ImageComponent`:

```tsx
// file: frontend/src/components/GenericComponent.tsx

import { ImageComponent } from './ImageComponent';
```

#### 2. Update the AttributeType

Update the `AttributeType` type definition to include the new type for the `ImageComponent`. 

For example, if the new attribute type is `'Image'` (which should correspond to the name of the backend component class), you can add it to the union:

```tsx
type AttributeType =
  | 'str'
  | 'bool'
  | 'float'
  | 'int'
  | 'Quantity'
  | 'list'
  | 'method'
  | 'DataService'
  | 'Enum'
  | 'NumberSlider'
  | 'Image'; // Add the name of the backend component class here
```

#### 3. Add a Conditional Branch for the New Component

Inside the `GenericComponent` function, add a new conditional branch to render the `ImageComponent` when the attribute type is `'Image'`:

```tsx
} else if (attribute.type === 'Image') {
  return (
    <ImageComponent
      name={name}
      parentPath={parentPath}
      readOnly={attribute.readonly}
      docString={attribute.doc}
      addNotification={addNotification}
      // Add any other specific props for the ImageComponent here
      value={attribute.value['value']['value'] as string}
      format={attribute.value['format']['value'] as string}
    />
  );
} else {
  // other code
```

Make sure to update the props passed to the `ImageComponent` based on its specific requirements.

### Step 5: Adding Custom Notification Message (Optional)

In some cases, you may want to provide a custom notification message to the user when an attribute of a specific type is updated. This can be useful for enhancing user experience and providing contextual information about the changes.

For example, updating an `Image` component corresponds to setting a very long string. We don't want to display the whole string in the notification but just notify the user that the image was updated (and maybe also the format).

To create a custom notification message, you can update the message passed to the `addNotification` method in the `useEffect` hook in the component file file. For the `ImageComponent`, this could look like this:

```tsx
useEffect(() => {
  addNotification(`${parentPath}.${name} changed.`);
}, [props.value]);
```

However, you might want to use the `addNotification` at different places. For an example, see the [MethodComponent](../../frontend/src/components/MethodComponent.tsx).
**Note**: you can specify the notification level by passing a string of type `LevelName` (one of 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'). The default value is 'DEBUG'.

### Step 6: Write Tests for the Component (TODO)

Test the frontend component to ensure that it renders correctly and interacts seamlessly
with the backend. Consider writing unit tests using a testing library like Jest or React
Testing Library, and manually test the component in the browser.
