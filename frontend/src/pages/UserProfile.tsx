import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { profileAPI } from '../utils/api';

interface ProfileData {
  age: number | '';
  gender: string;
  height_cm: number | '';
  weight_kg: number | '';
  medical_conditions: string[];
  injury_type: string;
  mobility_level: string;
  pain_level: number;
}

export const UserProfile = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [activeTab, setActiveTab] = useState<'basic' | 'medical' | 'mobility'>('basic');
  const { t } = useTranslation();
  
  const [profile, setProfile] = useState<ProfileData>({
    age: '',
    gender: 'male',
    height_cm: '',
    weight_kg: '',
    medical_conditions: [],
    injury_type: '',
    mobility_level: 'beginner',
    pain_level: 0,
  });

  const medicalOptions = [
    { value: 'knee_arthritis', label: t("userProfile.medicalConditions.arthritis") },
    { value: 'shoulder_pain', label: t("userProfile.medicalConditions.shoulderPain") },
    { value: 'back_pain', label: t("userProfile.medicalConditions.backPain") },
    { value: 'osteoporosis', label: t("userProfile.medicalConditions.osteoporosis") },
    { value: 'diabetes', label: t("userProfile.medicalConditions.diabetes") },
    { value: 'heart_disease', label: t("userProfile.medicalConditions.heartDisease") },
    { value: 'hypertension', label: t("userProfile.medicalConditions.hypertension") },
    { value: 'stroke_recovery', label: t("userProfile.medicalConditions.strokeRecovery") },
  ];

  const injuryOptions = [
    { value: '', label: 'Chọn loại chấn thương' },
    { value: 'knee_pain', label: 'Đau khớp gối' },
    { value: 'shoulder_pain', label: 'Đau vai' },
    { value: 'back_pain', label: 'Đau lưng' },
    { value: 'balance_issue', label: 'Vấn đề cân bằng' },
    { value: 'hip_pain', label: 'Đau hông' },
    { value: 'ankle_pain', label: 'Đau cổ chân' },
    { value: 'other', label: 'Khác' },
  ];

  const didFetch = useRef(false);

  useEffect(() => {
    if (didFetch.current) return;
    didFetch.current = true;
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
      const data = await profileAPI.getMe();
      setProfile({
        age: (data.age as number) || '',
        gender: (data.gender as string) || 'male',
        height_cm: (data.height_cm as number) || '',
        weight_kg: (data.weight_kg as number) || '',
        medical_conditions: data.medical_conditions
          ? JSON.parse(data.medical_conditions as string)
          : [],
        injury_type: (data.injury_type as string) || '',
        mobility_level: (data.mobility_level as string) || 'beginner',
        pain_level: (data.pain_level as number) || 0,
      });
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
    if (bmi < 18.5) return { text: t("userProfile.bmi.underweight"), color: 'text-yellow-600 dark:text-yellow-400' };
    if (bmi < 25) return { text: t("userProfile.bmi.normal"), color: 'text-green-600 dark:text-green-400' };
    if (bmi < 30) return { text: t("userProfile.bmi.overweight"), color: 'text-orange-600 dark:text-orange-400' };
    return { text: t("userProfile.bmi.obese"), color: 'text-red-600 dark:text-red-400' };
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
      await profileAPI.update({
        age: profile.age ? Number(profile.age) : null,
        gender: profile.gender,
        height_cm: profile.height_cm ? Number(profile.height_cm) : null,
        weight_kg: profile.weight_kg ? Number(profile.weight_kg) : null,
        medical_conditions: JSON.stringify(profile.medical_conditions),
        injury_type: profile.injury_type,
        mobility_level: profile.mobility_level,
        pain_level: profile.pain_level,
      });
      setMessage({ type: 'success', text: t("userProfile.success") });
      await loadProfile();
    } catch (error) {
      console.error('Error updating profile:', error);
      setMessage({ type: 'error', text: t("userProfile.serverError") });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="flex items-center justify-center h-screen">
          <div className="text-xl text-gray-600 dark:text-gray-400">{t("userProfile.loading")}</div>
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
            {t("userProfile.title")}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {t("userProfile.subtitle")}
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
                    ? 'text-[#0284c7] dark:text-blue-600 border-b-2 border-[#0284c7] dark:border-blue-600 bg-blue-50 dark:bg-[#075985]/20'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                {t("userProfile.tabs.basic")}
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('medical')}
                className={`flex-1 px-6 py-4 text-base font-semibold transition-colors ${
                  activeTab === 'medical'
                    ? 'text-[#0284c7] dark:text-blue-600 border-b-2 border-[#0284c7] dark:border-blue-600 bg-blue-50 dark:bg-[#075985]/20'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                {t("userProfile.tabs.medical")}
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('mobility')}
                className={`flex-1 px-6 py-4 text-base font-semibold transition-colors ${
                  activeTab === 'mobility'
                    ? 'text-[#0284c7] dark:text-blue-600 border-b-2 border-[#0284c7] dark:border-blue-600 bg-blue-50 dark:bg-[#075985]/20'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                {t("userProfile.tabs.mobility")}
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="space-y-6">
            {/* Basic Info Tab */}
            {activeTab === 'basic' && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 border border-gray-200 dark:border-gray-700">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                  {t("userProfile.tabs.basic")}
                </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Age */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  {t("userProfile.fields.age")} <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={profile.age}
                  onChange={(e) => setProfile({ ...profile, age: e.target.value ? Number(e.target.value) : '' })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-[#0369a1] dark:focus:ring-blue-600 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder={t("userProfile.placeholders.age")}
                  required
                  min="1"
                  max="120"
                />
              </div>

              {/* Gender */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  {t("userProfile.fields.gender")} <span className="text-red-500">*</span>
                </label>
                <select
                  value={profile.gender}
                  onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-[#0369a1] dark:focus:ring-blue-600 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  required
                >
                  <option value="male">{t("userProfile.genderOptions.male")}</option>
                  <option value="female">{t("userProfile.genderOptions.female")}</option>
                  <option value="other">{t("userProfile.genderOptions.other")}</option>
                </select>
              </div>

              {/* Height */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  {t("userProfile.fields.height")} (cm) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={profile.height_cm}
                  onChange={(e) => setProfile({ ...profile, height_cm: e.target.value ? Number(e.target.value) : '' })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-[#0369a1] dark:focus:ring-blue-600 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder={t("userProfile.placeholders.height")}
                  required
                  min="100"
                  max="250"
                />
              </div>

              {/* Weight */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  {t("userProfile.fields.weight")} (kg) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={profile.weight_kg}
                  onChange={(e) => setProfile({ ...profile, weight_kg: e.target.value ? Number(e.target.value) : '' })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-[#0369a1] dark:focus:ring-blue-600 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder={t("userProfile.placeholders.weight")}
                  required
                  min="20"
                  max="300"
                />
              </div>
            </div>

            {/* BMI Display */}
            {bmi && (
              <div className="mt-6 p-4 bg-blue-50 dark:bg-[#075985]/20 rounded-lg border border-blue-200 dark:border-[#075985]">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{t("userProfile.bmi.label")}:</p>
                    <p className="text-3xl font-bold text-[#0284c7] dark:text-blue-600">{bmi}</p>
                  </div>
                  {bmiCategory && (
                    <div className="text-right">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{t("userProfile.bmi.category")}:</p>
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
                  {t("userProfile.medicalTitle")}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  {t("userProfile.medicalSubtitle")}
                </p>

            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                Loại chấn thương
              </label>
              <select
                value={profile.injury_type}
                onChange={(e) => setProfile({ ...profile, injury_type: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-[#0369a1] dark:focus:ring-blue-600 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {injuryOptions.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="mb-3 block text-sm font-semibold text-gray-700 dark:text-gray-300">
                Tình trạng bệnh lý
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {medicalOptions.map((option) => (
                <label
                  key={option.value}
                  className={`flex items-center gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    profile.medical_conditions.includes(option.value)
                      ? 'border-[#0369a1] bg-blue-50 dark:bg-[#075985]/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-[#0284c7]'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={profile.medical_conditions.includes(option.value)}
                    onChange={() => handleMedicalConditionToggle(option.value)}
                    className="w-5 h-5 text-[#0369a1] border-gray-300 rounded focus:ring-[#0369a1]"
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
                  {t("userProfile.tabs.mobility")}
                </h2>

            <div className="space-y-6">
              {/* Mobility Level */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                  {t("userProfile.fields.mobilityLevel")}
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {[
                    { value: 'beginner', label: t("userProfile.mobilityLevels.beginner"), desc: t("userProfile.mobilityLevels.beginnerDesc") },
                    { value: 'intermediate', label: t("userProfile.mobilityLevels.intermediate"), desc: t("userProfile.mobilityLevels.intermediateDesc") },
                    { value: 'advanced', label: t("userProfile.mobilityLevels.advanced"), desc: t("userProfile.mobilityLevels.advancedDesc") },
                  ].map((level) => (
                    <label
                      key={level.value}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        profile.mobility_level === level.value
                          ? 'border-[#0369a1] bg-blue-50 dark:bg-[#075985]/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-[#0284c7]'
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
                  {t("userProfile.fields.painLevel")}: <span className="text-2xl font-bold text-[#0284c7] dark:text-blue-600">{profile.pain_level}/10</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="10"
                  value={profile.pain_level}
                  onChange={(e) => setProfile({ ...profile, pain_level: Number(e.target.value) })}
                  className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-[#0369a1]"
                />
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mt-2">
                  <span>0 - {t("userProfile.painScale.none")}</span>
                  <span>5 - {t("userProfile.painScale.medium")}</span>
                  <span>10 - {t("userProfile.painScale.severe")}</span>
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
                className="flex-1 bg-[#0369a1] hover:bg-[#0284c7] disabled:bg-gray-400 text-white font-bold py-4 px-8 rounded-xl text-lg transition shadow-lg disabled:cursor-not-allowed"
              >
                {saving ? t("userProfile.loading") : t("userProfile.save")}
              </button>
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="px-8 py-4 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-bold rounded-xl transition"
              >
                {t("userProfile.cancel")}
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
