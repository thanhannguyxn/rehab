import { useState, useEffect } from 'react';
import { useNavigate, Link, useParams, useLocation } from 'react-router-dom';
import { VideoCapture } from '../components/VideoCapture';
import { useWebSocket } from '../hooks/useWebSocket';
import { exerciseAPI, sessionAPI } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import type { Exercise } from '../types';

export default function ExercisePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const location = useLocation();
  const pathname = location.pathname;
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [selectedExercise, setSelectedExercise] = useState<string | null>(null);
  const [isExercising, setIsExercising] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [showSummary, setShowSummary] = useState(false);
  const [sessionSummary, setSessionSummary] = useState<any>(null);
  const [showInstructionsModal, setShowInstructionsModal] = useState(false);

  const { isConnected, analysisData, sendFrame, resetCounter } = useWebSocket(
    selectedExercise || 'squat',
    isExercising
  );

  const { exerciseId } = useParams<{ exerciseId?: string }>();

  useEffect(() => {
    loadExercises();
  }, [exerciseId]);

  const loadExercises = async () => {
    try {
      const data = await exerciseAPI.getExercises();
      setExercises(data.exercises || []);
      if (exerciseId) {
        // If opened via /exercise/:exerciseId, try to select that one
        const found = (data.exercises || []).find((ex: Exercise) => ex.id === exerciseId);
        if (found) {
          setSelectedExercise(exerciseId);
        } else if ((data.exercises || []).length > 0) {
          // fallback to first if not found
          setSelectedExercise(data.exercises[0].id);
        }
      } else {
        if ((data.exercises || []).length > 0) {
          setSelectedExercise(data.exercises[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to load exercises:', error);
    }
  };

  // Instead of starting immediately, show instructions modal first. Actual
  // session start happens in startSessionConfirmed().
  const handleStart = () => {
    if (!selectedExercise) return;
    setShowInstructionsModal(true);
  };

  const startSessionConfirmed = async () => {
    setShowInstructionsModal(false);
    try {
      const result = await sessionAPI.startSession(selectedExercise as string);
      console.log('startSessionConfirmed: startSession result=', result);
      setSessionId(result.session_id);
      setIsExercising(true);
      setShowSummary(false);
    } catch (error) {
      console.error('Failed to start session:', error);
      alert('Không thể bắt đầu buổi tập. Vui lòng thử lại.');
    }
  };

  const handleStop = async () => {
    setIsExercising(false);

    try {
      if (sessionId) {
        console.log('handleStop: calling endSession for id=', sessionId);
        const result = await sessionAPI.endSession(sessionId);
        console.log('handleStop: endSession result=', result);
        setSessionSummary(result);
        setShowSummary(true);
      } else {
        console.warn('handleStop: no sessionId available, showing fallback summary');
        setSessionSummary({
          accuracy: 0,
          total_reps: 0,
          correct_reps: 0,
          duration_seconds: 0,
          common_errors: {},
        });
        setShowSummary(true);
      }
    } catch (error) {
      console.error('Failed to end session:', error);
      setSessionSummary({
        accuracy: 0,
        total_reps: 0,
        correct_reps: 0,
        duration_seconds: 0,
        common_errors: {},
      });
      setShowSummary(true);
    }
  };

  const handleReset = () => {
    resetCounter();
  };

  const currentExercise = exercises.find((ex) => ex.id === selectedExercise);

  // Static exercise details (used for instructions modal). If you later
  // have these coming from the API, replace this with API data.
  const exerciseDetails: Record<string, { difficulty: string; description: string; instructions: string[] }> = {
    squat: {
      difficulty: 'Trung bình',
      description: 'Bài tập tăng cường cơ chân và và hông',
      instructions: [
        'Đứng thẳng, hai tay duỗi thẳng hai bên',
        'Từ từ hạ thấp cơ thể xuống như ngồi ghế',
        'Giữ lưng thẳng trong suốt động tác',
        'Hạ tay từ từ về tư thế ban đầu',
      ],
    },
    arm_raise: {
      difficulty: 'Dễ',
      description: 'Bài tập vai và tay',
      instructions: [
        'Đứng thẳng, hai tay duỗi thẳng hai bên',
        'Từ từ nâng tay lên cao qua đầu',
        'Giữ tay thẳng trong suốt động tác',
        'Hạ tay từ từ về tư thế ban đầu',
      ],
    },
  };

  return (
    // root: giảm kích thước chữ mặc định cho toàn trang exercise
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-teal-50 text-sm">
      {/* Navbar (copied from ExercisesList for consistent header) */}
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

      {/* Main split: giảm cỡ chữ cho các tiêu đề con & các nút điều khiển */}
      <main className="flex flex-col md:flex-row gap-6 px-6 py-6 max-w-7xl mx-auto mt-6">
        {/* Camera on the left */}
        <section className="md:w-1/2 w-full flex flex-col">
          <h2 className="text-lg md:text-xl font-semibold mb-1">Camera</h2>
          <p className="text-sm text-gray-500 mb-4">Luồng camera trực tiếp của bạn — sẽ tự động bật khi bắt đầu buổi tập</p>
          <div className="w-full bg-gray-900 rounded-xl overflow-hidden relative flex items-center justify-center min-h-[480px] shadow-lg border border-gray-100">
            {isExercising ? (
              <VideoCapture
                isActive={isExercising}
                onFrame={sendFrame}
                landmarks={analysisData?.landmarks}
                feedback={analysisData?.feedback}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="text-6xl mb-4">📷</div>
                  <p className="text-2xl text-gray-300 mb-2">Camera sẽ bật khi bạn bắt đầu</p>
                  <p className="text-lg text-gray-400">Đảm bảo có đủ ánh sáng và không gian</p>
                </div>
              </div>
            )}

            {isExercising && (
              <button
                onClick={handleReset}
                className="absolute bottom-4 left-4 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-md font-semibold"
              >
                🔄 Đặt Lại
              </button>
            )}
          </div>
        </section>

        {/* Tutorial / video instructions on the right */}
        <aside className="md:w-1/2 w-full flex flex-col">
          <h2 className="text-lg md:text-xl font-semibold mb-1">Video hướng dẫn</h2>
          <p className="text-sm text-gray-500 mb-4">Xem hướng dẫn trước khi bắt đầu — video minh họa cách thực hiện đúng kỹ thuật</p>
          <div className="w-full bg-white rounded-xl p-4 shadow-2xl flex flex-col overflow-hidden min-h-[480px] border border-gray-50">
            <div className="flex-1 bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center">
              {/* Wide / horizontal tutorial placeholder */}
              <div className="w-full h-full flex items-center justify-center text-center p-6">
                <div>
                  <svg className="w-20 h-20 text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-gray-600 text-xl font-medium">Video hướng dẫn sẽ hiển thị ở đây</p>
                  <p className="text-sm md:text-base text-gray-500 mt-2">Bạn có thể thêm iframe hoặc thẻ &lt;video&gt; vào đây. Kích thước sẽ được tối ưu để vừa khung ngang.</p>
                </div>
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Mục tiêu: {currentExercise?.target_reps || 15} lần</p>
                <div className="mt-1 text-2xl font-bold text-gray-800">
                  {isExercising ? analysisData?.rep_count || 0 : 0} / {currentExercise?.target_reps || 15}
                </div>
              </div>
              <div className="flex items-center gap-3">
                {isExercising && (
                  <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
                )}
                <button
                  onClick={isExercising ? handleStop : handleStart}
                  disabled={!selectedExercise}
                  className={`px-6 py-3 rounded-lg font-bold transition shadow-lg ${
                    isExercising ? 'bg-red-600 hover:bg-red-700 text-white' : 'bg-teal-600 hover:bg-teal-700 text-white'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {isExercising ? '⏹ Dừng' : '▶ Bắt Đầu'}
                </button>
              </div>
            </div>
          </div>
        </aside>
      </main>

      {/* Session summary modal (in-page overlay) */}
      {showSummary && sessionSummary && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg w-full max-w-3xl p-6 mx-4 shadow-xl">
            <div className="text-center mb-6">
              <h2 className="text-4xl font-bold text-gray-800 mb-2">🎉 Hoàn Thành!</h2>
              <div className="text-5xl font-bold text-green-600 mb-2">{sessionSummary.accuracy?.toFixed(1)}%</div>
              <p className="text-lg text-gray-600">Độ chính xác</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
              <div className="bg-blue-50 p-6 rounded-lg text-center">
                <p className="text-gray-600 text-lg mb-2">Tổng số lần</p>
                <p className="text-4xl font-bold text-blue-600">{sessionSummary.total_reps}</p>
              </div>
              <div className="bg-green-50 p-6 rounded-lg text-center">
                <p className="text-gray-600 text-lg mb-2">Đúng kỹ thuật</p>
                <p className="text-4xl font-bold text-green-600">{sessionSummary.correct_reps}</p>
              </div>
              <div className="bg-purple-50 p-6 rounded-lg text-center">
                <p className="text-gray-600 text-lg mb-2">Thời gian</p>
                <p className="text-4xl font-bold text-purple-600">{Math.floor(sessionSummary.duration_seconds / 60)}p</p>
              </div>
            </div>

            {sessionSummary.common_errors && Object.keys(sessionSummary.common_errors).length > 0 && (
              <div className="mb-6">
                <h4 className="text-lg font-semibold mb-2">Lỗi thường gặp</h4>
                <ul className="list-disc list-inside text-gray-700">
                  {Object.entries(sessionSummary.common_errors).map(([error, count]: [string, any]) => (
                    <li key={error}>{error} — {count} lần</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={() => {
                  setShowSummary(false);
                  setSessionId(null);
                }}
                className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-bold py-4 px-6 rounded-lg text-lg"
              >
                Tập Tiếp
              </button>
              <button
                onClick={() => navigate('/')}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-4 px-6 rounded-lg text-lg"
              >
                Về Trang Chủ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      {/* Instructions Modal (shows before starting) */}
      {showInstructionsModal && currentExercise && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg w-full max-w-2xl p-6 mx-4 shadow-lg">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-2xl font-bold">Hướng Dẫn: {currentExercise.name}</h3>
              <button onClick={() => setShowInstructionsModal(false)} className="text-gray-500 hover:text-gray-700">✕</button>
            </div>

            <p className="text-gray-600 mb-4">{exerciseDetails[currentExercise.id]?.description}</p>

            <div className="space-y-2 mb-6">
              {exerciseDetails[currentExercise.id]?.instructions.map((step, idx) => (
                <div key={idx} className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-teal-100 text-teal-600 flex items-center justify-center font-semibold">{idx + 1}</div>
                  <p className="text-gray-700">{step}</p>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3">
              <button onClick={() => setShowInstructionsModal(false)} className="px-4 py-2 rounded-md bg-gray-200 hover:bg-gray-300">Hủy</button>
              <button onClick={startSessionConfirmed} className="px-6 py-2 rounded-md bg-teal-600 hover:bg-teal-700 text-white font-semibold">Bắt Đầu</button>
            </div>
          </div>
        </div>
      )}

      <footer className="bg-white border-t border-gray-200 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-gray-600 text-lg">
            © 2025 AI-Powered Home Rehabilitation System
          </p>
          <p className="text-gray-500 mt-1">
            Được phát triển để hỗ trợ người cao tuổi
          </p>
        </div>
      </footer>
    </div>
  );
};