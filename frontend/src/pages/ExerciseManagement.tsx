import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_URL, API_BASE_URL } from '../utils/config';
import { useTranslation } from 'react-i18next';

interface PendingExercise {
  id: number;
  video_path: string;
  thumbnail_path?: string;
  status: string;
  detected_type: string;
  confidence: number;
  error_message?: string;
  created_at: string;
}

interface AngleRule {
  id?: number;
  angle_name: string;
  min_angle?: number;
  max_angle?: number;
  error_message: string;
  error_severity: string;
}

interface AngleTracking {
  primary_angles: string[];
  angle_names_vi: Record<string, string>;
  description: string;
}

interface ApprovedExercise {
  id: string;
  name: string;
  description: string;
  target_reps: number;
  duration_seconds: number;
  base_exercise_type: string;
  down_threshold: number;
  up_threshold: number;
  hysteresis: number;
  difficulty_level: string;
  video_path?: string;
  is_default: boolean;
  created_at?: string;
  angle_tracking: AngleTracking;
  angle_rules: AngleRule[];
}

export const ExerciseManagement = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [pendingList, setPendingList] = useState<PendingExercise[]>([]);
  const [approvedList, setApprovedList] = useState<ApprovedExercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'pending' | 'approved'>('approved');

  // Edit modal state
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingExercise, setEditingExercise] = useState<ApprovedExercise | null>(null);
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    target_reps: 15,
    duration_seconds: 300,
    down_threshold: 0,
    up_threshold: 0,
    hysteresis: 5,
    difficulty_level: 'medium',
    base_exercise_type: 'squat'
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadPendingExercises();
    loadApprovedExercises();
  }, []);

  const loadPendingExercises = async () => {
    try {
      const token = sessionStorage.getItem('token');
      const response = await fetch(`${API_URL}/doctor/exercises/pending`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setPendingList(data.pending_exercises);
      }
    } catch (error) {
      console.error('Error loading pending exercises:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadApprovedExercises = async () => {
    try {
      const token = sessionStorage.getItem('token');
      const response = await fetch(`${API_URL}/doctor/exercises`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setApprovedList(data.exercises);
      }
    } catch (error) {
      console.error('Error loading approved exercises:', error);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];

      // Validate file type
      if (!file.type.startsWith('video/')) {
        alert(t('exerciseManagement.alerts.onlyVideo'));
        return;
      }

      // Validate file size (max 100MB)
      if (file.size > 100 * 1024 * 1024) {
        alert(t('exerciseManagement.alerts.fileTooLarge'));
        return;
      }

      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const token = sessionStorage.getItem('token');
      const response = await fetch(`${API_URL}/doctor/exercises/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        await response.json();
        alert(t('exerciseManagement.alerts.uploadSuccess'));
        setSelectedFile(null);
        // Reset file input
        const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
        // Reload pending list
        loadPendingExercises();
        setActiveTab('pending');
      } else {
        const error = await response.json();
        alert(error.detail || t('exerciseManagement.alerts.uploadFailed'));
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert(t('exerciseManagement.alerts.uploadError'));
    } finally {
      setUploading(false);
    }
  };

  const openEditModal = (exercise: ApprovedExercise) => {
    setEditingExercise(exercise);
    setEditForm({
      name: exercise.name,
      description: exercise.description || '',
      target_reps: exercise.target_reps,
      duration_seconds: exercise.duration_seconds,
      down_threshold: exercise.down_threshold,
      up_threshold: exercise.up_threshold,
      hysteresis: exercise.hysteresis || 5,
      difficulty_level: exercise.difficulty_level || 'medium',
      base_exercise_type: exercise.base_exercise_type || 'squat'
    });
    setEditModalOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!editingExercise) return;

    setSaving(true);
    try {
      const token = sessionStorage.getItem('token');
      const response = await fetch(`${API_URL}/doctor/exercises/${editingExercise.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editForm)
      });

      if (response.ok) {
        alert(t('exerciseManagement.alerts.updateSuccess'));
        setEditModalOpen(false);
        setEditingExercise(null);
        loadApprovedExercises();
      } else {
        const error = await response.json();
        alert(error.detail || t('exerciseManagement.alerts.updateError'));
      }
    } catch (error) {
      console.error('Error saving:', error);
      alert(t('exerciseManagement.alerts.updateError'));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteExercise = async (exerciseId: string) => {
    if (!window.confirm(t('exerciseManagement.deleteConfirm'))) return;

    try {
      const token = sessionStorage.getItem('token');
      const response = await fetch(`${API_URL}/doctor/exercises/${exerciseId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert(t('exerciseManagement.deleteSuccess'));
        loadApprovedExercises();
      } else {
        const error = await response.json();
        alert(error.detail || t('exerciseManagement.alerts.deleteErrorTitle'));
      }
    } catch (error) {
      console.error('Error deleting:', error);
      alert(t('exerciseManagement.alerts.deleteErrorTitle'));
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      'UPLOADING': 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400',
      'PROCESSING': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400',
      'PENDING': 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400',
      'APPROVED': 'bg-teal-100 text-teal-700 dark:bg-teal-500/20 dark:text-teal-400',
      'REJECTED': 'bg-gray-100 text-gray-700 dark:bg-gray-500/20 dark:text-gray-400',
      'ERROR': 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'
    };
    const labels: Record<string, string> = {
      'UPLOADING': t('exerciseManagement.status.UPLOADING'),
      'PROCESSING': t('exerciseManagement.status.PROCESSING'),
      'PENDING': t('exerciseManagement.status.PENDING'),
      'APPROVED': t('exerciseManagement.status.APPROVED'),
      'REJECTED': t('exerciseManagement.status.REJECTED'),
      'ERROR': t('exerciseManagement.status.ERROR')
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${styles[status] || styles['PENDING']}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getBaseExerciseLabel = (type: string) => {
    const labels: Record<string, string> = {
      'squat': t('exerciseManagement.baseTypes.squat'),
      'arm_raise': t('exerciseManagement.baseTypes.arm_raise'),
      'calf_raise': t('exerciseManagement.baseTypes.calf_raise'),
      'single_leg_stand': t('exerciseManagement.baseTypes.single_leg_stand')
    };
    return labels[type] || type;
  };

  const getDifficultyBadge = (level: string) => {
    const styles: Record<string, string> = {
      'easy': 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400',
      'medium': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400',
      'hard': 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'
    };
    const labels: Record<string, string> = {
      'easy': t('exerciseManagement.difficulty.easy'),
      'medium': t('exerciseManagement.difficulty.medium'),
      'hard': t('exerciseManagement.difficulty.hard')
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${styles[level] || styles['medium']}`}>
        {labels[level] || level}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-black text-gray-900 dark:text-white transition-colors duration-300">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-black bg-gradient-to-r from-teal-500 to-cyan-500 bg-clip-text text-transparent">
              {t('exerciseManagement.title')}
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              {t('exerciseManagement.subtitle')}
            </p>
          </div>
          <button
            onClick={() => navigate('/doctor')}
            className="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-bold py-2 px-4 rounded-lg transition"
          >
            {t('exerciseManagement.back')}
          </button>
        </div>

        {/* Upload Card */}
        <div className="bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            {t('exerciseManagement.uploadCardTitle')}
          </h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* File Input */}
            <div>
              <label className="block mb-2 font-semibold text-gray-700 dark:text-gray-300">
                {t('exerciseManagement.fileInputLabel')}
              </label>
              <input
                type="file"
                accept="video/*"
                onChange={handleFileChange}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                {t('exerciseManagement.fileSupportText')}
              </p>

              {/* Upload Button */}
              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                className="w-full mt-4 bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600 text-white font-bold py-3 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
              >
                {uploading ? t('exerciseManagement.uploading') : t('exerciseManagement.uploadBtn')}
              </button>
            </div>

            {/* Preview */}
            <div>
              {selectedFile ? (
                <div>
                  <label className="block mb-2 font-semibold text-gray-700 dark:text-gray-300">
                    {t('exerciseManagement.previewLabel')}
                  </label>
                  <video
                    src={URL.createObjectURL(selectedFile)}
                    controls
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600"
                    style={{ maxHeight: '300px' }}
                  />
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg min-h-[200px]">
                  <div className="text-center">
                    <span className="text-5xl">🎥</span>
                    <p className="text-gray-500 dark:text-gray-400 mt-2">
                      {t('exerciseManagement.noVideoPreview')}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('approved')}
            className={`px-6 py-3 rounded-lg font-bold transition ${
              activeTab === 'approved'
                ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white shadow-lg'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            {t('exerciseManagement.tabApproved')} ({approvedList.length})
          </button>
          <button
            onClick={() => setActiveTab('pending')}
            className={`px-6 py-3 rounded-lg font-bold transition ${
              activeTab === 'pending'
                ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white shadow-lg'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            {t('exerciseManagement.tabPending')} ({pendingList.length})
          </button>
        </div>

        {/* Approved Exercises Tab */}
        {activeTab === 'approved' && (
          <div className="bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {t('exerciseManagement.listTitle')}
              </h2>
              <button
                onClick={loadApprovedExercises}
                className="text-teal-600 dark:text-teal-400 hover:underline"
              >
                {t('exerciseManagement.refresh')}
              </button>
            </div>

            {approvedList.length === 0 ? (
              <div className="text-center py-8">
                <span className="text-5xl"></span>
                <p className="text-gray-500 dark:text-gray-400 mt-2">
                  {t('exerciseManagement.emptyApproved')}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {approvedList.map(exercise => (
                  <div
                    key={exercise.id}
                    className="border border-gray-200 dark:border-gray-700 rounded-xl p-4 hover:shadow-lg transition"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                            {exercise.name}
                          </h3>
                          {exercise.is_default && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400 rounded-full text-xs font-semibold">
                              {t('exerciseManagement.defaultBadge')}
                            </span>
                          )}
                          {getDifficultyBadge(exercise.difficulty_level)}
                        </div>

                        <p className="text-gray-600 dark:text-gray-400 mb-3">
                          {exercise.description || t('exerciseManagement.noDesc')}
                        </p>

                        {/* Angle Tracking Info */}
                        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 mb-3">
                          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                            {t('exerciseManagement.angleTrackingTitle')}
                          </h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">{t('exerciseManagement.typeLabel')}</span>
                              <span className="ml-1 font-semibold text-teal-600 dark:text-teal-400">
                                {getBaseExerciseLabel(exercise.base_exercise_type)}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">{t('exerciseManagement.primaryAngleLabel')}</span>
                              <span className="ml-1 font-semibold">
                                {exercise.angle_tracking?.primary_angles?.map(
                                  a => exercise.angle_tracking.angle_names_vi[a] || a
                                ).join(', ')}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">{t('exerciseManagement.downLabel')}</span>
                              <span className="ml-1 font-semibold">{exercise.down_threshold}°</span>
                            </div>
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">{t('exerciseManagement.upLabel')}</span>
                              <span className="ml-1 font-semibold">{exercise.up_threshold}°</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                            {exercise.angle_tracking?.description}
                          </p>
                        </div>

                        {/* Exercise Stats */}
                        <div className="flex gap-4 text-sm text-gray-600 dark:text-gray-400">
                          <span>{exercise.target_reps} {t('exerciseManagement.repsLabel')}</span>
                          <span>{Math.floor(exercise.duration_seconds / 60)} {t('exerciseManagement.minutesLabel')}</span>
                          {exercise.angle_rules?.length > 0 && (
                            <span>{exercise.angle_rules.length} {t('exerciseManagement.rulesLabel')}</span>
                          )}
                        </div>

                        {/* Angle Rules Preview */}
                        {exercise.angle_rules?.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                              {t('exerciseManagement.rulesPreviewTitle')}
                            </h5>
                            <div className="flex flex-wrap gap-2">
                              {exercise.angle_rules.slice(0, 3).map((rule, idx) => (
                                <span
                                  key={idx}
                                  className="px-2 py-1 bg-orange-50 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded text-xs"
                                >
                                  {rule.angle_name}: {rule.min_angle}° - {rule.max_angle}°
                                </span>
                              ))}
                              {exercise.angle_rules.length > 3 && (
                                <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs">
                                  +{exercise.angle_rules.length - 3} {t('exerciseManagement.moreRules')}
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      {!exercise.is_default && (
                        <div className="flex gap-2 ml-4">
                          <button
                            onClick={() => openEditModal(exercise)}
                            className="p-2 bg-blue-100 hover:bg-blue-200 dark:bg-blue-500/20 dark:hover:bg-blue-500/30 text-blue-600 dark:text-blue-400 rounded-lg transition"
                            title="Chỉnh sửa"
                          >
                            {t('exerciseManagement.editBtn')}
                          </button>
                          <button
                            onClick={() => handleDeleteExercise(exercise.id)}
                            className="p-2 bg-red-100 hover:bg-red-200 dark:bg-red-500/20 dark:hover:bg-red-500/30 text-red-600 dark:text-red-400 rounded-lg transition"
                            title="Xóa"
                          >
                            {t('exerciseManagement.deleteBtn')}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Pending Exercises Tab */}
        {activeTab === 'pending' && (
          <div className="bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {t('exerciseManagement.pendingTitle')}
              </h2>
              <button
                onClick={loadPendingExercises}
                className="text-teal-600 dark:text-teal-400 hover:underline"
              >
                {t('exerciseManagement.refresh')}
              </button>
            </div>

          {loading ? (
            <div className="text-center py-8">
              
              <p className="text-gray-500 dark:text-gray-400 mt-2">{t('exerciseManagement.loading')}</p>
            </div>
          ) : pendingList.length === 0 ? (
            <div className="text-center py-8">
              <span className="text-5xl"></span>
              <p className="text-gray-500 dark:text-gray-400 mt-2">
                {t('exerciseManagement.emptyApproved')} được upload
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {pendingList.map(pending => (
                <div
                  key={pending.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden hover:shadow-lg transition cursor-pointer"
                  onClick={() => navigate(`/pending-exercises/${pending.id}`)}
                >
                  {/* Thumbnail */}
                  <div className="aspect-video bg-gray-200 dark:bg-gray-800 relative">
                    {pending.thumbnail_path ? (
                      <img
                        src={`${API_BASE_URL}/${pending.thumbnail_path}`}
                        alt="Thumbnail"
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-xl font-bold text-gray-400">Video</span>
                      </div>
                    )}
                    <div className="absolute top-2 right-2">
                      {getStatusBadge(pending.status)}
                    </div>
                  </div>

                  {/* Info */}
                  <div className="p-4">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">
                      {pending.detected_type || t('exerciseManagement.analyzing')}
                    </h3>

                    {pending.confidence && pending.confidence > 0 && (
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {t('exerciseManagement.confidenceLabel')}
                        </span>
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-teal-500 to-cyan-500 h-2 rounded-full"
                            style={{ width: `${pending.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-semibold text-teal-600 dark:text-teal-400">
                          {Math.round(pending.confidence * 100)}%
                        </span>
                      </div>
                    )}

                    {pending.error_message && (
                      <p className="text-sm text-red-600 dark:text-red-400 truncate">
                        {pending.error_message}
                      </p>
                    )}

                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      {new Date(pending.created_at).toLocaleString('vi-VN')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editModalOpen && editingExercise && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {t('exerciseManagement.modalTitle')}
                </h2>
                <button
                  onClick={() => { setEditModalOpen(false); setEditingExercise(null); }}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  {t('exerciseManagement.cancelBtn')}
                </button>
              </div>

              {/* Angle Tracking Info (Read-only) */}
              <div className="bg-teal-50 dark:bg-teal-900/30 border border-teal-200 dark:border-teal-500/30 rounded-lg p-4 mb-6">
                <h3 className="text-lg font-semibold text-teal-700 dark:text-teal-400 mb-2">
                  {t('exerciseManagement.angleInfoTitle')}
                </h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">{t('exerciseManagement.baseTypeLabel')}</span>
                    <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                      {getBaseExerciseLabel(editingExercise.base_exercise_type)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">{t('exerciseManagement.primaryAngleLabel')}</span>
                    <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                      {editingExercise.angle_tracking?.primary_angles?.map(
                        a => editingExercise.angle_tracking.angle_names_vi[a] || a
                      ).join(', ')}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-teal-600 dark:text-teal-400 mt-2">
                  {editingExercise.angle_tracking?.description}
                </p>
              </div>

              <div className="space-y-4">
                {/* Name */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    {t('exerciseManagement.exerciseNameLabel')}
                  </label>
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    {t('exerciseManagement.exerciseDescLabel')}
                  </label>
                  <textarea
                    value={editForm.description}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    rows={3}
                  />
                </div>

                {/* Base Exercise Type */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    {t('exerciseManagement.baseTypeSelectLabel')}
                  </label>
                  <select
                    value={editForm.base_exercise_type}
                    onChange={(e) => setEditForm({ ...editForm, base_exercise_type: e.target.value })}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value="squat">{t('exerciseManagement.baseTypes.squat')}</option>
                    <option value="arm_raise">{t('exerciseManagement.baseTypes.arm_raise')}</option>
                    <option value="calf_raise">{t('exerciseManagement.baseTypes.calf_raise')}</option>
                    <option value="single_leg_stand">{t('exerciseManagement.baseTypes.single_leg_stand')}</option>
                  </select>
                </div>

                {/* Thresholds */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Down Threshold (°)
                    </label>
                    <input
                      type="number"
                      value={editForm.down_threshold}
                      onChange={(e) => setEditForm({ ...editForm, down_threshold: Number(e.target.value) })}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Up Threshold (°)
                    </label>
                    <input
                      type="number"
                      value={editForm.up_threshold}
                      onChange={(e) => setEditForm({ ...editForm, up_threshold: Number(e.target.value) })}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Hysteresis (°)
                    </label>
                    <input
                      type="number"
                      value={editForm.hysteresis}
                      onChange={(e) => setEditForm({ ...editForm, hysteresis: Number(e.target.value) })}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>

                {/* Target & Duration */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      {t('exerciseManagement.targetRepsLabel')}
                    </label>
                    <input
                      type="number"
                      value={editForm.target_reps}
                      onChange={(e) => setEditForm({ ...editForm, target_reps: Number(e.target.value) })}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      {t('exerciseManagement.durationLabel')}
                    </label>
                    <input
                      type="number"
                      value={editForm.duration_seconds}
                      onChange={(e) => setEditForm({ ...editForm, duration_seconds: Number(e.target.value) })}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>

                {/* Difficulty */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    {t('exerciseManagement.difficultyLabel')}
                  </label>
                  <select
                    value={editForm.difficulty_level}
                    onChange={(e) => setEditForm({ ...editForm, difficulty_level: e.target.value })}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value="easy">{t('exerciseManagement.difficulty.easy')}</option>
                    <option value="medium">{t('exerciseManagement.difficulty.medium')}</option>
                    <option value="hard">{t('exerciseManagement.difficulty.hard')}</option>
                  </select>
                </div>

                {/* Existing Angle Rules (Read-only info) */}
                {editingExercise.angle_rules?.length > 0 && (
                  <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-500/30 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-orange-700 dark:text-orange-400 mb-2">
                      {t('exerciseManagement.existingRulesTitle')}
                    </h4>
                    <div className="space-y-2">
                      {editingExercise.angle_rules.map((rule, idx) => (
                        <div key={idx} className="text-sm text-gray-700 dark:text-gray-300">
                          <span className="font-semibold">{rule.angle_name}:</span>
                          <span className="ml-2">
                            {rule.min_angle !== null && `Min: ${rule.min_angle}°`}
                            {rule.min_angle !== null && rule.max_angle !== null && ' | '}
                            {rule.max_angle !== null && `Max: ${rule.max_angle}°`}
                          </span>
                          {rule.error_message && (
                            <span className="ml-2 text-orange-600 dark:text-orange-400">
                              → {rule.error_message}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-4 mt-6">
                <button
                  onClick={handleSaveEdit}
                  disabled={saving || !editForm.name}
                  className="flex-1 bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600 text-white font-bold py-3 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
                >
                  {saving ? t('exerciseManagement.saving') : t('exerciseManagement.saveBtn')}
                </button>
                <button
                  onClick={() => { setEditModalOpen(false); setEditingExercise(null); }}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-bold py-3 rounded-lg transition"
                >
                  {t('exerciseManagement.cancelBtn')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
