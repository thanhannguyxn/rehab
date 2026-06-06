import { useState, useMemo } from 'react';
import { authAPI } from '../utils/api';

interface SuccessData {
  username: string;
  plain_password: string;
  full_name: string;
  email?: string;
  email_sent: boolean;
}

interface Props {
  onClose: () => void;
  onSuccess: (data: SuccessData) => void;
}

function removeVietnameseTones(str: string) {
  return str
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D');
}

function suggestUsername(fullName: string) {
  return removeVietnameseTones(fullName)
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '.')
    .replace(/[^a-z0-9.]/g, '');
}

const MOBILITY_OPTIONS = [
  { value: 'beginner', label: 'Mới bắt đầu' },
  { value: 'intermediate', label: 'Trung bình' },
  { value: 'advanced', label: 'Nâng cao' },
];

const INJURY_OPTIONS = [
  { value: '', label: 'Chọn loại chấn thương' },
  { value: 'knee_pain', label: 'Đau khớp gối' },
  { value: 'shoulder_pain', label: 'Đau vai' },
  { value: 'back_pain', label: 'Đau lưng' },
  { value: 'balance_issue', label: 'Vấn đề cân bằng' },
  { value: 'hip_pain', label: 'Đau hông' },
  { value: 'ankle_pain', label: 'Đau cổ chân' },
  { value: 'other', label: 'Khác' },
];

const MEDICAL_OPTIONS = [
  { value: 'knee_arthritis', label: 'Viêm khớp gối' },
  { value: 'shoulder_pain', label: 'Đau vai' },
  { value: 'back_pain', label: 'Đau lưng' },
  { value: 'osteoporosis', label: 'Loãng xương' },
  { value: 'diabetes', label: 'Tiểu đường' },
  { value: 'heart_disease', label: 'Bệnh tim mạch' },
  { value: 'hypertension', label: 'Cao huyết áp' },
  { value: 'stroke_recovery', label: 'Phục hồi sau đột quỵ' },
];

export const CreatePatientModal = ({ onClose, onSuccess }: Props) => {
  const [form, setForm] = useState({
    full_name: '',
    username: '',
    email: '',
    age: '',
    gender: '',
    height_cm: '',
    weight_kg: '',
    injury_type: '',
    medical_conditions: [] as string[],
    mobility_level: 'beginner',
    pain_level: '3',
    doctor_notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const bmi = useMemo(() => {
    const h = parseFloat(form.height_cm);
    const w = parseFloat(form.weight_kg);
    if (h > 0 && w > 0) {
      return (w / Math.pow(h / 100, 2)).toFixed(1);
    }
    return null;
  }, [form.height_cm, form.weight_kg]);

  const bmiCategory = (val: string | null) => {
    if (!val) return null;
    const n = parseFloat(val);
    if (n < 18.5) return { label: 'Thiếu cân', color: 'text-blue-600' };
    if (n < 25) return { label: 'Bình thường', color: 'text-green-600' };
    if (n < 30) return { label: 'Thừa cân', color: 'text-yellow-600' };
    return { label: 'Béo phì', color: 'text-red-600' };
  };

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const val = e.target.value;
    setForm(prev => {
      const next = { ...prev, [field]: val };
      if (field === 'full_name' && !prev.username) {
        next.username = suggestUsername(val);
      }
      return next;
    });
  };

  const toggleMedicalCondition = (condition: string) => {
    setForm(prev => ({
      ...prev,
      medical_conditions: prev.medical_conditions.includes(condition)
        ? prev.medical_conditions.filter(c => c !== condition)
        : [...prev.medical_conditions, condition]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.full_name.trim() || !form.username.trim()) {
      setError('Họ tên và tên đăng nhập là bắt buộc.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const result = await authAPI.createPatient({
        full_name: form.full_name.trim(),
        username: form.username.trim(),
        email: form.email.trim() || undefined,
        age: form.age ? parseInt(form.age) : undefined,
        gender: form.gender || undefined,
        height_cm: form.height_cm ? parseFloat(form.height_cm) : undefined,
        weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : undefined,
        injury_type: form.injury_type || undefined,
        medical_conditions: form.medical_conditions.length > 0 ? JSON.stringify(form.medical_conditions) : undefined,
        mobility_level: form.mobility_level,
        pain_level: parseInt(form.pain_level),
        doctor_notes: form.doctor_notes.trim() || undefined,
      });
      onSuccess({
        username: result.user.username,
        plain_password: result.plain_password,
        full_name: form.full_name.trim(),
        email: form.email.trim() || undefined,
        email_sent: result.email_sent,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Có lỗi xảy ra, vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between rounded-t-2xl z-10">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Tạo Tài Khoản Bệnh Nhân</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Mật khẩu sẽ được tạo tự động và gửi qua email</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 transition">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Section 1: Thông tin tài khoản */}
          <div>
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Thông tin tài khoản</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Họ và tên <span className="text-red-500">*</span></label>
                <input type="text" value={form.full_name} onChange={set('full_name')} required
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0284c7] focus:border-transparent text-sm"
                  placeholder="Nguyễn Văn An" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tên đăng nhập <span className="text-red-500">*</span></label>
                <input type="text" value={form.username} onChange={set('username')} required
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0284c7] focus:border-transparent text-sm font-mono"
                  placeholder="nguyen.van.an" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email <span className="text-gray-400">(để gửi thông tin đăng nhập)</span>
                </label>
                <input type="email" value={form.email} onChange={set('email')}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0284c7] focus:border-transparent text-sm"
                  placeholder="benhnhan@email.com" />
              </div>
            </div>
          </div>

          {/* Section 2: Thể trạng */}
          <div>
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Thể trạng</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tuổi</label>
                <input type="number" value={form.age} onChange={set('age')} min="1" max="120"
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0284c7] focus:border-transparent text-sm"
                  placeholder="65" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Giới tính</label>
                <select value={form.gender} onChange={set('gender')}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0284c7] focus:border-transparent text-sm">
                  <option value="">Chọn</option>
                  <option value="male">Nam</option>
                  <option value="female">Nữ</option>
                  <option value="other">Khác</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Chiều cao (cm)</label>
                <input type="number" value={form.height_cm} onChange={set('height_cm')} min="50" max="250" step="0.1"
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0284c7] focus:border-transparent text-sm"
                  placeholder="165" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cân nặng (kg)</label>
                <input type="number" value={form.weight_kg} onChange={set('weight_kg')} min="10" max="300" step="0.1"
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0284c7] focus:border-transparent text-sm"
                  placeholder="60" />
              </div>
            </div>
            {bmi && (
              <div className="mt-3 flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">BMI:</span>
                <span className="text-lg font-bold text-gray-900 dark:text-white">{bmi}</span>
                {bmiCategory(bmi) && (
                  <span className={`text-sm font-medium ${bmiCategory(bmi)!.color}`}>{bmiCategory(bmi)!.label}</span>
                )}
              </div>
            )}
          </div>

          {/* Section 3: Bệnh lý */}
          <div>
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Bệnh lý & Phục hồi</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Loại chấn thương</label>
                <select value={form.injury_type} onChange={set('injury_type')}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0284c7] focus:border-transparent text-sm">
                  {INJURY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mức độ vận động</label>
                <select value={form.mobility_level} onChange={set('mobility_level')}
                  className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0284c7] focus:border-transparent text-sm">
                  {MOBILITY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Tình trạng bệnh lý</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {MEDICAL_OPTIONS.map((condition) => (
                    <label
                      key={condition.value}
                      className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
                        form.medical_conditions.includes(condition.value)
                          ? 'bg-blue-50 border-[#0284c7] dark:bg-[#0284c7]/20 dark:border-[#0284c7]'
                          : 'bg-white border-gray-300 dark:bg-gray-800 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-750'
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="w-4 h-4 text-[#0284c7] border-gray-300 rounded focus:ring-[#0369a1] dark:border-gray-600 dark:bg-gray-700"
                        checked={form.medical_conditions.includes(condition.value)}
                        onChange={() => toggleMedicalCondition(condition.value)}
                      />
                      <span className="ml-3 text-sm font-medium text-gray-700 dark:text-gray-300 select-none">
                        {condition.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Mức độ đau: <span className="font-bold text-[#0284c7]">{form.pain_level}/10</span>
                </label>
                <input type="range" min="0" max="10" value={form.pain_level} onChange={set('pain_level')}
                  className="w-full accent-[#0284c7]" />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>Không đau</span><span>Đau vừa</span><span>Rất đau</span>
                </div>
              </div>
            </div>
          </div>

          {/* Section 4: Ghi chú */}
          <div>
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Ghi chú bác sĩ</h3>
            <textarea value={form.doctor_notes} onChange={set('doctor_notes')} rows={3}
              className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0284c7] focus:border-transparent text-sm resize-none"
              placeholder="Ghi chú nội bộ về bệnh nhân, chỉ bác sĩ thấy..." />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition text-sm">
              Hủy
            </button>
            <button type="submit" disabled={loading}
              className="flex-1 px-4 py-3 bg-[#0284c7] hover:bg-[#0369a1] text-white font-bold rounded-lg transition text-sm disabled:opacity-50 flex items-center justify-center gap-2">
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Đang tạo...
                </>
              ) : 'Tạo Tài Khoản'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};


interface SuccessPopupProps {
  data: SuccessData;
  onClose: () => void;
}

export const SuccessCredentialsPopup = ({ data, onClose }: SuccessPopupProps) => {
  const [copiedUser, setCopiedUser] = useState(false);
  const [copiedPass, setCopiedPass] = useState(false);

  const copy = (text: string, setFlag: (v: boolean) => void) => {
    navigator.clipboard.writeText(text);
    setFlag(true);
    setTimeout(() => setFlag(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md p-6">
        <div className="text-center mb-5">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
            <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Tạo tài khoản thành công!</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">{data.full_name}</p>
        </div>

        <div className="space-y-3 mb-5">
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 flex items-center justify-between gap-2">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Tên đăng nhập</p>
              <p className="font-mono font-bold text-gray-900 dark:text-white">{data.username}</p>
            </div>
            <button onClick={() => copy(data.username, setCopiedUser)}
              className="px-3 py-1.5 text-xs rounded-lg bg-[#0284c7] hover:bg-[#0369a1] text-white font-medium transition min-w-[60px]">
              {copiedUser ? '✓ Đã copy' : 'Copy'}
            </button>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 flex items-center justify-between gap-2">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Mật khẩu</p>
              <p className="font-mono font-bold text-gray-900 dark:text-white">{data.plain_password}</p>
            </div>
            <button onClick={() => copy(data.plain_password, setCopiedPass)}
              className="px-3 py-1.5 text-xs rounded-lg bg-[#0284c7] hover:bg-[#0369a1] text-white font-medium transition min-w-[60px]">
              {copiedPass ? '✓ Đã copy' : 'Copy'}
            </button>
          </div>
        </div>

        {data.email ? (
          data.email_sent ? (
            <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-sm text-green-700 dark:text-green-400 mb-4">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Đã gửi thông tin đến <strong className="ml-1">{data.email}</strong>
            </div>
          ) : (
            <div className="flex items-center gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg text-sm text-yellow-700 dark:text-yellow-400 mb-4">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Không thể gửi email. Vui lòng lưu lại thông tin đăng nhập bên trên.
            </div>
          )
        ) : (
          <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-[#0284c7] dark:text-blue-400 mb-4">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Chưa nhập email, hãy gửi thông tin đăng nhập thủ công cho bệnh nhân.
          </div>
        )}

        <button onClick={onClose}
          className="w-full py-3 bg-[#0284c7] hover:bg-[#0369a1] text-white font-bold rounded-lg transition">
          Đóng
        </button>
      </div>
    </div>
  );
};
