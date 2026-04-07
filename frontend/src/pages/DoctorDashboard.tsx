import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { doctorAPI } from '../utils/api';
import { PatientCard } from '../components/PatientCard';
import type { Patient } from '../types';
import { useTranslation } from 'react-i18next';
import { PatientCardSkeleton } from '../components/skeletons/PatientCardSkeleton';

export const DoctorDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Pagination and Search states
  const [searchTerm, setSearchTerm] = useState('');
  const [visibleCount, setVisibleCount] = useState(5);

  const { t, i18n } = useTranslation();

  useEffect(() => {
    loadPatients();
  }, []);

  // Filter patients based on search term
  const filteredPatients = patients.filter(patient =>
    patient.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    patient.username?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Load more logic
  const currentPatients = filteredPatients.slice(0, visibleCount);

  const handleLoadMore = () => {
    setVisibleCount(prev => prev + 6);
  };

  // Reset to initial count when search term changes
  useEffect(() => {
    setVisibleCount(6);
  }, [searchTerm]);

  const loadPatients = async () => {
    try {
      const data = await doctorAPI.getPatients();
      setPatients(data.patients);
    } catch (error) {
      console.error('Failed to load patients:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-black transition-colors duration-200">
      <div className="max-w-6xl mx-auto p-6">
        {/* Exercise Management Links */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <button
            onClick={() => navigate('/exercise-management')}
            className="bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600 text-white font-bold py-4 rounded-xl shadow-lg flex items-center justify-center gap-2 transition"
          >
            <span>Quản Lý Bài Tập</span>
          </button>
          <button
            onClick={() => navigate('/exercise-management')}
            className="bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white font-bold py-4 rounded-xl shadow-lg flex items-center justify-center gap-2 transition"
          >
            <span>Thêm Bài Tập Mới</span>
          </button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md text-center border dark:border-gray-800">
            <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">{t("doctorDashboard.totalPatients")}</p>
            <p className="text-5xl font-bold text-blue-600 dark:text-blue-400">{patients.length}</p>
          </div>
          <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md text-center border dark:border-gray-800">
            <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">{t("doctorDashboard.todaySessions")}</p>
            <p className="text-5xl font-bold text-green-600 dark:text-green-400">
              {patients.filter((p) => {
                if (!p.last_session) return false;
                const sessionDate = new Date(p.last_session.date);
                const today = new Date();
                return sessionDate.toDateString() === today.toDateString();
              }).length}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md text-center border dark:border-gray-800">
            <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">{t("doctorDashboard.avgAccuracy")}</p>
            <p className="text-5xl font-bold text-purple-600 dark:text-purple-400">
              {patients.filter((p) => p.last_session).length > 0
                ? (
                    patients
                      .filter((p) => p.last_session)
                      .reduce((sum, p) => sum + (p.last_session?.accuracy || 0), 0) /
                    patients.filter((p) => p.last_session).length
                  ).toFixed(1)
                : '0'}
              %
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
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    className="px-6 py-3 rounded-lg bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white font-medium transition-colors shadow-sm"
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
  );
};
