import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ThemeProvider, useTheme } from '../context/ThemeContext';

const TestComponent = () => {
  const { isDarkMode, toggleDarkMode } = useTheme();
  return (
    <div>
      <span data-testid="theme-status">{isDarkMode ? 'Dark' : 'Light'}</span>
      <button data-testid="toggle-btn" onClick={toggleDarkMode}>
        Toggle
      </button>
    </div>
  );
};

describe('ThemeContext', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = ''; // Reset classes
  });

  it('provides default dark mode if no local storage is set', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme-status').textContent).toBe('Dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(localStorage.getItem('theme')).toBe('dark');
  });

  it('respects initial local storage mode (light)', () => {
    localStorage.setItem('theme', 'light');

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme-status').textContent).toBe('Light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('toggles mode when toggleDarkMode is called', async () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    const toggleBtn = screen.getByTestId('toggle-btn');
    
    // Default is dark
    expect(screen.getByTestId('theme-status').textContent).toBe('Dark');

    // Click to toggle
    await userEvent.click(toggleBtn);

    expect(screen.getByTestId('theme-status').textContent).toBe('Light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(localStorage.getItem('theme')).toBe('light');

    // Click again to toggle back
    await userEvent.click(toggleBtn);
    expect(screen.getByTestId('theme-status').textContent).toBe('Dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(localStorage.getItem('theme')).toBe('dark');
  });

  it('throws an error if useTheme is used outside of ThemeProvider', () => {
    // Hide console.error to avoid spamming the test output
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => render(<TestComponent />)).toThrow(
      'useTheme must be used within a ThemeProvider'
    );
    
    consoleSpy.mockRestore();
  });
});
