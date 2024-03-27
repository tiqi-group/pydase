import { io } from 'socket.io-client';
import { SerializedValue } from './components/GenericComponent';
import { serializeDict, serializeList } from './utils/serializationUtils';

export const hostname =
  process.env.NODE_ENV === 'development' ? `localhost` : window.location.hostname;
export const port =
  process.env.NODE_ENV === 'development' ? 8001 : window.location.port;
const URL = `ws://${hostname}:${port}/`;
console.debug('Websocket: ', URL);

export const socket = io(URL, { path: '/ws/socket.io', transports: ['websocket'] });

export const updateValue = (
  serializedObject: SerializedValue,
  callback?: (ack: unknown) => void
) => {
  if (callback) {
    socket.emit('update_value', { value: serializedObject }, callback);
  } else {
    socket.emit('update_value', { value: serializedObject });
  }
};

export const runMethod = (
  accessPath: string,
  args: unknown[] = [],
  kwargs: Record<string, unknown> = {},
  callback?: (ack: unknown) => void
) => {
  const serializedArgs = serializeList(args);
  const serializedKwargs = serializeDict(kwargs);

  if (callback) {
    socket.emit(
      'trigger_method',
      { access_path: accessPath, args: serializedArgs, kwargs: serializedKwargs },
      callback
    );
  } else {
    socket.emit('trigger_method', {
      access_path: accessPath,
      args: serializedArgs,
      kwargs: serializedKwargs
    });
  }
};
