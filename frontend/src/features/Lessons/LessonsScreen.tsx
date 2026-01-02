/**
 * Lessons Screen - Помощь с уроками
 */

import { useState, useEffect } from 'react';
import { telegram } from '../../services/telegram';
import { getSubjects, type UserProfile } from '../../services/api';

interface Subject {
  id: string;
  name: string;
  icon: string;
  description: string;
  grade_range: [number, number];
}

interface LessonsScreenProps {
  user: UserProfile;
}

export function LessonsScreen({ user }: LessonsScreenProps) {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Загрузка списка предметов
    getSubjects()
      .then((data) => {
        setSubjects(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Ошибка загрузки предметов:', err);
        setIsLoading(false);
      });
  }, []);

  const handleSubjectClick = (subject: Subject) => {
    telegram.hapticFeedback('medium');
    telegram.showAlert(
      `Откроется интерактивный урок по предмету "${subject.name}". Функция в разработке! 🚀`
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4">
      {/* Заголовок */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-2">
          📚 Помощь с уроками
        </h1>
        <p className="text-[var(--tg-theme-hint-color)]">
          {user.grade ? `${user.grade} класс` : 'Выбери предмет для изучения'}
        </p>
      </div>

      {/* Список предметов */}
      <div className="grid grid-cols-2 gap-3">
        {subjects.map((subject) => {
          const isAvailable = user.grade
            ? user.grade >= subject.grade_range[0] && user.grade <= subject.grade_range[1]
            : true;

          return (
            <button
              key={subject.id}
              onClick={() => handleSubjectClick(subject)}
              disabled={!isAvailable}
              className={`p-4 rounded-2xl transition-all ${
                isAvailable
                  ? 'bg-[var(--tg-theme-button-color)]/10 hover:bg-[var(--tg-theme-button-color)]/20 active:scale-95'
                  : 'opacity-50 cursor-not-allowed'
              }`}
            >
              <div className="text-4xl mb-2">{subject.icon}</div>
              <div className="text-sm font-semibold text-[var(--tg-theme-text-color)] mb-1">
                {subject.name}
              </div>
              <div className="text-xs text-[var(--tg-theme-hint-color)]">
                {subject.description}
              </div>
              {!isAvailable && (
                <div className="text-xs text-red-500 mt-1">
                  Для {subject.grade_range[0]}-{subject.grade_range[1]} классов
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Быстрая помощь */}
      <div className="mt-6 p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl">
        <h3 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2">
          ⚡ Быстрая помощь
        </h3>
        <p className="text-sm text-[var(--tg-theme-hint-color)] mb-3">
          Отправь фото задачи или вопрос, и я помогу его решить!
        </p>
        <button
          onClick={() => {
            telegram.hapticFeedback('heavy');
            telegram.showAlert('Отправь боту фото или текст задачи в чате! 📸');
          }}
          className="w-full py-3 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-medium"
        >
          Задать вопрос AI 🤖
        </button>
      </div>
    </div>
  );
}
