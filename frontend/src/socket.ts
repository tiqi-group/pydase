import { io } from 'socket.io-client';

export const hostname =
  process.env.NODE_ENV === 'development' ? `localhost` : window.location.hostname;
export const port =
  process.env.NODE_ENV === 'development' ? 8001 : window.location.port;
const URL = `ws://${hostname}:${port}/`;
console.debug('Websocket: ', URL);

export const socket = io(URL, { path: '/ws/socket.io', transports: ['websocket'] });
