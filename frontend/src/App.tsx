import { useEffect, useReducer, useState } from 'react';
import { Navbar, Button, Form, Nav, Offcanvas, Container } from 'react-bootstrap';
import { hostname, port, socket } from './socket';
import {
  DataServiceComponent,
  DataServiceJSON
} from './components/DataServiceComponent';

type ValueType = boolean | string | number | object;

type State = DataServiceJSON | null;
type Action =
  | { type: 'SET_DATA'; data: DataServiceJSON }
  | { type: 'UPDATE_ATTRIBUTE'; parent_path: string; name: string; value: ValueType };
type NotificationElement = {
  data: { parent_path: string; name: string; value: object };
};

/**
 * A function to update a specific property in a deeply nested object.
 * The property to be updated is specified by a path array.
 *
 * Each path element can be a regular object key or an array index of the
 * form "attribute[index]", where "attribute" is the key of the array in
 * the object and "index" is the index of the element in the array.
 *
 * For array indices, the element at the specified index in the array is
 * updated.
 *
 * If the property to be updated is an object or an array, it is updated
 * recursively.
 *
 * @param {Array<string>} path - An array where each element is a key in the object,
 * forming a path to the property to be updated.
 * @param {object} obj - The object to be updated.
 * @param {object} value - The new value for the property specified by the path.
 * @return {object} - A new object with the specified property updated.
 */
function updateNestedObject(path: Array<string>, obj: object, value: ValueType) {
  // Base case: If the path is empty, return the new value.
  // This means we've reached the nested property to be updated.
  if (path.length === 0) {
    return value;
  }

  // Recursive case: If the path is not empty, split it into the first key and the rest
  // of the path.
  const [first, ...rest] = path;

  // Check if 'first' is an array index.
  const indexMatch = first.match(/^(\w+)\[(\d+)\]$/);

  // If 'first' is an array index of the form "attribute[index]", then update the
  // element at the specified index in the array. Otherwise, update the property
  // specified by 'first' in the object.
  if (indexMatch) {
    const attribute = indexMatch[1];
    const index = parseInt(indexMatch[2]);

    if (Array.isArray(obj[attribute]?.value)) {
      return {
        ...obj,
        [attribute]: {
          ...obj[attribute],
          value: obj[attribute].value.map((item, i) =>
            i === index
              ? {
                  ...item,
                  value: updateNestedObject(rest, item.value || {}, value)
                }
              : item
          )
        }
      };
    } else {
      throw new Error(
        `Expected ${attribute}.value to be an array, but received ${typeof obj[
          attribute
        ]?.value}`
      );
    }
  } else {
    return {
      ...obj,
      [first]: {
        ...obj[first],
        value: updateNestedObject(rest, obj[first]?.value || {}, value)
      }
    };
  }
}

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'SET_DATA':
      return action.data;
    case 'UPDATE_ATTRIBUTE': {
      const path = action.parent_path.split('.').slice(1).concat(action.name);

      return updateNestedObject(path, state, action.value);
    }
    default:
      throw new Error();
  }
};

const App = () => {
  const [state, dispatch] = useReducer(reducer, null);
  const [isInstantUpdate, setIsInstantUpdate] = useState(true);
  const [showSettings, setShowSettings] = useState(false);

  const handleCloseSettings = () => setShowSettings(false);
  const handleShowSettings = () => setShowSettings(true);

  useEffect(() => {
    // Fetch data from the API when the component mounts
    fetch(`http://${hostname}:${port}/service-properties`)
      .then((response) => response.json())
      .then((data: DataServiceJSON) => dispatch({ type: 'SET_DATA', data }));

    function onNotify(value: NotificationElement) {
      dispatch({
        type: 'UPDATE_ATTRIBUTE',
        parent_path: value.data.parent_path,
        name: value.data.name,
        value: value.data.value
      });
    }

    socket.on('notify', onNotify);

    return () => {
      socket.off('notify', onNotify);
    };
  }, []);

  // While the data is loading
  if (!state) {
    return <p>Loading...</p>;
  }
  return (
    <>
      <Navbar expand={false} bg="primary" variant="dark" fixed="top">
        <Container fluid>
          <Navbar.Brand href="#home">My App</Navbar.Brand>
          <Navbar.Toggle aria-controls="offcanvasNavbar" onClick={handleShowSettings} />
        </Container>
      </Navbar>

      <Offcanvas show={showSettings} onHide={handleCloseSettings} placement="end">
        <Offcanvas.Header closeButton>
          <Offcanvas.Title>Settings</Offcanvas.Title>
        </Offcanvas.Header>
        <Offcanvas.Body>
          <Form.Check
            checked={isInstantUpdate}
            onChange={(e) => setIsInstantUpdate(e.target.checked)}
            type="switch"
            label="Enable Instant Update"
          />
          {/* Add any additional controls you want here */}
        </Offcanvas.Body>
      </Offcanvas>

      <div className="App">
        <DataServiceComponent
          props={state as DataServiceJSON}
          isInstantUpdate={isInstantUpdate}
        />
      </div>
    </>
  );
};

export default App;
