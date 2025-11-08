import { useState, FormEvent } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Login = () => {
  const { role } = useParams<{ role: 'patient' | 'doctor' }>();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const isDoctor = role === 'doctor';
  const roleText = isDoctor ? 'Bác Sĩ' : 'Bệnh Nhân';
  const roleColor = isDoctor ? 'green' : 'teal';
  const defaultAccount = isDoctor 
    ? { username: 'doctor1', password: 'doctor123' }
    : { username: 'patient1', password: 'patient123' };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(username, password);
      navigate(isDoctor ? '/dashboard' : '/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Đăng nhập thất bại. Vui lòng thử lại.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 to-teal-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl flex flex-col md:flex-row overflow-hidden">
        {/* Left: branding / role info (visible on all sizes but becomes a left column on md+) */}
        <div className={`md:w-1/2 p-6 flex flex-col items-center justify-center bg-${roleColor}-50`}>
          <div className={`bg-${roleColor}-100 w-20 h-20 rounded-full flex items-center justify-center mb-4`}>
            {isDoctor ? (
              <svg className={`w-12 h-12 text-${roleColor}-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            ) : (
              <svg className={`w-12 h-12 text-${roleColor}-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            )}
          </div>

          <h1 className={`text-2xl md:text-3xl font-bold text-${roleColor}-600 mb-2 text-center`}>
            Đăng Nhập {roleText}
          </h1>
          <p className="text-base md:text-lg text-gray-700 text-center mb-4">Hệ Thống Phục Hồi Chức Năng</p>

          <div className="w-full max-w-sm mt-3">
            <p className="text-base text-gray-700 mb-2 font-semibold">Tài khoản mẫu:</p>
            <div className="space-y-1 text-sm text-gray-700">
              <p className={`${isDoctor ? 'font-semibold' : ''}`}>
                {isDoctor ? '✅ ' : '🏥 '}
                Bác sĩ: <span className="font-mono bg-white px-2 py-0.5 rounded">doctor1 / doctor123</span>
              </p>
              <p className={`${!isDoctor ? 'font-semibold' : ''}`}>
                {!isDoctor ? '✅ ' : '👤 '}
                Bệnh nhân: <span className="font-mono bg-white px-2 py-0.5 rounded">patient1 / patient123</span>
              </p>
            </div>
          </div>

          <div className="mt-4">
            <Link to="/login-choice" className="text-sm text-gray-700 hover:text-${roleColor}-700 transition">
              ← Đăng nhập loại tài khoản khác
            </Link>
          </div>
        </div>

        {/* Right: form */}
        <div className="md:w-1/2 p-6 flex items-center justify-center">
          <div className="w-full max-w-sm">
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-100 border-2 border-red-400 text-red-700 px-6 py-4 rounded-lg text-lg">
                  {error}
                </div>
              )}

              <div>
                <label htmlFor="username" className="block text-base font-semibold text-gray-700 mb-2">
                  Tên đăng nhập
                </label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className={`w-full px-4 py-3 text-base border-2 border-gray-300 rounded-lg focus:border-${roleColor}-500 focus:ring-2 focus:ring-${roleColor}-200 transition`}
                  placeholder="Nhập tên đăng nhập"
                  required
                  autoFocus
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-base font-semibold text-gray-700 mb-2">
                  Mật khẩu
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`w-full px-4 py-3 text-base border-2 border-gray-300 rounded-lg focus:border-${roleColor}-500 focus:ring-2 focus:ring-${roleColor}-200 transition`}
                  placeholder="Nhập mật khẩu"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className={`w-full bg-${roleColor}-600 hover:bg-${roleColor}-700 text-white font-bold py-3 px-4 rounded-lg text-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg`}
              >
                {isLoading ? 'Đang đăng nhập...' : 'Đăng Nhập'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
