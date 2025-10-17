import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './styles/accessibility.css'
import { AppRouter } from './Router.tsx'

// 🛡️ КРИТИЧЕСКИ ВАЖНО: Инициализация защиты от clickjacking
// Защищает детей от встраивания сайта в вредоносные фреймы
import { initClickjackingProtection } from './security/clickjacking'

// 📊 Инициализация мониторинга производительности
import { initPerformanceMonitoring } from './monitoring/performanceMonitoring'

// 🚀 Предзагрузка критических ресурсов
import { preloadCriticalAssets } from './utils/performance'

// Инициализируем защиту ДО рендера React приложения
initClickjackingProtection()

// Инициализируем мониторинг производительности
initPerformanceMonitoring()

// Предзагружаем критические ресурсы
preloadCriticalAssets()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppRouter />
  </StrictMode>,
)
