import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Log para debugging
console.log('=== BolsaV2 Frontend Starting ===')
console.log('React version:', React.version)
console.log('Root element:', document.getElementById('root'))

// Suprimir errores de extensiones del navegador
const originalError = console.error;
console.error = (...args) => {
  if (
    typeof args[0] === 'string' &&
    args[0].includes('message channel closed')
  ) {
    return;
  }
  originalError.apply(console, args);
};

try {
  const rootElement = document.getElementById('root')
  if (!rootElement) {
    throw new Error('Root element not found')
  }
  
  console.log('Creating React root...')
  const root = ReactDOM.createRoot(rootElement)
  
  console.log('Rendering App...')
  root.render(
    <App />
  )
  
  console.log('=== BolsaV2 Frontend Started Successfully ===')
} catch (error) {
  console.error('=== Fatal Error Starting Frontend ===', error)
  document.body.innerHTML = `
    <div style="padding: 20px; color: red; font-family: monospace;">
      <h1>Error Loading BolsaV2</h1>
      <pre>${error}</pre>
    </div>
  `
}
