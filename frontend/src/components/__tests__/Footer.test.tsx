/**
 * Тесты для компонента Footer
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Footer } from '../Footer';

describe('Footer Component', () => {
  it('рендерится без ошибок', () => {
    const { container } = render(<Footer />);
    expect(container).toBeInTheDocument();
  });

  it('имеет правильную семантическую структуру footer', () => {
    render(<Footer />);
    const footer = screen.getByRole('contentinfo');
    expect(footer).toBeInTheDocument();
  });

  it('содержит копирайт', () => {
    render(<Footer />);
    const currentYear = new Date().getFullYear();
    expect(screen.getByText(new RegExp(currentYear.toString()))).toBeInTheDocument();
  });

  it('содержит название проекта', () => {
    render(<Footer />);
    const matches = screen.getAllByText(/PandaPal/i);
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(matches[0]).toBeInTheDocument();
  });
});
