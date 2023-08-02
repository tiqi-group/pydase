import App from './App';
import { createRoot } from 'react-dom/client';

// Render the App component into the #root div
const container = document.getElementById('root');
const root = createRoot(container);
root.render(<App />);
