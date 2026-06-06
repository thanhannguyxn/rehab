import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useDebounce } from 'use-debounce';
import { useAuth } from '../context/AuthContext';
import { doctorAPI } from '../utils/api';
import { PatientCard } from '../components/PatientCard';
import { CreatePatientModal, SuccessCredentialsPopup } from '../components/CreatePatientModal';
import type { Patient } from '../types';
import { useTranslation } from 'react-i18next';
import { PatientCardSkeleton } from '../components/skeletons/PatientCardSkeleton';

export const DoctorDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { data, isLoading, refetch: loadPatients } = useQuery<{ patients: Patient[] }>({
    queryKey: ['doctor-patients'],
    queryFn: () => doctorAPI.getPatients()
  });

  const patients: Patient[] = data?.patients || [];

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [successData, setSuccessData] = useState<Parameters<typeof SuccessCredentialsPopup>[0]['data'] | null>(null);

  // Pagination and Search states
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm] = useDebounce(searchTerm, 300);
  const [visibleCount, setVisibleCount] = useState(6);

  const { t, i18n } = useTranslation();

  // Filter patients based on debounced search term
  const filteredPatients = useMemo(() => {
    if (!debouncedSearchTerm) return patients;
    const term = debouncedSearchTerm.toLowerCase();
    return patients.filter((patient: Patient) =>
      patient.full_name?.toLowerCase().includes(term) || 
      patient.username?.toLowerCase().includes(term)
    );
  }, [patients, debouncedSearchTerm]);

  // Load more logic
  const currentPatients = useMemo(() => {
    return filteredPatients.slice(0, visibleCount);
  }, [filteredPatients, visibleCount]);

  const handleLoadMore = () => {
    setVisibleCount(prev => prev + 6);
  };

  // Reset to initial count when search term changes
  useMemo(() => {
    setVisibleCount(6);
  }, [debouncedSearchTerm]);

  // Memoize heavy stats calculations
  const todaySessionsCount = useMemo(() => {
    const today = new Date().toDateString();
    return patients.filter((p: Patient) => {
      if (!p.last_session) return false;
      return new Date(p.last_session.date).toDateString() === today;
    }).length;
  }, [patients]);

  const avgAccuracy = useMemo(() => {
    const patientsWithSessions = patients.filter((p: Patient) => p.last_session);
    if (patientsWithSessions.length === 0) return '0';
    const sum = patientsWithSessions.reduce((acc: number, p: Patient) => acc + (p.last_session?.accuracy || 0), 0);
    return (sum / patientsWithSessions.length).toFixed(1);
  }, [patients]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <>
      <div className="min-h-screen bg-gray-50 dark:bg-black transition-colors duration-200">
      <div className="max-w-6xl mx-auto p-6">
        {/* Action buttons */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <button
            onClick={() => navigate('/exercise-management')}
            className="bg-[#0369a1] hover:bg-[#0284c7] text-white font-bold py-4 rounded-xl shadow-lg flex items-center justify-center gap-2 transition"
          >
            <span>Quản Lý Bài Tập</span>
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-[#0369a1] hover:bg-[#0284c7] text-white font-bold py-4 rounded-xl shadow-lg flex items-center justify-center gap-2 transition"
          >
            <span>Tạo Tài Khoản Bệnh Nhân</span>
          </button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md text-center border dark:border-gray-800">
            <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">{t("doctorDashboard.totalPatients")}</p>
            <p className="text-5xl font-bold text-[#0284c7] dark:text-blue-600">{patients.length}</p>
          </div>
          <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md text-center border dark:border-gray-800">
            <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">{t("doctorDashboard.todaySessions")}</p>
            <p className="text-5xl font-bold text-green-600 dark:text-green-400">
              {todaySessionsCount}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md text-center border dark:border-gray-800">
            <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">{t("doctorDashboard.avgAccuracy")}</p>
            <p className="text-5xl font-bold text-purple-600 dark:text-purple-400">
              {avgAccuracy}%
            </p>
          </div>
        </div>

        {/* Patients List */}
        <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6 border dark:border-gray-800">
          <div className="flex flex-col md:flex-row justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4 md:mb-0">{t("doctorDashboard.patientList")}</h2>
            <div className="relative w-full md:w-1/3">
              <input
                type="text"
                placeholder={t("doctorDashboard.searchPatients", i18n.language === 'vi' ? "Tìm kiếm bệnh nhân" : "Search patients")}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0369a1]"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Array.from({ length: visibleCount }).map((_, index) => (
                <PatientCardSkeleton key={index} />
              ))}
            </div>
          ) : filteredPatients.length === 0 ? (
            <p className="text-center text-gray-600 dark:text-gray-400 py-8 text-lg">{t("doctorDashboard.empty")}</p>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {currentPatients.map((patient) => (
                  <PatientCard key={patient.id} patient={patient} />
                ))}
              </div>
              
              {/* Load More Button */}
              {visibleCount < filteredPatients.length && (
                <div className="mt-8 flex justify-center">
                  <button
                    onClick={handleLoadMore}
                    className="px-6 py-3 rounded-lg bg-[#0369a1] hover:bg-[#0284c7] text-white font-medium transition-colors shadow-sm"
                  >
                    {t("doctorDashboard.loadMore", i18n.language === 'vi' ? "Xem thêm" : "Load more")}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>

    {showCreateModal && (
      <CreatePatientModal
        onClose={() => setShowCreateModal(false)}
        onSuccess={(data) => {
          setShowCreateModal(false);
          setSuccessData(data);
          loadPatients();
        }}
      />
    )}

    {successData && (
      <SuccessCredentialsPopup
        data={successData}
        onClose={() => setSuccessData(null)}
      />
    )}
    </>
  );
};
