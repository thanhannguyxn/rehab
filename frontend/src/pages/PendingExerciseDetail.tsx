import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { API_URL, API_BASE_URL } from '../utils/config';

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

  useEffect(() => {
    loadPendingDetail();
  }, [id]);

  const loadPendingDetail = async () => {
    try {
      const token = sessionStorage.getItem('token');
      const response = await fetch(`${API_URL}/doctor/exercises/pending/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setPending(data);
        // Initialize edit form with detected values
        setEditName(data.manual_exercise_name || data.detected_exercise_type || '');
        setEditDescription(data.manual_description || data.movement_signature?.description || '');
        setEditDownThreshold(data.detected_thresholds?.down_threshold || '');
        setEditUpThreshold(data.detected_thresholds?.up_threshold || '');
      } else {
        alert('Không tìm thấy bài tập');
        navigate('/exercise-management');
      }
    } catch (error) {
      console.error('Error loading pending detail:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!window.confirm('Bạn có chắc muốn duyệt bài tập này?')) return;

    setProcessing(true);
    try {
      const token = sessionStorage.getItem('token');

      // First update manual values if changed
      await fetch(`${API_URL}/doctor/exercises/pending/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          manual_exercise_name: editName,
          manual_description: editDescription,
          manual_thresholds: {
            down_threshold: editDownThreshold || null,
            up_threshold: editUpThreshold || null,
            hysteresis: 5.0
          }
        })
      });

      // Then approve
      const response = await fetch(`${API_URL}/doctor/exercises/approve/${id}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Thành công! Bài tập "${data.exercise_id}" đã được thêm vào hệ thống.`);
        navigate('/exercise-management');
      } else {
        const error = await response.json();
        alert(error.detail || 'Lỗi khi duyệt bài tập');
      }
    } catch (error) {
      console.error('Error approving:', error);
      alert('Lỗi khi duyệt bài tập');
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!window.confirm('Bạn có chắc muốn xóa bài tập này? Video sẽ bị xóa vĩnh viễn.')) return;

    setProcessing(true);
    try {
      const token = sessionStorage.getItem('token');
      const response = await fetch(`${API_URL}/doctor/exercises/pending/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('Đã xóa bài tập');
        navigate('/exercise-management');
      } else {
        const error = await response.json();
        alert(error.detail || 'Lỗi khi xóa');
      }
    } catch (error) {
      console.error('Error rejecting:', error);
      alert('Lỗi khi xóa');
    } finally {
      setProcessing(false);
    }
  };

  const handleReanalyze = async () => {
    if (!window.confirm('Bạn có muốn phân tích lại video này?')) return;

    setProcessing(true);
    try {
      const token = sessionStorage.getItem('token');
      const response = await fetch(`${API_URL}/doctor/exercises/reanalyze/${id}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('Đang phân tích lại video...');
        loadPendingDetail();
      } else {
        const error = await response.json();
        alert(error.detail || 'Lỗi');
      }
    } catch (error) {
      console.error('Error re-analyzing:', error);
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-4xl text-blue-500 mb-4">
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
      'UPLOADING': 'bg-blue-500',
      'PROCESSING': 'bg-yellow-500',
      'PENDING': 'bg-green-500',
      'APPROVED': 'bg-teal-500',
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
            <h1 className="text-4xl font-black bg-gradient-to-r from-teal-500 to-cyan-500 bg-clip-text text-transparent">
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
          <div className="bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl">
            <h2 className="text-xl font-bold mb-4">Video</h2>
            <div className="aspect-video bg-gray-200 dark:bg-gray-800 rounded-lg overflow-hidden">
              <video
                src={`${API_BASE_URL}/${pending.video_path}`}
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
            <div className="bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl">
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
                  <div className="animate-spin text-4xl text-blue-500 mb-4 flex justify-center">
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
                    <p className="text-2xl font-bold text-teal-600 dark:text-teal-400">
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
                            className="bg-gradient-to-r from-teal-500 to-cyan-500 h-3 rounded-full"
                            style={{ width: `${pending.confidence_score * 100}%` }}
                          />
                        </div>
                        <span className="text-lg font-bold text-teal-600 dark:text-teal-400">
                          {Math.round(pending.confidence_score * 100)}%
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Tracking Logic Info */}
                  {pending.movement_signature?.tracking_logic && (
                    <div className="mb-4 bg-teal-50 dark:bg-teal-900/30 border border-teal-200 dark:border-teal-500/30 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-teal-700 dark:text-teal-400 mb-3">
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
                        <div className="mt-4 pt-3 border-t border-teal-200 dark:border-teal-500/30">
                          <h4 className="text-sm font-semibold text-teal-600 dark:text-teal-400 mb-2">
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
                                      : 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400'
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
                            className="px-2 py-1 bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400 rounded text-sm"
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
              <div className="bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-xl">
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
                  className="flex-1 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-bold py-4 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
                >
                  {processing ? 'Đang xử lý...' : 'Duyệt và Thêm vào Hệ Thống'}
                </button>
                <button
                  onClick={handleReject}
                  disabled={processing}
                  className="flex-1 bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white font-bold py-4 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
                >
                  {processing ? 'Đang xử lý...' : 'Từ Chối và Xóa'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
