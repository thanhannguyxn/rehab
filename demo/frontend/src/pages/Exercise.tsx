import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { exerciseAPI, sessionAPI } from '../utils/api';
import { useWebSocket } from '../hooks/useWebSocket';
import VideoCapture from '../components/VideoCapture';
import type { Exercise } from '../types';

const ExercisePage: React.FC = () => {
  const { exerciseId } = useParams<{ exerciseId: string }>();
  const navigate = useNavigate();
  
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [isExercising, setIsExercising] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sessionSummary, setSessionSummary] = useState<any>(null);
  const [showSummary, setShowSummary] = useState(false);

  const { isConnected, analysisData, sendFrame, resetCounter } = useWebSocket(
    exerciseId || '',
    isExercising
  );

  useEffect(() => {
    const loadExercise = async () => {
      try {
        const exercises = await exerciseAPI.getExercises();
        const found = exercises.find(ex => ex.id === exerciseId);
        if (found) {
          setExercise(found);
        } else {
          navigate('/patient');
        }
      } catch (error) {
        console.error('Failed to load exercise:', error);
        navigate('/patient');
      }
    };

    loadExercise();
  }, [exerciseId, navigate]);

  const handleStart = async () => {
    if (!exerciseId) return;

    try {
      const result = await sessionAPI.startSession(exerciseId);
      setSessionId(result.session_id);
      setIsExercising(true);
      setShowSummary(false);
    } catch (error) {
      console.error('Failed to start session:', error);
      alert('Không thể bắt đầu buổi tập. Vui lòng thử lại.');
    }
  };

  const handleEnd = async () => {
    if (!sessionId) return;

    setIsExercising(false);

    try {
      const result = await sessionAPI.endSession(sessionId);
      setSessionSummary(result);
      setShowSummary(true);
    } catch (error) {
      console.error('Failed to end session:', error);
      alert('Không thể kết thúc buổi tập. Vui lòng thử lại.');
    }
  };

  const handleReset = () => {
    resetCounter();
  };

  if (!exercise) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary mx-auto mb-4"></div>
          <p className="text-xl text-gray-600">Đang tải...</p>
        </div>
      </div>
    );
  }

  if (showSummary && sessionSummary) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8 border-2 border-gray-200">
            <div className="text-center mb-8">
              <div className="text-6xl mb-4">🎉</div>
              <h2 className="text-4xl font-bold text-gray-800 mb-2">Hoàn Thành!</h2>
              <p className="text-xl text-gray-600">Bạn đã hoàn thành bài tập</p>
            </div>

            <div className="space-y-6">
              <div className="bg-gradient-to-r from-primary to-primary-dark text-white rounded-xl p-6 text-center">
                <p className="text-xl mb-2">Độ chính xác</p>
                <p className="text-5xl font-bold">{sessionSummary.accuracy?.toFixed(1)}%</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-xl p-6 text-center border-2 border-gray-200">
                  <p className="text-lg text-gray-600 mb-2">Tổng số lần</p>
                  <p className="text-4xl font-bold text-gray-800">{sessionSummary.total_reps}</p>
                </div>
                <div className="bg-gray-50 rounded-xl p-6 text-center border-2 border-gray-200">
                  <p className="text-lg text-gray-600 mb-2">Làm đúng</p>
                  <p className="text-4xl font-bold text-green-600">{sessionSummary.correct_reps}</p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-xl p-6 text-center border-2 border-gray-200">
                <p className="text-lg text-gray-600 mb-2">Thời gian</p>
                <p className="text-4xl font-bold text-blue-600">
                  {Math.floor(sessionSummary.duration_seconds / 60)}:
                  {(sessionSummary.duration_seconds % 60).toString().padStart(2, '0')}
                </p>
              </div>

              {sessionSummary.common_errors && Object.keys(sessionSummary.common_errors).length > 0 && (
                <div className="bg-orange-50 rounded-xl p-6 border-2 border-orange-200">
                  <h3 className="text-xl font-bold text-gray-800 mb-4">Lỗi cần cải thiện:</h3>
                  <div className="space-y-2">
                    {Object.entries(sessionSummary.common_errors).map(([error, count]: [string, any]) => (
                      <div key={error} className="flex justify-between text-lg">
                        <span className="text-gray-700">{error}</span>
                        <span className="font-semibold text-orange-600">{count} lần</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="mt-8 space-y-4">
              <button
                onClick={() => {
                  setShowSummary(false);
                  setSessionSummary(null);
                }}
                className="w-full bg-primary hover:bg-primary-dark text-white font-bold text-xl py-5 rounded-lg transition-colors"
              >
                Tập Lại
              </button>
              <button
                onClick={() => navigate('/patient')}
                className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold text-xl py-5 rounded-lg transition-colors"
              >
                Về Trang Chủ
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-6 border-2 border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">{exercise.name}</h1>
              <p className="text-xl text-gray-600 mt-1">{exercise.description}</p>
            </div>
            <button
              onClick={() => navigate('/patient')}
              className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold text-lg px-6 py-3 rounded-lg transition-colors"
            >
              ← Quay lại
            </button>
          </div>
        </div>

        {/* Video Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Main Camera */}
          <div className="bg-gray-900 rounded-xl overflow-hidden">
            {isExercising ? (
              <VideoCapture
                isActive={isExercising}
                onFrame={sendFrame}
                landmarks={analysisData?.landmarks}
                feedback={analysisData?.feedback}
                repCount={analysisData?.rep_count}
                targetReps={exercise.target_reps}
              />
            ) : (
              <div className="aspect-video flex items-center justify-center">
                <div className="text-center">
                  <div className="text-white text-6xl mb-4">📹</div>
                  <p className="text-2xl text-gray-400 mb-2">Camera sẽ bật khi bạn bắt đầu</p>
                  <p className="text-lg text-gray-500">Đảm bảo có đủ ánh sáng và không gian</p>
                </div>
              </div>
            )}
          </div>

          {/* Tutorial Video */}
          <div className="bg-white rounded-xl overflow-hidden border-2 border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-xl font-bold text-gray-800">Video Hướng Dẫn</h3>
              <p className="text-gray-600">Xem mẫu để thực hiện động tác chuẩn xác</p>
            </div>
            <div className="aspect-video bg-gray-900 relative">
              {exercise.id === 'squat' ? (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center text-gray-400">
                    <div className="text-6xl mb-4">🏋️‍♂️</div>
                    <p>Video hướng dẫn Squat</p>
                  </div>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center text-gray-400">
                    <div className="text-6xl mb-4">🙋‍♂️</div>
                    <p>Video hướng dẫn Nâng Tay</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-xl shadow-md p-6 border-2 border-gray-200">
          <div className="flex gap-4">
            {!isExercising ? (
              <button
                onClick={handleStart}
                className="flex-1 bg-success hover:bg-success-dark text-white font-bold text-2xl py-6 rounded-lg transition-colors shadow-lg"
              >
                ▶️ Bắt Đầu Tập
              </button>
            ) : (
              <>
                <button
                  onClick={handleEnd}
                  className="flex-1 bg-red-500 hover:bg-red-600 text-white font-bold text-2xl py-6 rounded-lg transition-colors"
                >
                  ⏹️ Kết Thúc
                </button>
                <button
                  onClick={handleReset}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold text-xl px-8 rounded-lg transition-colors"
                >
                  🔄 Reset
                </button>
              </>
            )}
          </div>

          {isExercising && (
            <div className="mt-4 flex items-center justify-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-lg text-gray-600">
                {isConnected ? 'Đang kết nối' : 'Mất kết nối'}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExercisePage;
