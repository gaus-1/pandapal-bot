import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { registerServiceWorker, setupOfflineDetection } from './registerSW'

// Подавляем ошибки Telegram WebView (это нормальные предупреждения)
if (typeof window !== 'undefined') {
  const originalError = console.error;
  console.error = (...args: any[]) => {
    const message = args[0]?.toString() || '';
    // Игнорируем известные предупреждения Telegram WebView
    if (
      message.includes('SW registration failed') ||
      message.includes('no controller') ||
      message.includes('peer changed') ||
      message.includes('device-orientation') ||
      message.includes('Unrecognized feature')
    ) {
      return; // Подавляем эти ошибки
    }
    originalError.apply(console, args);
  };
}

// Регистрируем Service Worker для PWA
registerServiceWorker()
setupOfflineDetection()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
