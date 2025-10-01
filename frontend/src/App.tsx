import './index.css'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 text-gray-900">
      {/* Header */}
      <header className="max-w-6xl mx-auto px-4 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src="/logo.png" alt="PandaPal" className="w-12 h-12 rounded-full shadow-md" />
          <span className="font-display text-2xl font-bold">PandaPal</span>
        </div>
        <nav className="hidden md:flex items-center gap-6">
          <a href="#parents" className="text-sm hover:text-pink transition">Для родителей</a>
          <a href="#teachers" className="text-sm hover:text-pink transition">Для учителей</a>
          <a 
            href="https://t.me/PandaPalBot" 
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2 rounded-full bg-sky text-white hover:shadow-lg transition-shadow"
          >
            Начать
          </a>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="max-w-6xl mx-auto px-4">
        <section className="py-12 md:py-20 text-center">
          <h1 className="font-display text-4xl md:text-6xl font-bold leading-tight">
            Безопасный ИИ-друг<br />для твоего ребенка
          </h1>
          <p className="mt-6 text-lg md:text-xl text-gray-700 max-w-2xl mx-auto">
            Адаптивное, игровое и безопасное обучение для 1–9 классов
          </p>
          <div className="mt-8">
            <a 
              href="https://t.me/PandaPalBot" 
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-8 py-4 rounded-full bg-pink text-gray-900 font-semibold shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
            >
              Начать использовать
            </a>
          </div>
        </section>

        {/* Features */}
        <section className="grid md:grid-cols-3 gap-6 py-12">
          {[
            { title: 'Адаптивность', text: 'Контент подстраивается под возраст и уровень ребенка.' },
            { title: 'Безопасность', text: 'Фильтрация контента и защита персональных данных.' },
            { title: 'Игра', text: 'Геймификация и система достижений для мотивации.' },
          ].map((feature) => (
            <div 
              key={feature.title} 
              className="rounded-2xl bg-white/80 backdrop-blur p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <h3 className="font-display text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-700">{feature.text}</p>
            </div>
          ))}
        </section>

        {/* For Parents */}
        <section id="parents" className="py-12 md:py-16">
          <div className="rounded-2xl bg-white/60 backdrop-blur p-8 md:p-12">
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">Для родителей</h2>
            <p className="text-lg text-gray-700 max-w-3xl">
              Прозрачная аналитика прогресса ребенка, гибкие настройки безопасности и контроль времени обучения. 
              Вы всегда будете в курсе успехов и интересов вашего ребенка.
            </p>
          </div>
        </section>

        {/* For Teachers */}
        <section id="teachers" className="py-12 md:py-16">
          <div className="rounded-2xl bg-white/60 backdrop-blur p-8 md:p-12">
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">Для учителей</h2>
            <p className="text-lg text-gray-700 max-w-3xl">
              Инструменты для генерации индивидуальных заданий, отслеживания вовлеченности класса и автоматической проверки работ. 
              Экономьте время на рутине и фокусируйтесь на творчестве.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="max-w-6xl mx-auto px-4 py-12 text-center border-t border-gray-200/50 mt-16">
        <div className="flex items-center justify-center gap-3 mb-4">
          <img src="/logo.png" alt="PandaPal" className="w-8 h-8 rounded-full" />
          <span className="font-display text-lg font-semibold">PandaPal</span>
        </div>
        <p className="text-sm text-gray-600">
          © {new Date().getFullYear()} PandaPal. Все права защищены.
        </p>
      </footer>
    </div>
  )
}

export default App
