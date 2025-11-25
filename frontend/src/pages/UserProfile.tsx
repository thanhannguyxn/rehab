import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProfileData {
  age: number | '';
  gender: string;
  height_cm: number | '';
  weight_kg: number | '';
  medical_conditions: string[];
  mobility_level: string;
  pain_level: number;
}

export const UserProfile = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [activeTab, setActiveTab] = useState<'basic' | 'medical' | 'mobility'>('basic');
  
  const [profile, setProfile] = useState<ProfileData>({
    age: '',
    gender: 'male',
    height_cm: '',
    weight_kg: '',
    medical_conditions: [],
    mobility_level: 'beginner',
    pain_level: 0,
  });

  const medicalOptions = [
    { value: 'knee_arthritis', label: 'Viêm khớp gối' },
    { value: 'shoulder_pain', label: 'Đau vai' },
    { value: 'back_pain', label: 'Đau lưng' },
    { value: 'osteoporosis', label: 'Loãng xương' },
    { value: 'diabetes', label: 'Tiểu đường' },
    { value: 'heart_disease', label: 'Bệnh tim' },
    { value: 'hypertension', label: 'Cao huyết áp' },
    { value: 'stroke_recovery', label: 'Phục hồi sau đột quỵ' },
  ];

  useEffect(() => {
    loadProfile();
  }, []);

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage(null);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  const loadProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/profile/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProfile({
          age: data.age || '',
          gender: data.gender || 'male',
          height_cm: data.height_cm || '',
          weight_kg: data.weight_kg || '',
          medical_conditions: data.medical_conditions ? JSON.parse(data.medical_conditions) : [],
          mobility_level: data.mobility_level || 'beginner',
          pain_level: data.pain_level || 0,
        });
      }
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateBMI = () => {
    if (profile.height_cm && profile.weight_kg) {
      const heightM = Number(profile.height_cm) / 100;
      const bmi = Number(profile.weight_kg) / (heightM * heightM);
      return bmi.toFixed(1);
    }
    return null;
  };

  const getBMICategory = (bmi: number) => {
    if (bmi < 18.5) return { text: 'Thiếu cân', color: 'text-yellow-600 dark:text-yellow-400' };
    if (bmi < 25) return { text: 'Bình thường', color: 'text-green-600 dark:text-green-400' };
    if (bmi < 30) return { text: 'Thừa cân', color: 'text-orange-600 dark:text-orange-400' };
    return { text: 'Béo phì', color: 'text-red-600 dark:text-red-400' };
  };

  const handleMedicalConditionToggle = (condition: string) => {
    setProfile(prev => ({
      ...prev,
      medical_conditions: prev.medical_conditions.includes(condition)
        ? prev.medical_conditions.filter(c => c !== condition)
        : [...prev.medical_conditions, condition]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/profile/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          age: profile.age ? Number(profile.age) : null,
          gender: profile.gender,
          height_cm: profile.height_cm ? Number(profile.height_cm) : null,
          weight_kg: profile.weight_kg ? Number(profile.weight_kg) : null,
          medical_conditions: JSON.stringify(profile.medical_conditions),
          mobility_level: profile.mobility_level,
          pain_level: profile.pain_level,
        }),
      });

      if (response.ok) {
        await response.json();
        setMessage({ type: 'success', text: 'Cập nhật thông tin thành công!' });
        
        // Reload profile to get BMI
        await loadProfile();
      } else {
        setMessage({ type: 'error', text: 'Có lỗi xảy ra, vui lòng thử lại' });
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      setMessage({ type: 'error', text: 'Không thể kết nối đến server' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="flex items-center justify-center h-screen">
          <div className="text-xl text-gray-600 dark:text-gray-400">Đang tải...</div>
        </div>
      </div>
    );
  }

  const bmi = calculateBMI();
  const bmiCategory = bmi ? getBMICategory(Number(bmi)) : null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      <div className="px-8 py-8">
        {/* Header */}
        <div className="mb-8 max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Thông Tin Cá Nhân
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Cập nhật thông tin để nhận được bài tập phù hợp với bạn
          </p>
        </div>

        <form onSubmit={handleSubmit} className="max-w-7xl mx-auto">
          {/* Tabs Navigation */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 mb-6">
            <div className="flex border-b border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={() => setActiveTab('basic')}
                className={`flex-1 px-6 py-4 text-base font-semibold transition-colors ${
                  activeTab === 'basic'
                    ? 'text-teal-600 dark:text-teal-400 border-b-2 border-teal-600 dark:border-teal-400 bg-teal-50 dark:bg-teal-900/20'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                Thông Tin Cơ Bản
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('medical')}
                className={`flex-1 px-6 py-4 text-base font-semibold transition-colors ${
                  activeTab === 'medical'
                    ? 'text-teal-600 dark:text-teal-400 border-b-2 border-teal-600 dark:border-teal-400 bg-teal-50 dark:bg-teal-900/20'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                Tình Trạng Sức Khỏe
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('mobility')}
                className={`flex-1 px-6 py-4 text-base font-semibold transition-colors ${
                  activeTab === 'mobility'
                    ? 'text-teal-600 dark:text-teal-400 border-b-2 border-teal-600 dark:border-teal-400 bg-teal-50 dark:bg-teal-900/20'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                Vận Động & Đau Đớn
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="space-y-6">
            {/* Basic Info Tab */}
            {activeTab === 'basic' && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 border border-gray-200 dark:border-gray-700">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                  Thông Tin Cơ Bản
                </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Age */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Tuổi <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={profile.age}
                  onChange={(e) => setProfile({ ...profile, age: e.target.value ? Number(e.target.value) : '' })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-teal-500 dark:focus:ring-teal-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Nhập tuổi của bạn"
                  required
                  min="1"
                  max="120"
                />
              </div>

              {/* Gender */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Giới tính <span className="text-red-500">*</span>
                </label>
                <select
                  value={profile.gender}
                  onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-teal-500 dark:focus:ring-teal-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  required
                >
                  <option value="male">Nam</option>
                  <option value="female">Nữ</option>
                  <option value="other">Khác</option>
                </select>
              </div>

              {/* Height */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Chiều cao (cm) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={profile.height_cm}
                  onChange={(e) => setProfile({ ...profile, height_cm: e.target.value ? Number(e.target.value) : '' })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-teal-500 dark:focus:ring-teal-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Ví dụ: 170"
                  required
                  min="100"
                  max="250"
                />
              </div>

              {/* Weight */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Cân nặng (kg) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={profile.weight_kg}
                  onChange={(e) => setProfile({ ...profile, weight_kg: e.target.value ? Number(e.target.value) : '' })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-teal-500 dark:focus:ring-teal-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Ví dụ: 65"
                  required
                  min="20"
                  max="300"
                />
              </div>
            </div>

            {/* BMI Display */}
            {bmi && (
              <div className="mt-6 p-4 bg-gradient-to-r from-teal-50 to-blue-50 dark:from-teal-900/20 dark:to-blue-900/20 rounded-lg border border-teal-200 dark:border-teal-800">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Chỉ số BMI của bạn:</p>
                    <p className="text-3xl font-bold text-teal-600 dark:text-teal-400">{bmi}</p>
                  </div>
                  {bmiCategory && (
                    <div className="text-right">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Phân loại:</p>
                      <p className={`text-xl font-bold ${bmiCategory.color}`}>{bmiCategory.text}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
              </div>
            )}

            {/* Medical Conditions Tab */}
            {activeTab === 'medical' && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 border border-gray-200 dark:border-gray-700">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  Tình Trạng Sức Khỏe
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Chọn các vấn đề sức khỏe hiện tại (nếu có)
                </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {medicalOptions.map((option) => (
                <label
                  key={option.value}
                  className={`flex items-center gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    profile.medical_conditions.includes(option.value)
                      ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-teal-300 dark:hover:border-teal-700'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={profile.medical_conditions.includes(option.value)}
                    onChange={() => handleMedicalConditionToggle(option.value)}
                    className="w-5 h-5 text-teal-500 border-gray-300 rounded focus:ring-teal-500"
                  />
                  <span className="text-gray-900 dark:text-white font-medium">{option.label}</span>
                </label>
              ))}
                </div>
              </div>
            )}

            {/* Mobility & Pain Tab */}
            {activeTab === 'mobility' && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 border border-gray-200 dark:border-gray-700">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                  Mức Độ Vận Động & Đau Đớn
                </h2>

            <div className="space-y-6">
              {/* Mobility Level */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                  Khả năng di chuyển hiện tại
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {[
                    { value: 'beginner', label: 'Mới bắt đầu', desc: 'Ít vận động' },
                    { value: 'intermediate', label: 'Trung bình', desc: 'Vận động vừa phải' },
                    { value: 'advanced', label: 'Nâng cao', desc: 'Vận động tốt' },
                  ].map((level) => (
                    <label
                      key={level.value}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        profile.mobility_level === level.value
                          ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-teal-300 dark:hover:border-teal-700'
                      }`}
                    >
                      <input
                        type="radio"
                        name="mobility"
                        value={level.value}
                        checked={profile.mobility_level === level.value}
                        onChange={(e) => setProfile({ ...profile, mobility_level: e.target.value })}
                        className="sr-only"
                      />
                      <div className="text-center">
                        <div className="font-bold text-gray-900 dark:text-white">{level.label}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">{level.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Pain Level */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                  Mức độ đau hiện tại: <span className="text-2xl font-bold text-teal-600 dark:text-teal-400">{profile.pain_level}/10</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="10"
                  value={profile.pain_level}
                  onChange={(e) => setProfile({ ...profile, pain_level: Number(e.target.value) })}
                  className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-teal-500"
                />
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mt-2">
                  <span>0 - Không đau</span>
                  <span>5 - Đau vừa</span>
                  <span>10 - Rất đau</span>
                </div>
              </div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex gap-4">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold py-4 px-8 rounded-xl text-lg transition shadow-lg disabled:cursor-not-allowed"
              >
                {saving ? 'Đang lưu...' : 'Lưu Thông Tin'}
              </button>
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="px-8 py-4 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-bold rounded-xl transition"
              >
                Hủy
              </button>
            </div>

                    {/* Message */}
          </div>
        </form>
      </div>

      {/* Toast Popup Message */}
      {message && (
        <div className="fixed top-8 right-8 z-50 animate-slide-in-right">
          <div className={`flex items-center gap-3 px-6 py-4 rounded-xl shadow-2xl border-l-4 min-w-[320px] ${
            message.type === 'success'
              ? 'bg-white dark:bg-gray-800 border-green-500 text-gray-900 dark:text-white'
              : 'bg-white dark:bg-gray-800 border-red-500 text-gray-900 dark:text-white'
          }`}>
            <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
              message.type === 'success' ? 'bg-green-100 dark:bg-green-900' : 'bg-red-100 dark:bg-red-900'
            }`}>
              {message.type === 'success' ? (
                <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-red-600 dark:text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            <div className="flex-1">
              <p className="font-semibold text-sm">{message.text}</p>
            </div>
            <button
              onClick={() => setMessage(null)}
              className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
