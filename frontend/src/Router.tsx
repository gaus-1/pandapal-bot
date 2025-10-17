/**
 * Роутер для приложения PandaPal.
 * Обрабатывает маршруты для главной страницы, документации и игры.
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import App from './App';
import { Documentation } from './pages/Documentation';

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

        {/* Редирект всех неизвестных маршрутов на главную */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
});

AppRouter.displayName = 'AppRouter';
