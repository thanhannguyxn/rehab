import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { VideoCapture } from '../components/VideoCapture';
import { useWebSocket } from '../hooks/useWebSocket';
import { exerciseAPI, sessionAPI } from '../utils/api';
import type { Exercise } from '../utils/types';
import { AngleDisplay } from '../components/AngleDisplay';
import { RelaxationPopup } from '../components/RelaxationPopup';
import { VoiceSettings } from '../components/VoiceSettings';
import { voiceService, VoiceMessages } from '../utils/voiceService';
import { API_URL } from '../utils/config';
import { useTranslation } from 'react-i18next';

interface PersonalizedParams {
  down_angle?: number;
  up_angle?: number;
  max_reps?: number;
  rest_seconds: number;
  difficulty_score: number;
  warnings: string[];
  recommendations: string[];
}

export const ExercisePage = () => {
  const navigate = useNavigate();
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [selectedExercise, setSelectedExercise] = useState<string | null>(null);
  const [isExercising, setIsExercising] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [showSummary, setShowSummary] = useState(false);
  const [sessionSummary, setSessionSummary] = useState<any>(null);
  const [remainingTime, setRemainingTime] = useState<number>(0);
  const [completionStatus, setCompletionStatus] = useState<'completed' | 'timeout' | null>(null);
  const [personalizedParams, setPersonalizedParams] = useState<PersonalizedParams | null>(null);
  const [loadingParams, setLoadingParams] = useState(false);
  const [showRelaxation, setShowRelaxation] = useState(false);
  const [showVoiceSettings, setShowVoiceSettings] = useState(false);
  const { t } = useTranslation();

  // Track last announced rep and error to avoid repetition
  const lastAnnouncedRep = useRef<number>(0);
  const lastErrorAnnounced = useRef<string>('');
  const lastErrorTime = useRef<number>(0);

  // Prepare custom thresholds for WebSocket
  const customThresholds = personalizedParams ? {
    down_angle: personalizedParams.down_angle,
    up_angle: personalizedParams.up_angle,
    max_reps: personalizedParams.max_reps
  } : undefined;

  const { isConnected, analysisData, sendFrame, resetCounter } = useWebSocket(
    selectedExercise || 'squat',
    isExercising,
    customThresholds,
    sessionId
  );

  useEffect(() => {
    loadExercises();
  }, []);

  useEffect(() => {
    if (selectedExercise) {
      loadPersonalizedParams();
    }
  }, [selectedExercise]);

  const loadExercises = async () => {
    try {
      const data = await exerciseAPI.getExercises();
      setExercises(data.exercises);
      if (data.exercises.length > 0) {
        setSelectedExercise(data.exercises[0].id);
      }
    } catch (error) {
      console.error('Failed to load exercises:', error);
    }
  };

  const loadPersonalizedParams = async () => {
    if (!selectedExercise) return;

    setLoadingParams(true);
    try {
      const token = sessionStorage.getItem('token');
      const response = await fetch(`${API_URL}/personalized-params`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ exercise_type: selectedExercise })
      });

      if (response.ok) {
        const data = await response.json();
        setPersonalizedParams(data);
      } else {
        // If profile not set, params will be null
        setPersonalizedParams(null);
      }
    } catch (error) {
      console.error('Failed to load personalized params:', error);
      setPersonalizedParams(null);
    } finally {
      setLoadingParams(false);
    }
  };

  const handleStart = async () => {
    if (!selectedExercise || !currentExercise) return;

    try {
      const result = await sessionAPI.startSession(selectedExercise);
      setSessionId(result.session_id);
      setIsExercising(true);
      setShowSummary(false);
      setCompletionStatus(null);
      setRemainingTime(currentExercise.duration_seconds);

      // Reset voice tracking refs
      lastAnnouncedRep.current = 0;
      lastErrorAnnounced.current = '';
      lastErrorTime.current = 0;

      // Voice: Start exercise
      setTimeout(() => {
        voiceService.speak(VoiceMessages.start, true);
      }, 1000);
    } catch (error) {
      console.error('Failed to start session:', error);
      alert('Không thể bắt đầu buổi tập. Vui lòng thử lại.');
    }
  };

  const handleStop = async (status: 'completed' | 'timeout' | 'manual' = 'manual') => {
    setIsExercising(false);

    // Stop voice when exercise stops
    voiceService.stop();

    // Reset voice tracking refs
    lastAnnouncedRep.current = 0;
    lastErrorAnnounced.current = '';
    lastErrorTime.current = 0;

    if (sessionId) {
      try {
        const result = await sessionAPI.endSession(sessionId);
        setSessionSummary(result);

        // Determine completion status
        if (status === 'completed') {
          setCompletionStatus('completed');
          // Voice: Completed
          voiceService.speak(VoiceMessages.complete, true);
          // Show relaxation popup after completing exercise (allow initial voice to finish)
          setTimeout(() => {
            setShowRelaxation(true);
          }, 2000);
        } else if (status === 'timeout') {
          setCompletionStatus('timeout');
          // Voice: Timeout
          voiceService.speak(VoiceMessages.timeout, true);
          setShowSummary(true);
        } else {
          // Manual stop - check if target was reached
          const targetReached = targetReps && analysisData?.rep_count &&
                                analysisData.rep_count >= targetReps;
          setCompletionStatus(targetReached ? 'completed' : 'timeout');

          // Show relaxation if target reached
          if (targetReached) {
            voiceService.speak(VoiceMessages.complete, true);
            setTimeout(() => {
              setShowRelaxation(true);
            }, 2000);
          } else {
            setShowSummary(true);
          }
        }
      } catch (error) {
        console.error('Failed to end session:', error);
      }
    }
  };

  const handleReset = () => {
    resetCounter();
  };

  const currentExercise = exercises.find((ex) => ex.id === selectedExercise);

  // Use personalized reps if available, otherwise use default
  const targetReps = personalizedParams?.max_reps || currentExercise?.target_reps || 15;

  // Timer countdown effect with voice warnings
  useEffect(() => {
    if (!isExercising || remainingTime <= 0) return;

    const timer = setInterval(() => {
      setRemainingTime((prev) => {
        if (prev <= 1) {
          // Time's up! Auto stop with timeout status
          handleStop('timeout');
          return 0;
        }

        // Voice warnings at specific times
        if (prev === 60) {
          voiceService.addToQueue(VoiceMessages.timeRemaining(60));
        } else if (prev === 30) {
          voiceService.addToQueue(VoiceMessages.timeRemaining(30));
        } else if (prev === 10) {
          voiceService.addToQueue(VoiceMessages.timeRemaining(10));
        }

        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isExercising, remainingTime]);

  // Auto-complete when target reps reached + voice feedback
  useEffect(() => {
    if (!isExercising || !analysisData?.rep_count) return;

    const currentRep = analysisData.rep_count;

    // Voice milestones
    if (currentRep === Math.floor(targetReps * 0.25)) {
      // 25%
      voiceService.addToQueue(VoiceMessages.encouragement.good);
    } else if (currentRep === Math.floor(targetReps * 0.5)) {
      // 50%
      voiceService.addToQueue(VoiceMessages.halfway);
    } else if (currentRep === Math.floor(targetReps * 0.75)) {
      // 75%
      voiceService.addToQueue(VoiceMessages.almostDone);
    } else if (currentRep === targetReps - 1) {
      // Last rep
      voiceService.addToQueue(VoiceMessages.lastRep);
    }

    if (currentRep >= targetReps) {
      // Completed! Auto stop after a short delay
      const timeout = setTimeout(() => {
        handleStop('completed');
      }, 2000); // 2 second delay to show completion

      return () => clearTimeout(timeout);
    }
  }, [isExercising, analysisData?.rep_count, targetReps]);

  // Voice feedback for rep count changes
  useEffect(() => {
    if (!isExercising || !analysisData?.rep_count) return;

    const currentRep = analysisData.rep_count;

    // Announce each rep number only once (when rep changes)
    if (currentRep > 0 && currentRep <= targetReps && currentRep !== lastAnnouncedRep.current) {
      voiceService.speak(`${currentRep}`, false);
      lastAnnouncedRep.current = currentRep;
    }
  }, [analysisData?.rep_count, isExercising, targetReps]);

  // Voice feedback for errors (real-time with 3-second cooldown)
  useEffect(() => {
    if (!isExercising || !analysisData?.feedback) return;

    const feedback = analysisData.feedback;

    // Only announce errors (feedback that contains warning/error keywords)
    if (feedback && feedback.length > 0) {
      // Get the latest error message
      const latestError = feedback[feedback.length - 1];
      const now = Date.now();

      // Only announce if different error or 3 seconds passed since last announcement
      if (latestError !== lastErrorAnnounced.current || now - lastErrorTime.current > 3000) {
        let errorMessage = '';

        // Map error keywords to voice warnings (simplified for common errors)
        if (latestError.includes('vai chưa đủ') || latestError.includes('chưa đủ cao')) {
          errorMessage = VoiceMessages.errors.shoulderNotHigh;
        } else if (latestError.includes('tay cong') || latestError.includes('không thẳng tay')) {
          errorMessage = VoiceMessages.errors.armsBent;
        } else if (latestError.includes('chưa xuống') || latestError.includes('chưa hạ')) {
          errorMessage = VoiceMessages.errors.notLowered;
        } else if (latestError.includes('chưa xuống đủ') || latestError.includes('chưa gập đủ')) {
          errorMessage = VoiceMessages.errors.notDeep;
        } else if (latestError.includes('gối') || latestError.includes('knee')) {
          errorMessage = VoiceMessages.errors.kneesForward;
        } else if (latestError.includes('không thẳng') || latestError.includes('cong lưng')) {
          errorMessage = VoiceMessages.errors.notStraight;
        } else if (latestError.includes('gót') || latestError.includes('heel')) {
          errorMessage = VoiceMessages.errors.notRaised;
        } else if (latestError.includes('chân cong') || latestError.includes('leg bent')) {
          errorMessage = VoiceMessages.errors.kneesBent;
        }

        if (errorMessage) {
          voiceService.addToQueue(errorMessage);
          lastErrorAnnounced.current = latestError;
          lastErrorTime.current = now;
        }
      }
    }
  }, [analysisData?.feedback, isExercising]);

  // Exercise details and instructions
  const exerciseDetails: Record<string, { difficulty: string; description: string; instructions: string[] }> = {
    squat: {
      difficulty: t("exercisePage.exercises.difficulty.medium"),
      description: t("exercisePage.exercises.description.squat"),
      instructions: t("exercisePage.exercises.instructions.squat", {returnObjects: true}) as string[],
    },
    arm_raise: {
      difficulty: t("exercisePage.exercises.difficulty.easy"),
      description: t("exercisePage.exercises.description.armRaise"),
      instructions: t("exercisePage.exercises.instructions.armRaise", {returnObjects: true}) as string[],
    },

    // THÊM MỚI
    single_leg_stand: {
      difficulty: t("exercisePage.exercises.difficulty.medium"),
      description: t("exercisePage.exercises.description.singleLegStand"),
      instructions: t("exercisePage.exercises.instructions.singleLegStand", {returnObjects: true}) as string[],
    },
    // THÊM MỚI
    calf_raise: {
      difficulty: t("exercisePage.exercises.difficulty.easy"),
      description: t("exercisePage.exercises.description.calfRaise"),
      instructions: t("exercisePage.exercises.instructions.calfRaise", {returnObjects: true}) as string[],
    },
  };

  return (
    <>
      <div className="min-h-screen bg-gray-50 dark:bg-black text-gray-900 dark:text-white transition-colors duration-300">
        <div className="max-w-7xl mx-auto p-6">
          <h1 className="text-5xl font-black text-gray-900 dark:text-white mb-8 bg-gradient-to-r from-teal-500 to-cyan-500 dark:from-teal-400 dark:to-cyan-400 bg-clip-text text-transparent">{t("exercisePage.title")}</h1>

          {/* Exercise Selection at Top */}
          <div className="bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl mb-6 transition-colors duration-300">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">{t("exercisePage.selectExercise")}</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {exercises.map((exercise) => {
                const details = exerciseDetails[exercise.id];
                const isSelected = selectedExercise === exercise.id;

                return (
                  <button
                    key={exercise.id}
                    onClick={() => !isExercising && setSelectedExercise(exercise.id)}
                    disabled={isExercising}
                    className={`w-full text-left p-4 rounded-xl border-2 transition-all duration-300 ${
                      isSelected
                        ? 'border-teal-500 bg-gradient-to-br from-teal-50 to-cyan-50 dark:from-teal-500/20 dark:to-cyan-500/20 shadow-lg shadow-teal-500/20'
                        : 'border-gray-300 dark:border-gray-700 hover:border-teal-400 dark:hover:border-teal-500/50 bg-white dark:bg-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-xl ${isSelected ? 'bg-gradient-to-br from-teal-500 to-cyan-500' : 'bg-gray-300 dark:bg-gray-700'}`}>
                          {exercise.id === 'squat' ? (
                            <svg className={`w-6 h-6 ${isSelected ? 'text-white' : 'text-gray-700 dark:text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                          ) : (
                            <svg className={`w-6 h-6 ${isSelected ? 'text-white' : 'text-gray-700 dark:text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
                            </svg>
                          )}
                        </div>
                        <div>
                          <h3 className="font-bold text-lg text-gray-900 dark:text-white">{t(`exercisePage.exercises.names.${exercise.id}`)}</h3>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            details?.difficulty === t("exercisePage.exercises.difficulty.easy") ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400' :
                            details?.difficulty === t("exercisePage.exercises.difficulty.medium") ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400' :
                            'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'
                          }`}>
                            {details?.difficulty || t("exercisePage.exercises.difficulty.easy")}
                          </span>
                        </div>
                      </div>
                      {isSelected && (
                        <div className="text-teal-500 dark:text-teal-400">
                          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        </div>
                      )}
                    </div>
                    <p className="text-gray-700 dark:text-gray-400 text-sm mb-2">{details?.description}</p>
                    <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-500">
                      <span className="flex items-center gap-1">
                       {exercise.id === 'squat' ? '5-10 ' + t("exercisePage.minute") : '5 ' + t("exercisePage.minute")}
                      </span>
                      <span className="flex items-center gap-1">
                       {exercise.target_reps} reps
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Left: Video Area (3 columns) */}
            <div className="lg:col-span-3 space-y-4">
              {/* Main Video Display */}
              <div className="bg-gray-200 dark:bg-gray-900 rounded-lg overflow-hidden relative transition-colors duration-300" style={{ aspectRatio: '16/9' }}>
                {isExercising ? (
                <VideoCapture
                  isActive={isExercising}
                  onFrame={sendFrame}
                  landmarks={analysisData?.landmarks}
                  feedback={analysisData?.feedback}
                  repCount={analysisData?.rep_count}
                  targetReps={targetReps}
                  remainingTime={remainingTime}
                  analysisData={{
                    hold_time_remaining: analysisData?.hold_time_remaining,
                    rep_count: analysisData?.rep_count
                  }}
                  currentExercise={{
                    target_reps: targetReps
                  }}
                />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-6xl mb-4">📹</div>
                      <p className="text-2xl text-gray-700 dark:text-gray-400 mb-2">{t("exercisePage.cameraPlaceholder")}</p>
                      <p className="text-lg text-gray-600 dark:text-gray-500">{t("exercisePage.cameraNote")}</p>
                    </div>
                  </div>
                )}
              </div>


              {/* Control Button */}
              <button
                onClick={isExercising ? () => handleStop('manual') : handleStart}
                disabled={!selectedExercise}
                className={`w-full py-6 rounded-xl font-bold text-2xl transition shadow-2xl ${
                  isExercising
                    ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white shadow-red-500/50'
                    : 'bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600 text-white shadow-teal-500/50'
                } disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105`}
              >
                {isExercising ? '⏸ ' + t("exercisePage.pause") : '▶ ' + t("exercisePage.start")}
              </button>

              {/* Voice Settings Button */}
              <button
                onClick={() => setShowVoiceSettings(true)}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold py-4 rounded-xl text-xl transition shadow-lg transform hover:scale-105"
              >
                {t("exercisePage.voiceSettings")}
              </button>

              {isExercising && (
                <button
                  onClick={handleReset}
                  className="w-full bg-gray-200 dark:bg-gradient-to-br dark:from-gray-800 dark:to-gray-900 hover:bg-gray-300 dark:hover:from-gray-700 dark:hover:to-gray-800 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white font-bold py-4 rounded-xl text-xl transition shadow-lg"
                >
                  {t("exercisePage.reset")}
                </button>
              )}

              {/* Instructions Section */}
              {currentExercise && (
                <div className="bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl transition-colors duration-300">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    {t("exercisePage.instructions")}: {currentExercise.name}
                  </h2>
                  <p className="text-lg text-gray-800 dark:text-gray-400 mb-4">
                    {exerciseDetails[currentExercise.id]?.description}
                  </p>
                  <div className="space-y-2">
                    <p className="font-semibold text-gray-900 dark:text-white text-lg">{t("exercisePage.steps")}</p>
                    {exerciseDetails[currentExercise.id]?.instructions.map((step, index) => (
                      <p key={index} className="text-gray-800 dark:text-gray-300 text-base">
                        {index + 1}. {step}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Exercise instruction video */}
              <div className="bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl transition-colors duration-300">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">{t("exercisePage.videoGuide")}</h3>
                <div className="bg-gray-200 dark:bg-black rounded-xl aspect-video flex items-center justify-center border border-gray-300 dark:border-gray-800 transition-colors duration-300 overflow-hidden">
                  {selectedExercise ? (
                    <>
                      <video
                        key={selectedExercise}
                        controls
                        loop
                        autoPlay
                        muted
                        playsInline
                        className="w-full h-full object-contain"
                        onVolumeChange={(e) => {
                          // Force muted to always be true
                          const video = e.currentTarget;
                          if (!video.muted) {
                            video.muted = true;
                          }
                        }}
                        src={
                          selectedExercise === 'squat' ? '/squat.mp4' :
                          selectedExercise === 'arm_raise' ? '/arm_raise.mp4' :
                          selectedExercise === 'calf_raise' ? '/calf_raise.mp4' :
                          selectedExercise === 'single_leg_stand' ? '/single_leg_stand.mp4' :
                          ''
                        }
                        onError={(e) => {
                          // Only show placeholder if video truly cannot be loaded
                          const video = e.currentTarget;
                          if (video.networkState === HTMLMediaElement.NETWORK_NO_SOURCE) {
                            console.error('Video file not found for exercise:', selectedExercise);
                            video.style.display = 'none';
                            const placeholder = video.parentElement?.querySelector('.video-placeholder');
                            if (placeholder) {
                              (placeholder as HTMLElement).style.display = 'flex';
                            }
                          }
                        }}
                        onLoadedData={(e) => {
                          console.log('Video loaded successfully for:', selectedExercise);
                          // Make sure video is visible and placeholder is hidden
                          const video = e.currentTarget;
                          video.style.display = 'block';
                          const placeholder = video.parentElement?.querySelector('.video-placeholder');
                          if (placeholder) {
                            (placeholder as HTMLElement).style.display = 'none';
                          }
                        }}
                      >
                        {t("exercisePage.noVideoSupport")}
                      </video>
                      <div className="video-placeholder text-center" style={{ display: 'none', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%', position: 'absolute' }}>
                        <svg className="w-20 h-20 text-gray-400 dark:text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p className="text-gray-600 dark:text-gray-500 text-lg">
                          {t("exercisePage.noVideo")}
                        </p>
                      </div>
                    </>
                  ) : (
                    <div className="text-center" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%' }}>
                      <svg className="w-20 h-20 text-gray-400 dark:text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <p className="text-gray-600 dark:text-gray-500 text-lg">
                        {t("exercisePage.selectToWatch")}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Progress and Angle Display */}
            <div className="lg:col-span-1">
              <div className="sticky top-6 space-y-3">
                {/* Exercise Progress Section */}
                <div className="bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-xl transition-colors duration-300 z-10">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">{t("exercisePage.progress")}</h2>
                  <p className="text-xs text-gray-700 dark:text-gray-400 mb-3">{t("exercisePage.target")}: {targetReps} {t("exercisePage.targetReps")} {currentExercise?.duration_seconds ? Math.floor(currentExercise.duration_seconds / 60) : 3} {t("exercisePage.minute")}</p>
                  
                  <div className="space-y-2">
                    {/* Timer display */}
                    {isExercising && remainingTime > 0 && (
                      <div className={`w-full px-4 py-3 rounded-lg border-2 ${
                        remainingTime <= 10
                          ? 'bg-red-600 border-red-500'
                          : remainingTime <= 30
                          ? 'bg-orange-600 border-orange-500'
                          : 'bg-gradient-to-br from-blue-600 to-blue-700 border-blue-500'
                      } text-white shadow-lg`}>
                        <div className="text-2xl font-bold mb-0.5 text-center">
                          {Math.floor(remainingTime / 60)}:{(remainingTime % 60).toString().padStart(2, '0')}
                        </div>
                        <div className="text-center text-xs opacity-90">{t("exercisePage.time")}</div>
                      </div>
                    )}
                    
                    {/* Rep counter */}
                    <div className={`w-full px-4 py-3 rounded-lg border-2 ${
                      isExercising && analysisData?.rep_count && analysisData.rep_count >= targetReps
                        ? 'bg-gradient-to-br from-green-600 to-green-700 border-green-500'
                        : 'bg-gradient-to-br from-teal-600 to-cyan-600 border-teal-500'
                    } text-white shadow-lg`}>
                      <div className="text-3xl font-bold mb-0.5 text-center">
                        {isExercising ? analysisData?.rep_count || 0 : 0} / {targetReps}
                      </div>
                      <div className="text-center text-xs opacity-90">{t("exercisePage.reps")}</div>
                    </div>
                  </div>

                  {isExercising && (
                    <div className="mt-3 flex items-center justify-center">
                      <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse mr-2`}></div>
                      <span className="text-xs text-gray-700 dark:text-gray-400">
                        {isConnected ? t("exercisePage.connected") : t("exercisePage.disconnected")}
                      </span>
                    </div>
                  )}
                </div>
                
                <AngleDisplay
                  angles={analysisData?.angles}
                  exerciseType={selectedExercise || 'squat'}
                  isDetected={analysisData?.pose_detected || false}
                />

              {/* Personalized Parameters Card */}
              {personalizedParams && (
                <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/30 dark:to-purple-900/30 border border-blue-300 dark:border-blue-500/30 rounded-xl p-5 shadow-lg">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">{t("exercisePage.personalized")}</h3>

                  {/* Difficulty Score */}
                  <div className="mb-4 p-3 bg-blue-100 dark:bg-black/30 rounded-lg border border-blue-200 dark:border-transparent">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-base text-gray-700 dark:text-gray-300">{t("exercisePage.difficulty")}:</span>
                      <span className="text-lg font-bold text-teal-600 dark:text-teal-400">
                        {Math.round(personalizedParams.difficulty_score * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-300 dark:bg-gray-700 rounded-full h-2.5">
                      <div
                        className="bg-gradient-to-r from-teal-500 to-cyan-500 h-2.5 rounded-full transition-all duration-500"
                        style={{ width: `${personalizedParams.difficulty_score * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Parameters */}
                  <div className="space-y-2 mb-4">
                    {personalizedParams.down_angle && (
                      <div className="flex items-center justify-between text-base">
                        <span className="text-gray-700 dark:text-gray-300">{t("exercisePage.angle")}:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">
                          {Math.round(personalizedParams.down_angle)}° - {Math.round(personalizedParams.up_angle || 180)}°
                        </span>
                      </div>
                    )}
                    {personalizedParams.max_reps && (
                      <div className="flex items-center justify-between text-base">
                        <span className="text-gray-700 dark:text-gray-300">Rep:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{personalizedParams.max_reps} lần</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between text-base">
                      <span className="text-gray-700 dark:text-gray-300">{t("exercisePage.rest")}:</span>
                      <span className="font-semibold text-gray-900 dark:text-white">{personalizedParams.rest_seconds}s</span>
                    </div>
                  </div>

                  {/* Warnings */}
                  {personalizedParams.warnings.length > 0 && (
                    <div className="mb-3 p-3 bg-orange-50 dark:bg-orange-900/30 border border-orange-300 dark:border-orange-500/30 rounded-lg">
                      <span className="font-semibold text-orange-700 dark:text-orange-300 text-base block mb-2">{t("exercisePage.warnings")}:</span>
                      <ul className="space-y-1.5 text-sm text-orange-800 dark:text-orange-200">
                        {personalizedParams.warnings.map((warning, idx) => (
                          <li key={idx}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Recommendations */}
                  {personalizedParams.recommendations.length > 0 && (
                    <div className="p-3 bg-green-50 dark:bg-green-900/30 border border-green-300 dark:border-green-500/30 rounded-lg">
                      <span className="font-semibold text-green-700 dark:text-green-300 text-base block mb-2">{t("exercisePage.recommendations")}:</span>
                      <ul className="space-y-1.5 text-sm text-green-800 dark:text-green-200">
                        {personalizedParams.recommendations.map((rec, idx) => (
                          <li key={idx}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Profile prompt if no personalized params */}
              {!loadingParams && !personalizedParams && (
                <div className="p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-xl">
                  <p className="text-xs text-yellow-200 font-semibold mb-1">
                    {t("exercisePage.noProfile")}
                  </p>
                  <p className="text-[10px] text-yellow-300/80 mb-2">
                    {t("exercisePage.fillProfile")}
                  </p>
                  <button
                    onClick={() => navigate('/profile')}
                    className="text-[10px] bg-yellow-600 hover:bg-yellow-700 text-white px-2 py-1 rounded-lg transition"
                  >
                    {t("exercisePage.fillNow")} →
                  </button>
                </div>
              )}
              </div>
            </div>
          </div>
        </div>

        {/* Session Summary Modal Popup */}
        {showSummary && sessionSummary && (
          <div className="fixed inset-0 bg-black/80 dark:bg-black/90 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-8">
                {/* Header with completion status */}
                <div className="text-center mb-8">
                  {completionStatus === 'completed' ? (
                    <>
                      <h2 className="text-4xl font-bold text-green-500 dark:text-green-400 mb-2">{t("exercisePage.completed")}</h2>
                      <p className="text-xl text-gray-600 dark:text-gray-400">{t("exercisePage.completedDesc")}</p>
                    </>
                  ) : (
                    <>
                      <h2 className="text-4xl font-bold text-orange-500 dark:text-orange-400 mb-2">{t("exercisePage.timeout")}</h2>
                      <p className="text-xl text-gray-600 dark:text-gray-400">{t("exercisePage.timeoutDesc")}</p>
                    </>
                  )}
                </div>

                {/* Accuracy */}
                <div className="text-center mb-6">
                  <div className={`text-6xl font-bold mb-2 ${
                    completionStatus === 'completed' ? 'text-green-500 dark:text-green-400' : 'text-orange-500 dark:text-orange-400'
                  }`}>
                    {sessionSummary?.accuracy?.toFixed(1)}%
                  </div>
                  <p className="text-xl text-gray-600 dark:text-gray-400">{t("exercisePage.accuracy")}</p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                  <div className="bg-blue-50 dark:bg-gradient-to-br dark:from-blue-500/20 dark:to-blue-600/20 border border-blue-200 dark:border-blue-500/30 p-4 rounded-xl text-center">
                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-1">{t("exercisePage.totalReps")}</p>
                    <p className="text-3xl font-bold text-blue-500 dark:text-blue-400">{sessionSummary?.total_reps}</p>
                  </div>
                  <div className="bg-green-50 dark:bg-gradient-to-br dark:from-green-500/20 dark:to-green-600/20 border border-green-200 dark:border-green-500/30 p-4 rounded-xl text-center">
                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-1">{t("exercisePage.correctReps")}</p>
                    <p className="text-3xl font-bold text-green-500 dark:text-green-400">{sessionSummary?.correct_reps}</p>
                  </div>
                  <div className="bg-purple-50 dark:bg-gradient-to-br dark:from-purple-500/20 dark:to-purple-600/20 border border-purple-200 dark:border-purple-500/30 p-4 rounded-xl text-center">
                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-1">{t("exercisePage.duration")}</p>
                    <p className="text-3xl font-bold text-purple-500 dark:text-purple-400">
                      {Math.floor(sessionSummary?.duration_seconds / 60)}:{(sessionSummary?.duration_seconds % 60).toString().padStart(2, '0')}
                    </p>
                  </div>
                </div>

                {/* Common Errors */}
                {sessionSummary?.common_errors && Object.keys(sessionSummary.common_errors).length > 0 && (
                  <div className="bg-orange-50 dark:bg-gradient-to-br dark:from-orange-500/20 dark:to-red-500/20 border border-orange-200 dark:border-orange-500/30 rounded-xl p-4 mb-6">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-3">{t("exercisePage.commonErrors")}</h3>
                    <div className="space-y-2">
                      {Object.entries(sessionSummary.common_errors).map(([error, data]: [string, any]) => (
                        <div key={error} className="flex justify-between text-base">
                          <span className="text-gray-700 dark:text-gray-300">{error}</span>
                          <span className="font-semibold text-orange-600 dark:text-orange-400">{data.count} rep</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-4">
                  <button
                    onClick={() => {
                      setShowSummary(false);
                      setSessionId(null);
                      setCompletionStatus(null);
                    }}
                    className="flex-1 bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600 text-white font-bold py-4 px-6 rounded-xl text-xl transition shadow-2xl shadow-teal-500/30"
                  >
                    {t("exercisePage.continue")}
                  </button>
                  <button
                    onClick={() => navigate('/')}
                    className="flex-1 bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-700 text-gray-900 dark:text-white font-bold py-4 px-6 rounded-lg text-xl transition shadow-lg"
                  >
                    {t("exercisePage.backHome")}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Relaxation Popup - Shows after completing exercise */}
        <RelaxationPopup
          isOpen={showRelaxation}
          onClose={() => {
            setShowRelaxation(false);
            // Auto show summary after relaxation
            if (!showSummary) {
              setShowSummary(true);
            }
          }}
          duration={180} // 3 minutes = 180 seconds
        />

        {/* Voice Settings Modal */}
        <VoiceSettings
          isOpen={showVoiceSettings}
          onClose={() => setShowVoiceSettings(false)}
        />
      </div>
    </>
  );
};