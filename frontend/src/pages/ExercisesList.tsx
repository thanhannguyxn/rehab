import { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { exerciseAPI } from '../utils/api';
import type { Exercise } from '../types';

const ExercisesList: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const location = useLocation();
  const pathname = location.pathname;
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await exerciseAPI.getExercises();
        setExercises(data.exercises || []);
      } catch (e) {
        console.error('Failed to load exercises', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-teal-600 mx-auto"></div>
          <p className="mt-4 text-xl text-gray-600">Đang tải...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-teal-50">
      {/* Navbar (match Landing header) */}
      <nav className="bg-white shadow-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <div className="bg-teal-600 text-white p-2 rounded-lg">
                <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                </svg>
              </div>
              <span className="text-xl font-bold text-gray-800">Rehab System</span>
            </div>

            <div className="hidden md:flex space-x-8 text-base">
              <Link
                to="/"
                className={`font-semibold ${pathname === '/' ? 'text-teal-600' : 'text-gray-600 hover:text-teal-700'}`}
              >
                Trang Chủ
              </Link>
              {user && (
                <>
                  <Link
                    to="/exercises"
                    className={`${pathname === '/exercises' || pathname.startsWith('/exercise') ? 'text-teal-600' : 'text-gray-600 hover:text-teal-600'} font-semibold`}
                  >
                    Bài Tập
                  </Link>
                  <Link
                    to="/history"
                    className={`${pathname.startsWith('/history') ? 'text-teal-600' : 'text-gray-600 hover:text-teal-600'} font-semibold`}
                  >
                    Lịch Sử
                  </Link>
                </>
              )}
            </div>

            {user ? (
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-base text-gray-600">Xin chào,</p>
                  <p className="text-lg font-bold text-teal-600">{user.full_name}</p>
                </div>
                <button
                  onClick={() => { logout(); navigate('/'); }}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold text-base transition"
                >
                  Đăng Xuất
                </button>
              </div>
            ) : (
              <Link
                to="/login-choice"
                className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-3 rounded-lg font-semibold text-base transition shadow-lg"
              >
                Đăng Nhập
              </Link>
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 py-12 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">Danh sách bài tập</h1>
        <p className="text-xl text-gray-600 mb-6 max-w-3xl mx-auto">Chọn bài tập phù hợp và bắt đầu buổi tập với hướng dẫn trực quan.</p>
      </section>

      <div className="max-w-7xl mx-auto px-6 pb-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {exercises.map((ex) => (
            <button
              key={ex.id}
              onClick={() => navigate(`/exercise/${ex.id}`)}
              className="text-left bg-white rounded-2xl p-6 shadow-lg transform transition duration-300 hover:scale-105 hover:shadow-2xl flex flex-col"
            >
              <div className="w-full h-40 mb-4 overflow-hidden rounded-xl">
                <img
                  src={(ex as any).image_url ? (ex as any).image_url : `https://via.placeholder.com/800x450.png?text=${encodeURIComponent(ex.name)}`}
                  alt={`${ex.name} illustration`}
                  className="w-full h-full object-cover"
                />
              </div>

              <div className="flex-1">
                <h3 className="text-2xl font-bold mb-2 text-gray-800">{ex.name}</h3>
                <p className="text-gray-600 mb-4 line-clamp-3">{ex.description}</p>
              </div>
              <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
                <span>⏱️ {ex.id === 'squat' ? '5-10 phút' : '5 phút'}</span>
                <span>🔁 {ex.target_reps} lần</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12 py-8">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-gray-600 text-lg">© 2025 AI-Powered Home Rehabilitation System</p>
          <p className="text-gray-500 mt-1">Được phát triển để hỗ trợ người cao tuổi</p>
        </div>
      </footer>
    </div>
  );
};

export default ExercisesList;
