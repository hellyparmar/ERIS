import { StrictMode } from 'react'
import './styles/globals.css';
import './styles/design-system.css';
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Theme initialization — must run before React renders
const _savedTheme = localStorage.getItem('rdios-theme') || 'dark';
document.documentElement.setAttribute('data-theme', _savedTheme);

console.log('MAIN JSX START');
try {
  const root = createRoot(document.getElementById('root'));
  root.render(
    <StrictMode>
      <App />
    </StrictMode>
  );
  console.log('MAIN JSX RENDER REQUESTED');
} catch (err) {
  console.error('MAIN JSX RENDER ERROR', err);
  throw err;
}
