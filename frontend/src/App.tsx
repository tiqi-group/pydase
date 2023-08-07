import { useEffect, useReducer, useRef, useState } from 'react';
import {
  Navbar,
  Form,
  Offcanvas,
  Container,
  Toast,
  ToastContainer
} from 'react-bootstrap';
import { hostname, port, socket } from './socket';
import {
  DataServiceComponent,
  DataServiceJSON
} from './components/DataServiceComponent';
import './App.css';
import { getDataServiceJSONValueByPathAndKey } from './utils/nestedObjectUtils';

type ValueType = boolean | string | number | object;

type State = DataServiceJSON | null;
type Action =
  | { type: 'SET_DATA'; data: DataServiceJSON }
  | { type: 'UPDATE_ATTRIBUTE'; parent_path: string; name: string; value: ValueType };
type UpdateNotification = {
  data: { parent_path: string; name: string; value: object };
};
type ExceptionNotification = {
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
  const stateRef = useRef(state); // Declare a reference to hold the current state

  const [isInstantUpdate, setIsInstantUpdate] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [exceptions, setExceptions] = useState([]); // Exception notifications

  const removeNotificationById = (id: number) => {
    setNotifications((prevNotifications) =>
      prevNotifications.filter((n) => n.id !== id)
    );
  };

  const handleCloseSettings = () => setShowSettings(false);
  const handleShowSettings = () => setShowSettings(true);

  function onNotify(value: UpdateNotification) {
    // Extracting data from the notification
    const { parent_path, name, value: newValue } = value.data;

    // Getting the current time in the required format
    const timeString = new Date().toISOString().substring(11, 8);

    // Dispatching the update to the reducer
    dispatch({
      type: 'UPDATE_ATTRIBUTE',
      parent_path,
      name,
      value: newValue
    });

    // Formatting the value if it is of type 'Quantity'
    let notificationMsg: object | string = newValue;
    const path = parent_path.concat('.', name);
    if (
      getDataServiceJSONValueByPathAndKey(stateRef.current, path, 'type') === 'Quantity'
    ) {
      notificationMsg = `${newValue['magnitude']} ${newValue['unit']}`;
    }

    // Creating a new notification
    const newNotification = {
      id: Math.random(),
      time: timeString,
      text: `Attribute ${parent_path}.${name} updated to ${notificationMsg}.`
    };

    // Adding the new notification to the list
    setNotifications((prevNotifications) => [newNotification, ...prevNotifications]);
  }

  function onException(value: ExceptionNotification) {
    const currentTime = new Date();
    const timeString = currentTime.toISOString().substr(11, 8);

    const newNotification = {
      type: 'exception',
      id: Math.random(),
      time: timeString,
      text: `${value.data.type}: ${value.data.exception}.`
    };
    setExceptions((prevNotifications) => [newNotification, ...prevNotifications]);
  }

  // Keep the state reference up to date
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    // Fetch data from the API when the component mounts
    fetch(`http://${hostname}:${port}/service-properties`)
      .then((response) => response.json())
      .then((data: DataServiceJSON) => dispatch({ type: 'SET_DATA', data }));

    socket.on('notify', onNotify);
    socket.on('exception', onException);

    return () => {
      socket.off('notify', onNotify);
      socket.off('exception', onException);
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
          <Navbar.Brand>Data Service App</Navbar.Brand>
          <Navbar.Toggle aria-controls="offcanvasNavbar" onClick={handleShowSettings} />
        </Container>
      </Navbar>

      <ToastContainer
        className="navbarOffset toastContainer"
        position="top-end"
        style={{ position: 'fixed' }}>
        {showNotification &&
          notifications.map((notification) => (
            <Toast
              className="notificationToast"
              key={notification.id}
              onClose={() => {
                removeNotificationById(notification.id);
              }}
              onClick={() => {
                removeNotificationById(notification.id);
              }}
              onMouseLeave={() => {
                // For exception type notifications, do not dismiss on mouse leave
                if (notification.type !== 'exception') {
                  removeNotificationById(notification.id);
                }
              }}
              show={true}
              autohide={true}
              delay={2000}>
              <Toast.Header
                closeButton={notification.type === 'exception'}
                className={`${'notificationToast'} text-right`}>
                <strong className="me-auto">Notification</strong>
                <small>{notification.time}</small>
              </Toast.Header>
              <Toast.Body>{notification.text}</Toast.Body>
            </Toast>
          ))}
        {exceptions.map((exception) => (
          // Always render exceptions, regardless of showNotification
          <Toast
            className="exceptionToast"
            key={exception.id}
            onClose={() => {
              setExceptions((prevExceptions) =>
                prevExceptions.filter((e) => e.id !== exception.id)
              );
            }}
            show={true}
            autohide={false}>
            <Toast.Header closeButton className="exceptionToast text-right">
              <strong className="me-auto">Exception</strong>
              <small>{exception.time}</small>
            </Toast.Header>
            <Toast.Body>{exception.text}</Toast.Body>
          </Toast>
        ))}
      </ToastContainer>

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
          props={state as DataServiceJSON}
          isInstantUpdate={isInstantUpdate}
        />
      </div>
    </>
  );
};

export default App;
