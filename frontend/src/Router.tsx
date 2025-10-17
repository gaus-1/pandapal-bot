/**
 * Роутер для приложения PandaPal.
 * Обрабатывает маршруты для главной страницы, документации и игры.
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import App from './App';
import { Documentation } from './pages/Documentation';
// import GameApp from './game/GameApp'; // Будет добавлено при разработке игры

export const AppRouter: React.FC = React.memo(() => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Главная страница */}
        <Route path="/" element={<App />} />

        {/* Документация с переключением языков */}
        <Route path="/docs" element={<Documentation />} />

        {/* Игра (будет добавлено позже) */}
        {/* <Route path="/game" element={<GameApp />} /> */}

        {/* Редирект всех неизвестных маршрутов на главную */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
});

AppRouter.displayName = 'AppRouter';
