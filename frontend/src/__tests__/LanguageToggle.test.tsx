import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LanguageToggle } from '../components/LanguageToggle';
import { useTranslation } from 'react-i18next';

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: vi.fn(),
}));

describe('LanguageToggle', () => {
  const changeLanguageMock = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "VI" when language is "vi"', () => {
    (useTranslation as any).mockReturnValue({
      i18n: {
        language: 'vi',
        changeLanguage: changeLanguageMock,
      },
    });

    render(<LanguageToggle />);
    const button = screen.getByRole('button');
    expect(button.textContent).toBe('VI');
  });

  it('renders "EN" when language is "en"', () => {
    (useTranslation as any).mockReturnValue({
      i18n: {
        language: 'en',
        changeLanguage: changeLanguageMock,
      },
    });

    render(<LanguageToggle />);
    const button = screen.getByRole('button');
    expect(button.textContent).toBe('EN');
  });

  it('toggles from "vi" to "en" on click', async () => {
    (useTranslation as any).mockReturnValue({
      i18n: {
        language: 'vi',
        changeLanguage: changeLanguageMock,
      },
    });

    render(<LanguageToggle />);
    const button = screen.getByRole('button');
    
    await userEvent.click(button);
    expect(changeLanguageMock).toHaveBeenCalledWith('en');
  });

  it('toggles from "en" to "vi" on click', async () => {
    (useTranslation as any).mockReturnValue({
      i18n: {
        language: 'en',
        changeLanguage: changeLanguageMock,
      },
    });

    render(<LanguageToggle />);
    const button = screen.getByRole('button');
    
    await userEvent.click(button);
    expect(changeLanguageMock).toHaveBeenCalledWith('vi');
  });
});
