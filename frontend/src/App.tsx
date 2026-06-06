import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
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

// Fallback Loading Component
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-black transition-colors duration-200">
    <div className="text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-[#0284c7] mx-auto"></div>
      <p className="mt-4 text-xl text-gray-600 dark:text-gray-400">Đang tải...</p>
    </div>
  </div>
);

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
          <Route
            path="/exercise"
            element={
              <ProtectedRoute requiredRole="patient">
                <ExercisePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute requiredRole="patient">
                <PatientHistory />
              </ProtectedRoute>
            }
          />
          <Route
            path="/schedule-sessions"
            element={
              <ProtectedRoute requiredRole="patient">
                <ScheduleSessionsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute requiredRole="patient">
                <UserProfile />
              </ProtectedRoute>
            }
          />

          {/* Doctor Routes */}
          <Route
            path="/doctor/patient/:patientId"
            element={
              <ProtectedRoute requiredRole="doctor">
                <PatientDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/exercise-management"
            element={
              <ProtectedRoute requiredRole="doctor">
                <ExerciseManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="/pending-exercises/:id"
            element={
              <ProtectedRoute requiredRole="doctor">
                <PendingExerciseDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/doctor/assistant"
            element={
              <ProtectedRoute requiredRole="doctor">
                <DoctorAssistantPage />
              </ProtectedRoute>
            }
          />

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>

      {user?.role === 'patient' && <PatientCoachChat />}
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
