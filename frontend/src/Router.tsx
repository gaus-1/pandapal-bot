/**
 * Роутер для приложения PandaPal.
 * Обрабатывает маршруты для главной страницы, документации и игры.
 */

import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import App from './App';
import { Documentation } from './pages/Documentation';
import ApiDocs from './pages/ApiDocs';

// Ленивая загрузка игры для оптимизации
const PandaPalGo = lazy(() => import('./game/PandaPalGo'));

export const AppRouter: React.FC = React.memo(() => {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        {/* Главная страница */}
        <Route path="/" element={<App />} />

        {/* Документация с переключением языков */}
        <Route path="/docs" element={<Documentation />} />

        {/* API документация */}
        <Route path="/api-docs" element={<ApiDocs />} />

        {/* Игра PandaPal Go */}
        <Route
          path="/play"
          element={
            <Suspense
              fallback={
                <div className="flex items-center justify-center min-h-screen bg-gradient-to-b from-blue-50 to-purple-50">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-xl text-gray-600">Загрузка игры...</p>
                  </div>
                </div>
              }
            >
              <PandaPalGo />
            </Suspense>
          }
        />

        {/* Редирект всех неизвестных маршрутов на главную */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
});

AppRouter.displayName = 'AppRouter';
