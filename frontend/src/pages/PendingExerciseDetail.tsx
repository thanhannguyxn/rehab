import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { API_BASE_URL } from '../utils/config';
import { exerciseManagementAPI } from '../utils/api';

interface AngleRule {
  angle_name: string;
  min_angle?: number;
  max_angle?: number;
  error_message?: string;
  error_severity?: string;
}

interface TrackingLogic {
  base_exercise_type?: string;
  primary_angles?: string[];
  state_sequence?: string[];
  rep_completion_rule?: string;
  angle_rules?: AngleRule[];
}

interface PendingExerciseDetail {
  id: number;
  video_path: string;
  thumbnail_path?: string;
  video_duration_seconds?: number;
  detected_exercise_type?: string;
  detected_thresholds: {
    down_threshold?: number;
    up_threshold?: number;
    hysteresis?: number;
  };
  movement_signature: {
    description?: string;
    instructions?: string[];
    warnings?: string[];
    tracking_logic?: TrackingLogic;
    primary_joints?: string[];
  };
  confidence_score?: number;
  manual_exercise_name?: string;
  manual_description?: string;
  status: string;
  error_message?: string;
  created_at: string;
}

export const PendingExerciseDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [pending, setPending] = useState<PendingExerciseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  // Edit form state
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editDownThreshold, setEditDownThreshold] = useState<number | ''>('');
  const [editUpThreshold, setEditUpThreshold] = useState<number | ''>('');

  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  const [confirmAction, setConfirmAction] = useState<{ label: string; message: string; onConfirm: () => void } | null>(null);

  const showToast = (type: 'success' | 'error' | 'info', text: string) => {
    setToast({ type, text });
    setTimeout(() => setToast(null), 3500);
  };

  const didFetch = useRef(false);

  useEffect(() => {
    if (didFetch.current) return;
    didFetch.current = true;
    loadPendingDetail();
  }, [id]);

  const loadPendingDetail = async () => {
    try {
      const data = await exerciseManagementAPI.getPendingDetail(id!) as PendingExerciseDetail;
      setPending(data);
      setEditName(data.manual_exercise_name || data.detected_exercise_type || '');
      setEditDescription(data.manual_description || data.movement_signature?.description || '');
      setEditDownThreshold(data.detected_thresholds?.down_threshold || '');
      setEditUpThreshold(data.detected_thresholds?.up_threshold || '');
    } catch (error) {
      console.error('Error loading pending detail:', error);
      showToast('error', 'Không tìm thấy bài tập');
      navigate('/exercise-management');
    } finally {
      setLoading(false);
    }
  };

  const doApprove = async () => {
    setProcessing(true);
    try {
      await exerciseManagementAPI.updatePending(id!, {
        manual_exercise_name: editName,
        manual_description: editDescription,
        manual_thresholds: {
          down_threshold: editDownThreshold || null,
          up_threshold: editUpThreshold || null,
          hysteresis: 5.0,
        },
      });
      const data = await exerciseManagementAPI.approve(id!) as { exercise_id: string };
      showToast('success', `Đã duyệt bài tập "${data.exercise_id}" thành công!`);
      setTimeout(() => navigate('/exercise-management'), 1500);
    } catch (error: unknown) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast('error', detail || 'Lỗi khi duyệt bài tập');
    } finally {
      setProcessing(false);
    }
  };

  const doReject = async () => {
    setProcessing(true);
    try {
      await exerciseManagementAPI.deletePending(id!);
      showToast('success', 'Đã xóa bài tập');
      setTimeout(() => navigate('/exercise-management'), 1500);
    } catch (error: unknown) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast('error', detail || 'Lỗi khi xóa');
    } finally {
      setProcessing(false);
    }
  };

  const doReanalyze = async () => {
    setProcessing(true);
    try {
      await exerciseManagementAPI.reanalyze(id!);
      showToast('info', 'Đang phân tích lại video...');
      loadPendingDetail();
    } catch (error: unknown) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast('error', detail || 'Lỗi');
    } finally {
      setProcessing(false);
    }
  };

  const handleApprove = () => setConfirmAction({
    label: 'Duyệt bài tập',
    message: 'Bạn có chắc muốn duyệt bài tập này?',
    onConfirm: doApprove,
  });

  const handleReject = () => setConfirmAction({
    label: 'Xóa bài tập',
    message: 'Bạn có chắc muốn xóa bài tập này? Video sẽ bị xóa vĩnh viễn.',
    onConfirm: doReject,
  });

  const handleReanalyze = () => setConfirmAction({
    label: 'Phân tích lại',
    message: 'Bạn có muốn phân tích lại video này?',
    onConfirm: doReanalyze,
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-4xl text-[#0369a1] mb-4">
            <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <p className="text-gray-500 dark:text-gray-400 mt-4">Đang tải...</p>
        </div>
      </div>
    );
  }

  if (!pending) {
    return null;
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      'UPLOADING': 'bg-[#0369a1]',
      'PROCESSING': 'bg-yellow-500',
      'PENDING': 'bg-green-500',
      'APPROVED': 'bg-[#0369a1]',
      'REJECTED': 'bg-gray-500',
      'ERROR': 'bg-red-500'
    };
    const labels: Record<string, string> = {
      'UPLOADING': 'Đang tải',
      'PROCESSING': 'Đang xử lý',
      'PENDING': 'Chờ duyệt',
      'APPROVED': 'Đã duyệt',
      'REJECTED': 'Đã từ chối',
      'ERROR': 'Lỗi'
    };
    return (
      <span className={`px-3 py-1 rounded-full text-white font-semibold ${styles[status] || 'bg-gray-500'}`}>
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-black text-gray-900 dark:text-white transition-colors duration-300">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-black text-[#0369a1]">
              Chi Tiết Bài Tập
            </h1>
            <div className="flex items-center gap-4 mt-2">
              {getStatusBadge(pending.status)}
              <span className="text-gray-500 dark:text-gray-400">
                {new Date(pending.created_at).toLocaleString('vi-VN')}
              </span>
            </div>
          </div>
          <button
            onClick={() => navigate('/exercise-management')}
            className="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-bold py-2 px-4 rounded-lg transition"
          >
            Quay lại
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: Video Preview */}
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl">
            <h2 className="text-xl font-bold mb-4">Video</h2>
            <div className="aspect-video bg-gray-200 dark:bg-gray-800 rounded-lg overflow-hidden">
              <video
                src={pending.video_path?.startsWith('https://') ? pending.video_path : `${API_BASE_URL}/${pending.video_path}`}
                controls
                className="w-full h-full object-contain"
              />
            </div>
            {pending.video_duration_seconds && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                Thời lượng: {pending.video_duration_seconds} giây
              </p>
            )}
          </div>

          {/* Right: Analysis Results */}
          <div className="space-y-6">
            {/* AI Analysis */}
            <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl">
              <h2 className="text-xl font-bold mb-4">Kết Quả Phân Tích AI</h2>

              {pending.status === 'ERROR' && (
                <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-500/30 rounded-lg p-4 mb-4">
                  <p className="text-red-700 dark:text-red-400 font-semibold">Lỗi phân tích:</p>
                  <p className="text-red-600 dark:text-red-300">{pending.error_message}</p>
                  <button
                    onClick={handleReanalyze}
                    disabled={processing}
                    className="mt-2 bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50"
                  >
                    Phân tích lại
                  </button>
                </div>
              )}

              {pending.status === 'PROCESSING' && (
                <div className="text-center py-8">
                  <div className="animate-spin text-4xl text-[#0369a1] mb-4 flex justify-center">
                    <svg className="w-10 h-10 inline-block" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                  <p className="text-gray-500 dark:text-gray-400">Đang phân tích video...</p>
                  <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                    Quá trình này có thể mất 10-30 giây
                  </p>
                </div>
              )}

              {(pending.status === 'PENDING' || pending.status === 'APPROVED') && (
                <>
                  {/* Detected Type */}
                  <div className="mb-4">
                    <label className="block text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
                      Loại bài tập phát hiện:
                    </label>
                    <p className="text-2xl font-bold text-[#0284c7] dark:text-blue-600">
                      {pending.detected_exercise_type || 'Không xác định'}
                    </p>
                  </div>

                  {/* Confidence */}
                  {pending.confidence_score !== undefined && (
                    <div className="mb-4">
                      <label className="block text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
                        Độ tin cậy:
                      </label>
                      <div className="flex items-center gap-4">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                          <div
                            className="bg-[#0369a1] h-3 rounded-full"
                            style={{ width: `${pending.confidence_score * 100}%` }}
                          />
                        </div>
                        <span className="text-lg font-bold text-[#0284c7] dark:text-blue-600">
                          {Math.round(pending.confidence_score * 100)}%
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Tracking Logic Info */}
                  {pending.movement_signature?.tracking_logic && (
                    <div className="mb-4 bg-blue-50 dark:bg-[#075985]/30 border border-blue-200 dark:border-[#0369a1]/30 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-[#0284c7] dark:text-blue-600 mb-3">
                        Thông Tin Góc Khớp Theo Dõi
                      </h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Loại cơ sở:</span>
                          <span className="font-semibold text-gray-900 dark:text-white">
                            {pending.movement_signature.tracking_logic.base_exercise_type || 'N/A'}
                          </span>
                        </div>
                        {pending.movement_signature.tracking_logic.primary_angles && (
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Góc theo dõi:</span>
                            <span className="font-semibold text-gray-900 dark:text-white">
                              {pending.movement_signature.tracking_logic.primary_angles.join(', ')}
                            </span>
                          </div>
                        )}
                        {pending.movement_signature.tracking_logic.state_sequence && (
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Trình tự trạng thái:</span>
                            <span className="font-semibold text-gray-900 dark:text-white">
                              {pending.movement_signature.tracking_logic.state_sequence.join(' → ')}
                            </span>
                          </div>
                        )}
                        {pending.movement_signature.tracking_logic.rep_completion_rule && (
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Quy tắc đếm rep:</span>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {pending.movement_signature.tracking_logic.rep_completion_rule}
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Angle Rules from AI */}
                      {pending.movement_signature.tracking_logic.angle_rules &&
                       pending.movement_signature.tracking_logic.angle_rules.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-blue-200 dark:border-[#0369a1]/30">
                          <h4 className="text-sm font-semibold text-[#0284c7] dark:text-blue-600 mb-2">
                            Quy tắc phát hiện lỗi (AI):
                          </h4>
                          <div className="space-y-2">
                            {pending.movement_signature.tracking_logic.angle_rules.map((rule, idx) => (
                              <div key={idx} className="text-xs bg-white dark:bg-gray-800 rounded p-2">
                                <div className="flex items-center gap-2">
                                  <span className="font-semibold text-gray-700 dark:text-gray-300">
                                    {rule.angle_name}:
                                  </span>
                                  <span className="text-gray-600 dark:text-gray-400">
                                    {rule.min_angle !== undefined && `Min: ${rule.min_angle}°`}
                                    {rule.min_angle !== undefined && rule.max_angle !== undefined && ' | '}
                                    {rule.max_angle !== undefined && `Max: ${rule.max_angle}°`}
                                  </span>
                                  <span className={`px-1.5 py-0.5 rounded text-xs ${
                                    rule.error_severity === 'high'
                                      ? 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'
                                      : rule.error_severity === 'medium'
                                      ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400'
                                      : 'bg-blue-100 text-[#0284c7] dark:bg-[#0369a1]/20 dark:text-blue-600'
                                  }`}>
                                    {rule.error_severity || 'medium'}
                                  </span>
                                </div>
                                {rule.error_message && (
                                  <p className="text-orange-600 dark:text-orange-400 mt-1">
                                    → {rule.error_message}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Primary Joints */}
                  {pending.movement_signature?.primary_joints &&
                   pending.movement_signature.primary_joints.length > 0 && (
                    <div className="mb-4">
                      <label className="block text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
                        Khớp chính:
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {pending.movement_signature.primary_joints.map((joint, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-blue-100 text-[#0284c7] dark:bg-[#0369a1]/20 dark:text-blue-600 rounded text-sm"
                          >
                            {joint}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Thresholds */}
                  {pending.detected_thresholds && (
                    <div className="mb-4 grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
                          Down Threshold:
                        </label>
                        <p className="text-lg font-bold">
                          {pending.detected_thresholds.down_threshold?.toFixed(1) || '-'}°
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
                          Up Threshold:
                        </label>
                        <p className="text-lg font-bold">
                          {pending.detected_thresholds.up_threshold?.toFixed(1) || '-'}°
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Description */}
                  {pending.movement_signature?.description && (
                    <div className="mb-4">
                      <label className="block text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
                        Mô tả:
                      </label>
                      <p className="text-gray-700 dark:text-gray-300">
                        {pending.movement_signature.description}
                      </p>
                    </div>
                  )}

                  {/* Instructions */}
                  {pending.movement_signature?.instructions && pending.movement_signature.instructions.length > 0 && (
                    <div className="mb-4">
                      <label className="block text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
                        Hướng dẫn:
                      </label>
                      <ol className="list-decimal list-inside text-gray-700 dark:text-gray-300 space-y-1">
                        {pending.movement_signature.instructions.map((step, idx) => (
                          <li key={idx}>{step}</li>
                        ))}
                      </ol>
                    </div>
                  )}

                  {/* Warnings */}
                  {pending.movement_signature?.warnings && pending.movement_signature.warnings.length > 0 && (
                    <div className="bg-orange-50 dark:bg-orange-900/30 border border-orange-200 dark:border-orange-500/30 rounded-lg p-3">
                      <p className="text-orange-700 dark:text-orange-400 font-semibold mb-1">Cảnh báo:</p>
                      <ul className="list-disc list-inside text-orange-600 dark:text-orange-300 text-sm">
                        {pending.movement_signature.warnings.map((warning, idx) => (
                          <li key={idx}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Manual Edit Form */}
            {(pending.status === 'PENDING' || pending.status === 'ERROR') && (
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl">
                <h2 className="text-xl font-bold mb-4">Chỉnh Sửa (Tuỳ chọn)</h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
                      Tên bài tập:
                    </label>
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      placeholder="VD: Squat, Nâng Tay, ..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
                      Mô tả:
                    </label>
                    <textarea
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      rows={3}
                      placeholder="Mô tả bài tập..."
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
                        Down Threshold (°):
                      </label>
                      <input
                        type="number"
                        value={editDownThreshold}
                        onChange={(e) => setEditDownThreshold(e.target.value ? Number(e.target.value) : '')}
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
                        Up Threshold (°):
                      </label>
                      <input
                        type="number"
                        value={editUpThreshold}
                        onChange={(e) => setEditUpThreshold(e.target.value ? Number(e.target.value) : '')}
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            {(pending.status === 'PENDING' || pending.status === 'ERROR') && (
              <div className="flex gap-4">
                <button
                  onClick={handleApprove}
                  disabled={processing || !editName}
                  className="flex-1 bg-green-500 hover:bg-green-600 text-white font-bold py-4 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
                >
                  {processing ? 'Đang xử lý...' : 'Duyệt và Thêm vào Hệ Thống'}
                </button>
                <button
                  onClick={handleReject}
                  disabled={processing}
                  className="flex-1 bg-red-500 hover:bg-red-600 text-white font-bold py-4 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
                >
                  {processing ? 'Đang xử lý...' : 'Từ Chối và Xóa'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Confirm Modal */}
      {confirmAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-yellow-600 dark:text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="font-bold text-gray-900 dark:text-white">{confirmAction.label}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{confirmAction.message}</p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => { confirmAction.onConfirm(); setConfirmAction(null); }}
                className="flex-1 bg-[#0369a1] hover:bg-[#0284c7] text-white font-semibold py-2.5 rounded-xl transition"
              >
                Xác nhận
              </button>
              <button
                onClick={() => setConfirmAction(null)}
                className="flex-1 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 font-semibold py-2.5 rounded-xl transition"
              >
                Hủy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className="fixed top-6 right-6 z-50 animate-slide-in-right">
          <div className={`flex items-center gap-3 px-5 py-4 rounded-xl shadow-2xl border-l-4 min-w-[300px] bg-white dark:bg-gray-800 ${
            toast.type === 'success' ? 'border-green-500' : toast.type === 'error' ? 'border-red-500' : 'border-blue-500'
          }`}>
            <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
              toast.type === 'success' ? 'bg-green-100 dark:bg-green-900/40' : toast.type === 'error' ? 'bg-red-100 dark:bg-red-900/40' : 'bg-blue-100 dark:bg-blue-900/40'
            }`}>
              {toast.type === 'success' ? (
                <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
              ) : toast.type === 'error' ? (
                <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
              ) : (
                <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" /></svg>
              )}
            </div>
            <p className="flex-1 font-medium text-gray-900 dark:text-white text-sm">{toast.text}</p>
            <button onClick={() => setToast(null)} className="text-gray-400 hover:text-gray-600 transition">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
