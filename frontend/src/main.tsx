import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { AppRouter } from './Router.tsx'

// 🛡️ КРИТИЧЕСКИ ВАЖНО: Инициализация защиты от clickjacking
// Защищает детей от встраивания сайта в вредоносные фреймы
import { initClickjackingProtection } from './security/clickjacking'

// Инициализируем защиту ДО рендера React приложения
initClickjackingProtection()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppRouter />
  </StrictMode>,
)
