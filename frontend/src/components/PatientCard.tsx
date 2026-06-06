import { Link } from 'react-router-dom';
import type { Patient } from '../types';
import { useTranslation } from 'react-i18next';

interface PatientCardProps {
  patient: Patient;
}

export const PatientCard = ({ patient }: PatientCardProps) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffHours < 1) return t("patientCard.time.justNow");
    if (diffHours < 24) return `${diffHours} ` + t("patientCard.time.hoursAgo");
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return t("patientCard.time.yesterday");
    if (diffDays < 7) return `${diffDays} ` + t("patientCard.time.daysAgo");
    return date.toLocaleDateString('vi-VN');
  };

  const { t } = useTranslation();

  return (
    <Link
      to={`/doctor/patient/${patient.id}`}
      className="block bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md hover:shadow-xl transition-shadow border border-gray-100 dark:border-gray-700"
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-2xl font-bold text-gray-800 dark:text-white">{patient.full_name}</h3>
          <p className="text-gray-600 dark:text-gray-400">
            {patient.age} {t("patientCard.age")} • {patient.gender}
          </p>
        </div>
        <div className="bg-blue-100 dark:bg-[#075985]/40 text-[#075985] dark:text-blue-300 px-3 py-1 rounded-full text-sm font-semibold">
          {patient.username}
        </div>
      </div>

      {patient.last_session ? (
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{t("patientCard.lastSession")}</p>
          <div className="flex justify-between items-center">
            <div>
              <p className="font-semibold text-gray-800 dark:text-white">{patient.last_session.exercise}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">{formatDate(patient.last_session.date)}</p>
            </div>
            <div
              className={`text-2xl font-bold ${
                patient.last_session.accuracy >= 80
                  ? 'text-green-600 dark:text-green-400'
                  : patient.last_session.accuracy >= 60
                  ? 'text-yellow-600 dark:text-yellow-500'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {patient.last_session.accuracy.toFixed(1)}%
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg text-center">
          <p className="text-gray-600 dark:text-gray-400">{t("patientCard.noSession")}</p>
        </div>
      )}
    </Link>
  );
};
