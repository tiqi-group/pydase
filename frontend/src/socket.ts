import { io } from 'socket.io-client';

const URL = 'ws://localhost:8001/';
// process.env.NODE_ENV === 'production' ? undefined : 'ws://localhost:8001/ws';

export const socket = io(URL, { path: '/ws/socket.io', transports: ['websocket'] });
