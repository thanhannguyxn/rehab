import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ThemeToggle } from './ThemeToggle';
import { useState } from 'react';
import { LanguageToggle } from './LanguageToggle';
import { useTranslation } from 'react-i18next';

export const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const { t, i18n } = useTranslation();

  // Helper function to check if link is active
  const isActive = (path: string) => {
    return location.pathname === path;
  };

  // Helper function to get link classes
  const getLinkClasses = (path: string) => {
    const baseClasses = "transition font-medium";
    if (isActive(path)) {
      return `${baseClasses} text-[#0369a1] dark:text-blue-600 font-semibold`;
    }
    return `${baseClasses} text-gray-500 dark:text-gray-400 hover:text-[#0369a1]`;
  };

  return (
    <nav className="bg-white/95 dark:bg-black/95 backdrop-blur-sm border-b border-gray-200 dark:border-gray-800 sticky top-0 z-50 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3">
            <span className="text-2xl font-bold text-[#0369a1] dark:text-blue-600">
              Rehab AI
            </span>
          </Link>
          
          {/* Navigation Links */}
          <div className="hidden md:flex space-x-8 items-center">
            {user && user.role === 'patient' && (
              <>
                <Link to="/" className={getLinkClasses('/')}>
                  {t("navbar.home")}
                </Link>
                <Link to="/exercise" className={getLinkClasses('/exercise')}>
                  {t("navbar.exercise")}
                </Link>
                <Link to="/schedule-sessions" className={getLinkClasses('/schedule-sessions')}>
                  {t("navbar.scheduleSession")}
                </Link>
                <Link to="/history" className={getLinkClasses('/history')}>
                  {t("navbar.history")}
                </Link>
              </>
            )}
            
            {user && user.role === 'doctor' && (
              <>
                <Link to="/dashboard" className={getLinkClasses('/dashboard')}>
                  {t("navbar.doctorDashboard", i18n.language === 'vi' ? "Bảng Điều Khiển" : "Dashboard")}
                </Link>
                <Link to="/doctor/assistant" className={getLinkClasses('/doctor/assistant')}>
                  {t("navbar.aiAssistant", i18n.language === 'vi' ? "Trợ Lý AI" : "AI Assistant")}
                </Link>
              </>
            )}
          </div>

          {/* Right Side: Theme Toggle + User Actions */}
          <div className="flex items-center gap-3">
            <LanguageToggle />
            <ThemeToggle />
            
            {user ? (
              <div 
                className="relative"
                onMouseEnter={() => setShowUserDropdown(true)}
                onMouseLeave={() => setShowUserDropdown(false)}
              >
                {/* Avatar Button */}
                <button className="flex items-center gap-3 hover:opacity-80 transition">
                  <div className="w-10 h-10 rounded-full bg-[#0369a1] flex items-center justify-center text-white font-semibold shadow-lg">
                    {user.full_name.charAt(0).toUpperCase()}
                  </div>
                </button>

                {/* Dropdown Menu */}
                {showUserDropdown && (
                  <div className="absolute top-full right-0 pt-2">
                    <div className="w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-hidden">
                      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                        <p className="text-sm text-gray-500 dark:text-gray-400">{t("navbar.greeting")},</p>
                        <p className="text-base font-semibold text-gray-900 dark:text-white truncate">{user.full_name}</p>
                      </div>
                      {user.role === 'patient' && (
                        <button
                          onClick={() => {
                            navigate('/profile');
                            setShowUserDropdown(false);
                          }}
                          className="w-full text-left px-4 py-3 text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-gray-700 hover:text-[#0284c7] dark:hover:text-blue-600 transition font-medium flex items-center gap-2"
                        >
                          {t("navbar.profile")}
                        </button>
                      )}
                      <button
                        onClick={() => {
                          logout();
                          navigate('/');
                          setShowUserDropdown(false);
                        }}
                        className="w-full text-left px-4 py-3 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition font-medium flex items-center gap-2 border-t border-gray-100 dark:border-gray-700"
                      >
                        {t("navbar.logout")}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <Link
                to="/login-choice"
                className="bg-[#0369a1] hover:bg-[#0284c7] text-white px-6 py-2.5 rounded-lg font-semibold transition shadow-lg shadow-[#0369a1]/30"
              >
                {t("navbar.login")}
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
