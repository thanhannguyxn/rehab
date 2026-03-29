import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ThemeToggle } from '../components/ThemeToggle';
import { useTheme } from '../context/ThemeContext';

// Mock the hook
vi.mock('../context/ThemeContext', () => ({
  useTheme: vi.fn(),
}));

describe('ThemeToggle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dark mode (moon icon) when isDarkMode is false', () => {
    (useTheme as any).mockReturnValue({
      isDarkMode: false,
      toggleDarkMode: vi.fn(),
    });

    render(<ThemeToggle />);
    const button = screen.getByRole('button', { name: 'Switch to Dark Mode' });
    expect(button).toBeInTheDocument();
  });

  it('renders light mode (sun icon) when isDarkMode is true', () => {
    (useTheme as any).mockReturnValue({
      isDarkMode: true,
      toggleDarkMode: vi.fn(),
    });

    render(<ThemeToggle />);
    const button = screen.getByRole('button', { name: 'Switch to Light Mode' });
    expect(button).toBeInTheDocument();
  });

  it('calls toggleDarkMode on click', async () => {
    const toggleMock = vi.fn();
    (useTheme as any).mockReturnValue({
      isDarkMode: false,
      toggleDarkMode: toggleMock,
    });

    render(<ThemeToggle />);
    const button = screen.getByRole('button', { name: 'Switch to Dark Mode' });
    
    await userEvent.click(button);
    expect(toggleMock).toHaveBeenCalledTimes(1);
  });
});
