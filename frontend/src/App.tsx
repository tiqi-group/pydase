import { useCallback, useEffect, useReducer, useRef, useState } from 'react';
import { Navbar, Form, Offcanvas, Container } from 'react-bootstrap';
import { hostname, port, socket } from './socket';
import {
  DataServiceComponent,
  DataServiceJSON
} from './components/DataServiceComponent';
import './App.css';
import { Notifications } from './components/NotificationsComponent';
import { ConnectionToast } from './components/ConnectionToast';

type ValueType = boolean | string | number | object;

type State = DataServiceJSON | null;
type Action =
  | { type: 'SET_DATA'; data: DataServiceJSON }
  | { type: 'UPDATE_ATTRIBUTE'; parentPath: string; name: string; value: ValueType };
type UpdateMessage = {
  data: { parent_path: string; name: string; value: object };
};
type ExceptionMessage = {
  data: { exception: string; type: string };
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
      const path = action.parentPath.split('.').slice(1).concat(action.name);

      return updateNestedObject(path, state, action.value);
    }
    default:
      throw new Error();
  }
};
const App = () => {
  const [state, dispatch] = useReducer(reducer, null);
  const stateRef = useRef(state); // Declare a reference to hold the current state
  const [isInstantUpdate, setIsInstantUpdate] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [exceptions, setExceptions] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  // Keep the state reference up to date
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    // Allow the user to add a custom css file
    fetch(`http://${hostname}:${port}/custom.css`)
      .then((response) => {
        if (response.ok) {
          // If the file exists, create a link element for the custom CSS
          const link = document.createElement('link');
          link.href = `http://${hostname}:${port}/custom.css`;
          link.type = 'text/css';
          link.rel = 'stylesheet';
          document.head.appendChild(link);
        }
      })
      .catch(console.error); // Handle the error appropriately

    socket.on('connect', () => {
      // Fetch data from the API when the client connects
      fetch(`http://${hostname}:${port}/service-properties`)
        .then((response) => response.json())
        .then((data: DataServiceJSON) => dispatch({ type: 'SET_DATA', data }));
      setConnectionStatus('connected');
    });
    socket.on('disconnect', () => {
      setConnectionStatus('disconnected');
      setTimeout(() => {
        // Only set "reconnecting" is the state is still "disconnected"
        // E.g. when the client has already reconnected
        setConnectionStatus((currentState) =>
          currentState === 'disconnected' ? 'reconnecting' : currentState
        );
      }, 2000);
    });

    socket.on('notify', onNotify);
    socket.on('exception', onException);

    return () => {
      socket.off('notify', onNotify);
      socket.off('exception', onException);
    };
  }, []);

  // Adding useCallback to prevent notify to change causing a re-render of all
  // components
  const addNotification = useCallback((text: string) => {
    // Getting the current time in the required format
    const timeString = new Date().toISOString().substring(11, 19);
    // Adding an id to the notification to provide a way of removing it
    const id = Math.random();

    // Custom logic for notifications
    setNotifications((prevNotifications) => [
      { id, text, time: timeString },
      ...prevNotifications
    ]);
  }, []);

  const notifyException = (text: string) => {
    // Getting the current time in the required format
    const timeString = new Date().toISOString().substring(11, 19);
    // Adding an id to the notification to provide a way of removing it
    const id = Math.random();

    // Custom logic for notifications
    setExceptions((prevNotifications) => [
      { id, text, time: timeString },
      ...prevNotifications
    ]);
  };
  const removeNotificationById = (id: number) => {
    setNotifications((prevNotifications) =>
      prevNotifications.filter((n) => n.id !== id)
    );
  };

  const removeExceptionById = (id: number) => {
    setExceptions((prevNotifications) => prevNotifications.filter((n) => n.id !== id));
  };

  const handleCloseSettings = () => setShowSettings(false);
  const handleShowSettings = () => setShowSettings(true);

  function onNotify(value: UpdateMessage) {
    // Extracting data from the notification
    const { parent_path: parentPath, name, value: newValue } = value.data;

    // Dispatching the update to the reducer
    dispatch({
      type: 'UPDATE_ATTRIBUTE',
      parentPath,
      name,
      value: newValue
    });
  }

  function onException(value: ExceptionMessage) {
    const newException = `${value.data.type}: ${value.data.exception}.`;
    notifyException(newException);
  }

  // While the data is loading
  if (!state) {
    return <ConnectionToast connectionStatus={connectionStatus} />;
  }
  return (
    <>
      <Navbar expand={false} bg="primary" variant="dark" fixed="top">
        <Container fluid>
          <Navbar.Brand>Data Service App</Navbar.Brand>
          <Navbar.Toggle aria-controls="offcanvasNavbar" onClick={handleShowSettings} />
        </Container>
      </Navbar>

      <Notifications
        showNotification={showNotification}
        notifications={notifications}
        exceptions={exceptions}
        removeNotificationById={removeNotificationById}
        removeExceptionById={removeExceptionById}
      />

      <Offcanvas
        show={showSettings}
        onHide={handleCloseSettings}
        placement="end"
        style={{ zIndex: 9999 }}>
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
          <Form.Check
            checked={showNotification}
            onChange={(e) => setShowNotification(e.target.checked)}
            type="switch"
            label="Show Notifications"
          />
          {/* Add any additional controls you want here */}
        </Offcanvas.Body>
      </Offcanvas>

      <div className="App navbarOffset">
        <DataServiceComponent
          name={''}
          props={state as DataServiceJSON}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
        />
      </div>
      <ConnectionToast connectionStatus={connectionStatus} />
    </>
  );
};

export default App;
