import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/design-system.css'
import './styles/globals.css'
import './index.css'
import App from './App.jsx'

// Theme initialization — must run before React renders
const _savedTheme = localStorage.getItem('theme') || 'dark';
document.documentElement.setAttribute('data-theme', _savedTheme);

console.log('MAIN JSX START');
const root = createRoot(document.getElementById('root'));
root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
console.log('MAIN JSX RENDER REQUESTED');
