import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { agentAPI } from '../utils/api';

interface ScheduleItem {
  id: number;
  exercise_name: string;
  scheduled_for: string;
  doctor_name: string;
  note?: string;
  is_read: boolean;
  created_at: string;
}

function formatScheduleDate(dateString: string) {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) {
    return dateString;
  }
  return date.toLocaleString();
}

export const ScheduleSessionsPage = () => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(true);
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);

  const didFetch = useRef(false);

  useEffect(() => {
    if (didFetch.current) return;
    didFetch.current = true;
    const loadSchedules = async () => {
      try {
        const data = await agentAPI.getPatientSchedules();
        setSchedules(data.schedules || []);
      } catch (error) {
        console.error('Failed to load schedules:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadSchedules();
  }, []);

  const markRead = async (id: number) => {
    try {
      await agentAPI.markPatientNotificationRead(id);
      setSchedules((prev) => prev.map((s) => (s.id === id ? { ...s, is_read: true } : s)));
    } catch (error) {
      console.error('Failed to mark schedule as read:', error);
    }
  };

  const getTranslatedExerciseName = (rawName: string) => {
    const key = rawName.toLowerCase().replace(/-/g, '_');
    const translated = t(`exercisePage.exercises.names.${key}`);
    return translated.includes('exercisePage.exercises.names') ? rawName : translated;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-black transition-colors duration-300">
      <div className="pt-8 pb-2">
        <div className="max-w-6xl mx-auto px-6">
          <h1 className="text-5xl font-black mb-2 text-[#0369a1] dark:text-blue-600 capitalize">
            {t("schedulePage.title")}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg mt-2">{t("schedulePage.subtitle")}</p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6 mt-2">
        {isLoading ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8 text-center text-lg text-gray-600 dark:text-gray-300 flex items-center justify-center space-x-3">
            <svg className="animate-spin h-6 w-6 text-[#0369a1]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{t("schedulePage.loading")}</span>
          </div>
        ) : schedules.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-12 text-center border border-gray-100 dark:border-gray-700">
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 text-gray-400 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <p className="text-2xl font-semibold text-gray-800 dark:text-gray-200">{t("schedulePage.emptyTitle")}</p>
            <p className="text-gray-500 dark:text-gray-400 mt-2">{t("schedulePage.emptySubtitle")}</p>
          </div>
        ) : (
          <div className="space-y-4">
            {schedules.map((item) => (
              <div 
                key={item.id} 
                className={`bg-white dark:bg-gray-800 rounded-xl border ${
                  item.is_read ? 'border-gray-200 dark:border-gray-700' : 'border-blue-300 dark:border-[#0369a1]/50 shadow-md'
                } p-6 transition-all duration-200 hover:shadow-lg`}
              >
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <p className="text-xl font-bold text-gray-900 dark:text-white capitalize">{getTranslatedExerciseName(item.exercise_name)}</p>
                      <span
                        className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                          item.is_read 
                            ? 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300' 
                            : 'bg-blue-100 text-[#075985] dark:bg-[#075985]/50 dark:text-blue-300 ring-1 ring-[#0369a1]/20'
                        }`}
                      >
                        {item.is_read ? t("schedulePage.statusSeen") : t("schedulePage.statusNew")}
                      </span>
                    </div>
                    
                    <div className="space-y-1.5 mt-3">
                      <p className="text-sm text-gray-600 dark:text-gray-300 flex items-center gap-2">
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        <span className="font-medium text-gray-700 dark:text-gray-200">{t("schedulePage.scheduledFor")}</span> {formatScheduleDate(item.scheduled_for)}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-300 flex items-center gap-2">
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                        <span className="font-medium text-gray-700 dark:text-gray-200">{t("schedulePage.doctor")}</span> {item.doctor_name}
                      </p>
                      {item.note && (
                        <div className="text-sm mt-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
                          <span className="font-medium text-[#075985] dark:text-blue-300">{t("schedulePage.note")}</span> 
                          <span className="text-[#075985] dark:text-blue-200 ml-1">{item.note}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-row md:flex-col items-stretch justify-end gap-3 mt-2 md:mt-0 min-w-[140px]">
                    {!item.is_read && (
                      <button
                        onClick={() => markRead(item.id)}
                        className="flex-1 md:flex-none px-4 py-2.5 rounded-lg text-sm font-medium border-2 border-[#0369a1] text-[#0284c7] dark:text-blue-600 hover:bg-blue-50 dark:hover:bg-[#075985]/30 transition-colors flex items-center justify-center gap-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                        {t("schedulePage.btnMarkSeen")}
                      </button>
                    )}

                    <Link
                      to="/exercise"
                      className="flex-1 md:flex-none px-4 py-2.5 rounded-lg text-sm font-medium bg-[#0369a1] hover:bg-[#0284c7] text-white shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
                    >
                      <span>{t("schedulePage.btnOpen")}</span>

                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
