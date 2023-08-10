import { io } from 'socket.io-client';

export const hostname =
  process.env.NODE_ENV === 'development' ? `localhost` : window.location.hostname;
export const port =
  process.env.NODE_ENV === 'development' ? 8001 : window.location.port;
const URL = `ws://${hostname}:${port}/`;
console.debug('Websocket: ', URL);

export const socket = io(URL, { path: '/ws/socket.io', transports: ['websocket'] });

export const emit_update = (
  name: string,
  parentPath: string,
  value: unknown,
  callback?: (ack: unknown) => void
) => {
  if (callback) {
    socket.emit('frontend_update', { name, parent_path: parentPath, value }, callback);
  } else {
    socket.emit('frontend_update', { name, parent_path: parentPath, value });
  }
};
