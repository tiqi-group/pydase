import { io } from "socket.io-client";
import { serializeDict, serializeList } from "./utils/serializationUtils";
import { SerializedObject } from "./types/SerializedObject";

const hostname =
  process.env.NODE_ENV === "development" ? `localhost` : window.location.hostname;
const port = process.env.NODE_ENV === "development" ? 8001 : window.location.port;

// Get the forwarded prefix from the global variable
export const forwardedPrefix: string =
  (window as any) /* eslint-disable-line @typescript-eslint/no-explicit-any */
    .__FORWARDED_PREFIX__ || "";
// Get the forwarded protocol type from the global variable
export const forwardedProto: string =
  (window as any) /* eslint-disable-line @typescript-eslint/no-explicit-any */
    .__FORWARDED_PROTO__ || "http";

export const authority = `${hostname}:${port}${forwardedPrefix}`;

const wsProto = forwardedProto === "http" ? "ws" : "wss";

const URL = `${wsProto}://${hostname}:${port}/`;
console.debug("Websocket: ", URL);
export const socket = io(URL, {
  path: `${forwardedPrefix}/ws/socket.io`,
  transports: ["websocket"],
});

export const updateValue = (
  serializedObject: SerializedObject,
  callback?: (ack: unknown) => void,
) => {
  if (callback) {
    socket.emit(
      "update_value",
      { access_path: serializedObject["full_access_path"], value: serializedObject },
      callback,
    );
  } else {
    socket.emit("update_value", {
      access_path: serializedObject["full_access_path"],
      value: serializedObject,
    });
  }
};

export const runMethod = (
  accessPath: string,
  args: unknown[] = [],
  kwargs: Record<string, unknown> = {},
  callback?: (ack: unknown) => void,
) => {
  const serializedArgs = serializeList(args);
  const serializedKwargs = serializeDict(kwargs);

  if (callback) {
    socket.emit(
      "trigger_method",
      { access_path: accessPath, args: serializedArgs, kwargs: serializedKwargs },
      callback,
    );
  } else {
    socket.emit("trigger_method", {
      access_path: accessPath,
      args: serializedArgs,
      kwargs: serializedKwargs,
    });
  }
};
