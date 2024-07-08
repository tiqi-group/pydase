import { useCallback, useEffect, useReducer, useState } from "react";
import { Navbar, Form, Offcanvas, Container } from "react-bootstrap";
import { hostname, port, socket } from "./socket";
import "./App.css";
import {
  Notifications,
  Notification,
  LevelName,
} from "./components/NotificationsComponent";
import { ConnectionToast } from "./components/ConnectionToast";
import { setNestedValueByPath, State } from "./utils/stateUtils";
import { WebSettingsContext, WebSetting } from "./WebSettings";
import { GenericComponent } from "./components/GenericComponent";
import { SerializedObject } from "./types/SerializedObject";

type Action =
  | { type: "SET_DATA"; data: State }
  | {
      type: "UPDATE_ATTRIBUTE";
      fullAccessPath: string;
      newValue: SerializedObject;
    };
interface UpdateMessage {
  data: { full_access_path: string; value: SerializedObject };
}
interface LogMessage {
  levelname: LevelName;
  message: string;
}

const reducer = (state: State | null, action: Action): State | null => {
  switch (action.type) {
    case "SET_DATA":
      return action.data;
    case "UPDATE_ATTRIBUTE": {
      if (state === null) {
        return null;
      }
      return {
        ...state,
        value: setNestedValueByPath(
          state.value as Record<string, SerializedObject>,
          action.fullAccessPath,
          action.newValue,
        ),
      };
    }
    default:
      throw new Error();
  }
};
const App = () => {
  const [state, dispatch] = useReducer(reducer, null);
  const [serviceName, setServiceName] = useState<string | null>(null);
  const [webSettings, setWebSettings] = useState<Record<string, WebSetting>>({});
  const [isInstantUpdate, setIsInstantUpdate] = useState(() => {
    const saved = localStorage.getItem("isInstantUpdate");
    return saved !== null ? JSON.parse(saved) : false;
  });
  const [showSettings, setShowSettings] = useState(false);
  const [showNotification, setShowNotification] = useState(() => {
    const saved = localStorage.getItem("showNotification");
    return saved !== null ? JSON.parse(saved) : false;
  });
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [connectionStatus, setConnectionStatus] = useState("connecting");

  useEffect(() => {
    // Allow the user to add a custom css file
    fetch(`http://${hostname}:${port}/custom.css`)
      .then((response) => {
        if (response.ok) {
          // If the file exists, create a link element for the custom CSS
          const link = document.createElement("link");
          link.href = `http://${hostname}:${port}/custom.css`;
          link.type = "text/css";
          link.rel = "stylesheet";
          document.head.appendChild(link);
        }
      })
      .catch(console.error); // Handle the error appropriately

    socket.on("connect", () => {
      // Fetch data from the API when the client connects
      fetch(`http://${hostname}:${port}/service-properties`)
        .then((response) => response.json())
        .then((data: State) => {
          dispatch({ type: "SET_DATA", data });
          setServiceName(data.name);

          document.title = data.name; // Setting browser tab title
        });
      fetch(`http://${hostname}:${port}/web-settings`)
        .then((response) => response.json())
        .then((data: Record<string, WebSetting>) => setWebSettings(data));
      setConnectionStatus("connected");
    });
    socket.on("disconnect", () => {
      setConnectionStatus("disconnected");
      setTimeout(() => {
        // Only set "reconnecting" is the state is still "disconnected"
        // E.g. when the client has already reconnected
        setConnectionStatus((currentState) =>
          currentState === "disconnected" ? "reconnecting" : currentState,
        );
      }, 2000);
    });

    socket.on("notify", onNotify);
    socket.on("log", onLogMessage);

    return () => {
      socket.off("notify", onNotify);
      socket.off("log", onLogMessage);
    };
  }, []);

  // Persist isInstantUpdate and showNotification state changes to localStorage
  useEffect(() => {
    localStorage.setItem("isInstantUpdate", JSON.stringify(isInstantUpdate));
  }, [isInstantUpdate]);

  useEffect(() => {
    localStorage.setItem("showNotification", JSON.stringify(showNotification));
  }, [showNotification]);
  // Adding useCallback to prevent notify to change causing a re-render of all
  // components
  const addNotification = useCallback(
    (message: string, levelname: LevelName = "DEBUG") => {
      // Getting the current time in the required format
      const timeStamp = new Date().toISOString().substring(11, 19);
      // Adding an id to the notification to provide a way of removing it
      const id = Math.random();

      // Custom logic for notifications
      setNotifications((prevNotifications) => [
        { levelname, id, message, timeStamp },
        ...prevNotifications,
      ]);
    },
    [],
  );

  const removeNotificationById = (id: number) => {
    setNotifications((prevNotifications) =>
      prevNotifications.filter((n) => n.id !== id),
    );
  };

  const handleCloseSettings = () => setShowSettings(false);
  const handleShowSettings = () => setShowSettings(true);

  function onNotify(value: UpdateMessage) {
    // Extracting data from the notification
    const { full_access_path: fullAccessPath, value: newValue } = value.data;

    // Dispatching the update to the reducer
    dispatch({
      type: "UPDATE_ATTRIBUTE",
      fullAccessPath,
      newValue,
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
          <Navbar.Brand>{serviceName}</Navbar.Brand>
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
        <WebSettingsContext.Provider value={webSettings}>
          <GenericComponent
            attribute={state as SerializedObject}
            isInstantUpdate={isInstantUpdate}
            addNotification={addNotification}
          />
        </WebSettingsContext.Provider>
      </div>
      <ConnectionToast connectionStatus={connectionStatus} />
    </>
  );
};

export default App;
