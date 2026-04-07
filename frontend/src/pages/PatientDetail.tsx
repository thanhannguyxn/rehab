import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { doctorAPI } from '../utils/api';
import { SessionCard } from '../components/SessionCard';
import { ProgressChart } from '../components/ProgressChart';
import { ErrorAnalytics } from '../components/ErrorAnalytics';
import type { Session } from '../types';

import jsPDF from 'jspdf';
import 'jspdf-autotable';
import { useTranslation } from 'react-i18next';

// Extend jsPDF type to include autoTable
declare module 'jspdf' {
  interface jsPDF {
    autoTable: (options: any) => jsPDF;
  }
}

export const PatientDetail = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { t, i18n } = useTranslation();

  useEffect(() => {
    if (patientId) {
      loadPatientHistory();
    }
  }, [patientId]);

  const loadPatientHistory = async () => {
    try {
      // Load sessions
      const sessionData = await doctorAPI.getPatientHistory(Number(patientId), 50);
      setSessions(sessionData.sessions);
    } catch (error) {
      console.error('Failed to load patient history:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generatePDF = () => {
    const doc = new jsPDF();

    // Title
    doc.setFontSize(20);
    doc.text('BÁO CÁO TIẾN ĐỘ PHỤC HỒI CHỨC NĂNG', 20, 20);

    doc.setFontSize(12);
    doc.text(`Bệnh nhân ID: ${patientId}`, 20, 30);
    doc.text(`Ngày tạo: ${new Date().toLocaleDateString('vi-VN')}`, 20, 37);

    // Summary stats
    if (sessions.length > 0) {
      const avgAccuracy = (sessions.reduce((sum, s) => sum + s.accuracy, 0) / sessions.length).toFixed(1);
      const totalReps = sessions.reduce((sum, s) => sum + s.total_reps, 0);
      const totalMinutes = Math.floor(sessions.reduce((sum, s) => sum + s.duration_seconds, 0) / 60);

      doc.text('TỔNG QUAN:', 20, 50);
      doc.text(`- Tổng số buổi tập: ${sessions.length}`, 25, 57);
      doc.text(`- Độ chính xác trung bình: ${avgAccuracy}%`, 25, 64);
      doc.text(`- Tổng số lần tập: ${totalReps}`, 25, 71);
      doc.text(`- Tổng thời gian: ${totalMinutes} phút`, 25, 78);

      // Sessions table
      const tableData = sessions.slice(0, 10).map((s, i) => [
        i + 1,
        s.exercise_name,
        new Date(s.start_time).toLocaleDateString('vi-VN'),
        s.total_reps,
        `${s.accuracy.toFixed(1)}%`,
        `${Math.floor(s.duration_seconds / 60)}p`,
      ]);

      doc.autoTable({
        startY: 90,
        head: [['#', 'Bài tập', 'Ngày', 'Số lần', 'Chính xác', 'Thời gian']],
        body: tableData,
        styles: { fontSize: 10 },
        headStyles: { fillColor: [37, 99, 235] },
      });

      // Recommendations
      const finalY = (doc as any).lastAutoTable.finalY || 150;
      doc.text('NHẬN XÉT VÀ KHUYẾN NGHỊ:', 20, finalY + 15);
      
      if (parseFloat(avgAccuracy) >= 80) {
        doc.text('- Bệnh nhân có tiến độ tốt, duy trì tập luyện đều đặn', 25, finalY + 22);
        doc.text('- Có thể tăng cường độ tập luyện', 25, finalY + 29);
      } else if (parseFloat(avgAccuracy) >= 60) {
        doc.text('- Tiến độ khá, cần cải thiện kỹ thuật', 25, finalY + 22);
        doc.text('- Tập trung sửa các lỗi thường gặp', 25, finalY + 29);
      } else {
        doc.text('- Cần theo dõi sát sao và hướng dẫn kỹ hơn', 25, finalY + 22);
        doc.text('- Đề xuất tập với cường độ thấp hơn', 25, finalY + 29);
      }
    }

    // Save PDF
    doc.save(`bao-cao-benh-nhan-${patientId}.pdf`);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-black">
      {/* Header */}
      <div className="p-6 text-gray-900 dark:text-white">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">{t("patientDetail.title")}</h1>
            <p className="text-xl mt-1">{t("patientDetail.patientId")}: {patientId}</p>
          </div>
          <div className="flex gap-4">
            <button
              onClick={() => navigate(`/doctor/assistant?patientId=${patientId}`)}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-semibold text-lg transition"
            >
              {i18n.language === 'en' ? 'AI Assistant' : 'Trợ Lý AI'}
            </button>
            <button
              onClick={generatePDF}
              disabled={sessions.length === 0}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold text-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t("patientDetail.exportPDF")}
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-white px-6 py-3 rounded-lg font-semibold text-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition"
            >
              {t("patientDetail.back")}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-xl text-gray-600 dark:text-gray-400">{t("patientDetail.loading")}</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-12 text-center">
            <p className="text-2xl text-gray-600 dark:text-gray-400">{t("patientDetail.noSessions")}</p>
          </div>
        ) : (
          <>
            {/* Charts */}
            <div className="grid grid-cols-1 gap-6 mb-6">
              <ProgressChart sessions={sessions} />
              <ErrorAnalytics patientId={Number(patientId)} />
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md text-center">
                <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">{t("patientDetail.totalSessions")}</p>
                <p className="text-5xl font-bold text-blue-600">{sessions.length}</p>
              </div>
              <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md text-center">
                <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">{t("patientDetail.avgAccuracy")}</p>
                <p className="text-5xl font-bold text-green-600">
                  {(sessions.reduce((sum, s) => sum + s.accuracy, 0) / sessions.length).toFixed(1)}%
                </p>
              </div>
              <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md text-center">
                <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">{t("patientDetail.totalReps")}</p>
                <p className="text-5xl font-bold text-purple-600">
                  {sessions.reduce((sum, s) => sum + s.total_reps, 0)}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-900 p-6 rounded-lg shadow-md text-center">
                <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">{t("patientDetail.totalTime")}</p>
                <p className="text-5xl font-bold text-orange-600">
                  {Math.floor(sessions.reduce((sum, s) => sum + s.duration_seconds, 0) / 60)}p
                </p>
              </div>
            </div>

            {/* Session List */}
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-6">{t("patientDetail.sessionDetails")}</h2>
              <div className="space-y-4">
                {sessions.map((session) => (
                  <SessionCard key={session.id} session={session} />
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
