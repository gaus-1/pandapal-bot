import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { registerServiceWorker, setupOfflineDetection } from './registerSW'

// Подавляем ошибки Telegram WebView (это нормальные предупреждения)
if (typeof window !== 'undefined') {
  const originalError = console.error;
  const originalWarn = console.warn;

  console.error = (...args: any[]) => {
    const message = args.join(' ') || '';
    // Игнорируем известные предупреждения Telegram WebView и Service Worker
    if (
      message.includes('[SW]') ||
      message.includes('SW registration failed') ||
      message.includes('no controller') ||
      message.includes('no windows left') ||
      message.includes('it is not a window') ||
      message.includes('peer changed') ||
      message.includes('device-orientation') ||
      message.includes('Unrecognized feature') ||
      message.includes('MP-MTPROTO') ||
      message.includes('Service Worker')
    ) {
      return; // Подавляем эти ошибки
    }
    originalError.apply(console, args);
  };

  console.warn = (...args: any[]) => {
    const message = args.join(' ') || '';
    // Игнорируем известные предупреждения Telegram WebView
    if (
      message.includes('[SW]') ||
      message.includes('device-orientation') ||
      message.includes('Unrecognized feature') ||
      message.includes('Service Worker')
    ) {
      return; // Подавляем эти предупреждения
    }
    originalWarn.apply(console, args);
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
