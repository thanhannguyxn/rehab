import { Suspense, lazy, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { authAPI } from './utils/api';
import { ThemeProvider } from './context/ThemeContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { PatientCoachChat } from './components/PatientCoachChat';
import Layout from './components/Layout';
import { AppErrorBoundary } from './components/ErrorFallback';

// Lazy load all pages for Code Splitting
const Landing = lazy(() => import('./pages/Landing').then(module => ({ default: module.Landing })));
const LoginChoice = lazy(() => import('./pages/LoginChoice').then(module => ({ default: module.LoginChoice })));
const Login = lazy(() => import('./pages/Login').then(module => ({ default: module.Login })));
const ExercisePage = lazy(() => import('./pages/ExercisePage').then(module => ({ default: module.ExercisePage })));
const PatientHistory = lazy(() => import('./pages/PatientHistory').then(module => ({ default: module.PatientHistory })));
const DoctorDashboard = lazy(() => import('./pages/DoctorDashboard').then(module => ({ default: module.DoctorDashboard })));
const DoctorAssistantPage = lazy(() => import('./pages/DoctorAssistantPage').then(module => ({ default: module.DoctorAssistantPage })));
const PatientDetail = lazy(() => import('./pages/PatientDetail').then(module => ({ default: module.PatientDetail })));
const ScheduleSessionsPage = lazy(() => import('./pages/ScheduleSessionsPage').then(module => ({ default: module.ScheduleSessionsPage })));
const UserProfile = lazy(() => import('./pages/UserProfile').then(module => ({ default: module.UserProfile })));
const ExerciseManagement = lazy(() => import('./pages/ExerciseManagement').then(module => ({ default: module.ExerciseManagement })));
const PendingExerciseDetail = lazy(() => import('./pages/PendingExerciseDetail').then(module => ({ default: module.PendingExerciseDetail })));

const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-black transition-colors duration-200">
    <div className="text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-[#0284c7] mx-auto"></div>
      <p className="mt-4 text-xl text-gray-600 dark:text-gray-400">Đang tải...</p>
    </div>
  </div>
);

const PASSWORD_RULES = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{8,}$/;

function validatePassword(pw: string): string {
  if (pw.length < 8) return 'Mật khẩu phải có ít nhất 8 ký tự';
  if (!/[A-Z]/.test(pw)) return 'Mật khẩu phải có ít nhất 1 chữ in hoa';
  if (!/[0-9]/.test(pw)) return 'Mật khẩu phải có ít nhất 1 chữ số';
  if (!/[^a-zA-Z0-9]/.test(pw)) return 'Mật khẩu phải có ít nhất 1 ký tự đặc biệt (!@#$...)';
  return '';
}

// Popup hiện khi bệnh nhân đăng nhập lần đầu chưa đổi mật khẩu
function ChangePasswordPopup() {
  const { updateUser } = useAuth();
  const [newPassword, setNewPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const validationError = validatePassword(newPassword);
    if (validationError) { setError(validationError); return; }
    if (newPassword !== confirm) { setError('Mật khẩu xác nhận không khớp'); return; }
    setLoading(true);
    try {
      await authAPI.changePassword(newPassword);
      setSuccess(true);
      setTimeout(() => updateUser({ password_changed: true }), 1800);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Đổi mật khẩu thất bại. Vui lòng thử lại.');
      setLoading(false);
    }
  };

  const strengthChecks = [
    { label: 'Ít nhất 8 ký tự', ok: newPassword.length >= 8 },
    { label: 'Chữ in hoa (A-Z)', ok: /[A-Z]/.test(newPassword) },
    { label: 'Chữ số (0-9)', ok: /[0-9]/.test(newPassword) },
    { label: 'Ký tự đặc biệt (!@#$...)', ok: /[^a-zA-Z0-9]/.test(newPassword) },
  ];

  if (success) {
    return (
      <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md p-8 text-center">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Đổi mật khẩu thành công!</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">Đang chuyển vào hệ thống...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-amber-100 dark:bg-amber-900/30 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-6 h-6 text-amber-600 dark:text-amber-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Đặt mật khẩu mới</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Bạn cần đặt mật khẩu trước khi sử dụng hệ thống</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Mật khẩu mới</label>
            <input
              type="password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              placeholder="Nhập mật khẩu mới"
              autoFocus
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0369a1]"
            />
            {newPassword && (
              <ul className="mt-2 space-y-1">
                {strengthChecks.map(c => (
                  <li key={c.label} className={`flex items-center gap-1.5 text-xs ${c.ok ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'}`}>
                    <span>{c.ok ? '✓' : '○'}</span>{c.label}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Xác nhận mật khẩu</label>
            <input
              type="password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              placeholder="Nhập lại mật khẩu mới"
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0369a1]"
            />
          </div>
          {error && (
            <p className="text-red-600 dark:text-red-400 text-sm bg-red-50 dark:bg-red-900/20 px-4 py-2 rounded-lg">{error}</p>
          )}
          <button
            type="submit"
            disabled={loading || !PASSWORD_RULES.test(newPassword)}
            className="w-full bg-[#0369a1] hover:bg-[#0284c7] disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl transition"
          >
            {loading ? 'Đang lưu...' : 'Xác nhận'}
          </button>
        </form>
      </div>
    </div>
  );
}

function AppRoutes() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-[#0284c7] mx-auto"></div>
          <p className="mt-4 text-xl text-gray-600">Đang tải...</p>
        </div>
      </div>
    );
  }

  return (
    <Layout>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={user?.role === 'doctor' ? <Navigate to="/dashboard" replace /> : <Landing />} />
          <Route path="/login" element={<Navigate to="/login-choice" replace />} />
          <Route path="/login-choice" element={user ? <Navigate to="/" replace /> : <LoginChoice />} />
          <Route path="/login/:role" element={user ? <Navigate to="/" replace /> : <Login />} />

          {/* Dashboard Route - redirects based on role */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                {user?.role === 'patient' ? <Navigate to="/schedule-sessions" replace /> : <DoctorDashboard />}
              </ProtectedRoute>
            }
          />

          {/* Patient Routes */}
          <Route path="/exercise" element={<ProtectedRoute requiredRole="patient"><ExercisePage /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute requiredRole="patient"><PatientHistory /></ProtectedRoute>} />
          <Route path="/schedule-sessions" element={<ProtectedRoute requiredRole="patient"><ScheduleSessionsPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute requiredRole="patient"><UserProfile /></ProtectedRoute>} />

          {/* Doctor Routes */}
          <Route path="/doctor/patient/:patientId" element={<ProtectedRoute requiredRole="doctor"><PatientDetail /></ProtectedRoute>} />
          <Route path="/exercise-management" element={<ProtectedRoute requiredRole="doctor"><ExerciseManagement /></ProtectedRoute>} />
          <Route path="/pending-exercises/:id" element={<ProtectedRoute requiredRole="doctor"><PendingExerciseDetail /></ProtectedRoute>} />
          <Route path="/doctor/assistant" element={<ProtectedRoute requiredRole="doctor"><DoctorAssistantPage /></ProtectedRoute>} />

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>

      {user?.role === 'patient' && <PatientCoachChat />}

      {/* Popup đổi mật khẩu — hiện đè lên tất cả khi chưa đổi */}
      {user?.password_changed === false && <ChangePasswordPopup />}
    </Layout>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AppErrorBoundary>
            <AppRoutes />
          </AppErrorBoundary>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
