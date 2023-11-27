import { useCallback, useEffect, useReducer, useRef, useState } from 'react';
import { Navbar, Form, Offcanvas, Container } from 'react-bootstrap';
import { hostname, port, socket } from './socket';
import {
  DataServiceComponent,
  DataServiceJSON
} from './components/DataServiceComponent';
import './App.css';
import {
  Notifications,
  Notification,
  LevelName
} from './components/NotificationsComponent';
import { ConnectionToast } from './components/ConnectionToast';
import { SerializedValue, setNestedValueByPath, State } from './utils/stateUtils';

type Action =
  | { type: 'SET_DATA'; data: State }
  | {
      type: 'UPDATE_ATTRIBUTE';
      parentPath: string;
      name: string;
      value: SerializedValue;
    };
type UpdateMessage = {
  data: { parent_path: string; name: string; value: SerializedValue };
};
type LogMessage = {
  levelname: LevelName;
  message: string;
};

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'SET_DATA':
      return action.data;
    case 'UPDATE_ATTRIBUTE': {
      const pathList = action.parentPath.split('.').slice(1).concat(action.name);
      const joinedPath = pathList.join('.');

      return setNestedValueByPath(state, joinedPath, action.value);
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
  const [notifications, setNotifications] = useState<Notification[]>([]);
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
        .then((data: State) => dispatch({ type: 'SET_DATA', data }));
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
    socket.on('log', onLogMessage);

    return () => {
      socket.off('notify', onNotify);
      socket.off('log', onLogMessage);
    };
  }, []);

  // Adding useCallback to prevent notify to change causing a re-render of all
  // components
  const addNotification = useCallback(
    (message: string, levelname: LevelName = 'DEBUG') => {
      // Getting the current time in the required format
      const timeStamp = new Date().toISOString().substring(11, 19);
      // Adding an id to the notification to provide a way of removing it
      const id = Math.random();

      // Custom logic for notifications
      setNotifications((prevNotifications) => [
        { levelname, id, message, timeStamp },
        ...prevNotifications
      ]);
    },
    []
  );

  const removeNotificationById = (id: number) => {
    setNotifications((prevNotifications) =>
      prevNotifications.filter((n) => n.id !== id)
    );
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

  function onLogMessage(value: LogMessage) {
    addNotification(value.message, value.levelname);
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
        removeNotificationById={removeNotificationById}
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
