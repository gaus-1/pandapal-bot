import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { registerServiceWorker, setupOfflineDetection } from './registerSW'

// Регистрируем Service Worker для PWA
registerServiceWorker()
setupOfflineDetection()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
