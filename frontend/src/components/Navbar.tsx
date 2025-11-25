import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ThemeToggle } from './ThemeToggle';
import { useState } from 'react';

export const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  // Helper function to check if link is active
  const isActive = (path: string) => {
    return location.pathname === path;
  };

  // Helper function to get link classes
  const getLinkClasses = (path: string) => {
    const baseClasses = "transition font-medium";
    if (isActive(path)) {
      return `${baseClasses} text-teal-500 dark:text-teal-400 font-semibold`;
    }
    return `${baseClasses} text-gray-500 dark:text-gray-400 hover:text-teal-500`;
  };

  return (
    <nav className="bg-white/95 dark:bg-black/95 backdrop-blur-sm border-b border-gray-200 dark:border-gray-800 sticky top-0 z-50 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3">
            <span className="text-2xl font-bold bg-gradient-to-r from-teal-500 via-cyan-500 to-blue-500 dark:from-teal-400 dark:via-cyan-400 dark:to-blue-400 bg-clip-text text-transparent">
              Rehab AI
            </span>
          </Link>
          
          {/* Navigation Links */}
          <div className="hidden md:flex space-x-8 items-center">
            {user && user.role === 'patient' && (
              <>
                <Link to="/" className={getLinkClasses('/')}>
                  Trang Chủ
                </Link>
                <Link to="/exercise" className={getLinkClasses('/exercise')}>
                  Bài Tập
                </Link>
                <Link to="/history" className={getLinkClasses('/history')}>
                  Lịch Sử
                </Link>
              </>
            )}
            
            {user && user.role === 'doctor' && (
              <Link to="/dashboard" className={getLinkClasses('/dashboard')}>
                Dashboard
              </Link>
            )}
          </div>

          {/* Right Side: Theme Toggle + User Actions */}
          <div className="flex items-center gap-3">
            <ThemeToggle />
            
            {user ? (
              <div 
                className="relative"
                onMouseEnter={() => setShowUserDropdown(true)}
                onMouseLeave={() => setShowUserDropdown(false)}
              >
                {/* Avatar Button */}
                <button className="flex items-center gap-3 hover:opacity-80 transition">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center text-white font-semibold shadow-lg">
                    {user.full_name.charAt(0).toUpperCase()}
                  </div>
                </button>

                {/* Dropdown Menu */}
                {showUserDropdown && (
                  <div className="absolute top-full right-0 pt-2">
                    <div className="w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-hidden">
                      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                        <p className="text-sm text-gray-500 dark:text-gray-400">Xin chào,</p>
                        <p className="text-base font-semibold text-gray-900 dark:text-white truncate">{user.full_name}</p>
                      </div>
                      {user.role === 'patient' && (
                        <button
                          onClick={() => {
                            navigate('/profile');
                            setShowUserDropdown(false);
                          }}
                          className="w-full text-left px-4 py-3 text-gray-700 dark:text-gray-300 hover:bg-teal-50 dark:hover:bg-gray-700 hover:text-teal-600 dark:hover:text-teal-400 transition font-medium flex items-center gap-2"
                        >
                          Thông Tin Cá Nhân
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
                        Đăng Xuất
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <Link
                to="/login-choice"
                className="bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600 text-white px-6 py-2.5 rounded-lg font-semibold transition shadow-lg shadow-teal-500/30"
              >
                Đăng Nhập
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
