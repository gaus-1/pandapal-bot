/**
 * Генератор математических примеров для образовательной составляющей
 */

export const MathOperation = {
  ADDITION: '+',
  SUBTRACTION: '-',
  MULTIPLICATION: '×',
  DIVISION: '÷',
} as const;

export type MathOperation = typeof MathOperation[keyof typeof MathOperation];

export interface MathProblem {
  question: string;
  answer: number;
  operation: MathOperation;
  difficulty: number; // 1-5
}

export class MathProblems {
  /**
   * Генерация примера на сложение
   */
  static generateAddition(difficulty: number): MathProblem {
    const maxNum = difficulty * 10;
    const a = Math.floor(Math.random() * maxNum) + 1;
    const b = Math.floor(Math.random() * maxNum) + 1;

    return {
      question: `${a} + ${b}`,
      answer: a + b,
      operation: MathOperation.ADDITION,
      difficulty,
    };
  }

  /**
   * Генерация примера на вычитание
   */
  static generateSubtraction(difficulty: number): MathProblem {
    const maxNum = difficulty * 10;
    const a = Math.floor(Math.random() * maxNum) + 1;
    const b = Math.floor(Math.random() * a) + 1; // b всегда меньше a

    return {
      question: `${a} - ${b}`,
      answer: a - b,
      operation: MathOperation.SUBTRACTION,
      difficulty,
    };
  }

  /**
   * Генерация примера на умножение
   */
  static generateMultiplication(difficulty: number): MathProblem {
    const maxNum = Math.min(difficulty * 2, 10);
    const a = Math.floor(Math.random() * maxNum) + 1;
    const b = Math.floor(Math.random() * maxNum) + 1;

    return {
      question: `${a} × ${b}`,
      answer: a * b,
      operation: MathOperation.MULTIPLICATION,
      difficulty,
    };
  }

  /**
   * Генерация примера на деление
   */
  static generateDivision(difficulty: number): MathProblem {
    const maxNum = Math.min(difficulty * 2, 10);
    const b = Math.floor(Math.random() * maxNum) + 1;
    const answer = Math.floor(Math.random() * maxNum) + 1;
    const a = b * answer; // Гарантируем целое деление

    return {
      question: `${a} ÷ ${b}`,
      answer,
      operation: MathOperation.DIVISION,
      difficulty,
    };
  }

  /**
   * Генерация случайного примера по сложности
   */
  static generateRandom(difficulty: number): MathProblem {
    const operations = [
      this.generateAddition,
      this.generateSubtraction,
      this.generateMultiplication,
    ];

    // Деление добавляем только с 3 уровня сложности
    if (difficulty >= 3) {
      operations.push(this.generateDivision);
    }

    const randomOp = operations[Math.floor(Math.random() * operations.length)];
    return randomOp.call(this, difficulty);
  }

  /**
   * Генерация набора примеров для уровня
   */
  static generateSet(count: number, difficulty: number): MathProblem[] {
    const problems: MathProblem[] = [];

    for (let i = 0; i < count; i++) {
      problems.push(this.generateRandom(difficulty));
    }

    return problems;
  }

  /**
   * Проверка ответа
   */
  static checkAnswer(problem: MathProblem, userAnswer: number): boolean {
    return problem.answer === userAnswer;
  }

  /**
   * Форматирование примера для отображения
   */
  static formatProblem(problem: MathProblem): string {
    return problem.question;
  }
}
