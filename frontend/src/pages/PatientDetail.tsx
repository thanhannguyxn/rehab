import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { doctorAPI } from '../utils/api';
import { SessionCard } from '../components/SessionCard';
import { ProgressChart } from '../components/ProgressChart';
import { ErrorAnalytics } from '../components/ErrorAnalytics';
import type { Session } from '../types';

// Add emotion types
interface EmotionSummary {
  avg_pain_level?: number;
  avg_fatigue_level?: number;
  predominant_emotion?: string;
  pain_incidents?: number;
  fatigue_incidents?: number;
}

interface SessionWithEmotion extends Session {
  emotion_summary?: EmotionSummary;
}

interface EmotionTrends {
  patient_id: number;
  trends: Array<{
    session_id: number;
    date: string;
    exercise_name: string;
    duration_minutes: number;
    predominant_emotion: string;
    avg_pain_level: number;
    avg_fatigue_level: number;
    pain_incidents: number;
    fatigue_incidents: number;
    accuracy: number;
  }>;
  summary: {
    total_sessions: number;
    avg_pain_level: number;
    avg_fatigue_level: number;
    most_common_emotion: string;
    emotion_distribution: Record<string, number>;
  };
}
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
  const [sessions, setSessions] = useState<SessionWithEmotion[]>([]);
  const [emotionTrends, setEmotionTrends] = useState<EmotionTrends | null>(null);
  const [showEmotionChart, setShowEmotionChart] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const { t } = useTranslation();

  useEffect(() => {
    if (patientId) {
      loadPatientHistory();
    }
  }, [patientId]);

  const loadPatientHistory = async () => {
    try {
      // Load sessions with emotion data
      const sessionData = await doctorAPI.getPatientHistory(Number(patientId), 50);
      setSessions(sessionData.sessions);

      // Load emotion trends
      try {
        const emotionData = await fetch(`/api/doctor/patients/${patientId}/emotion-trends`, {
          headers: {
            'Authorization': `Bearer ${sessionStorage.getItem('token')}`
          }
        });
        if (emotionData.ok) {
          const trends = await emotionData.json();
          setEmotionTrends(trends);
        }
      } catch (emotionError) {
        console.log('No emotion data available:', emotionError);
        // Continue without emotion data
      }
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

  // Helper functions for emotion display
  const getEmotionIcon = (emotion: string) => {
    switch (emotion) {
      case 'happy': return '😊';
      case 'pain': return '😣';
      case 'tired': return '😴';
      case 'struggling': return '😰';
      case 'focused': return '🧘';
      case 'neutral': return '😐';
      default: return '😐';
    }
  };

  const getEmotionLabel = (emotion: string) => {
    switch (emotion) {
      case 'happy': return 'Vui vẻ';
      case 'pain': return 'Đau đớn';
      case 'tired': return 'Mệt mỏi';
      case 'struggling': return 'Gắng sức';
      case 'focused': return 'Tập trung';
      case 'neutral': return 'Bình thường';
      default: return 'Không xác định';
    }
  };

  const getEmotionBadgeColor = (emotion: string) => {
    switch (emotion) {
      case 'happy': return 'bg-green-100 text-green-800';
      case 'pain': return 'bg-red-100 text-red-800';
      case 'tired': return 'bg-yellow-100 text-yellow-800';
      case 'struggling': return 'bg-orange-100 text-orange-800';
      case 'focused': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-600 text-white p-6 shadow-lg">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">{t("patientDetail.title")}</h1>
            <p className="text-xl mt-1">{t("patientDetail.patientId")}: {patientId}</p>
          </div>
          <div className="flex gap-4">
            <button
              onClick={generatePDF}
              disabled={sessions.length === 0}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold text-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              📄 {t("patientDetail.exportPDF")}
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold text-lg hover:bg-blue-50 transition"
            >
              ← {t("patientDetail.back")}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-xl text-gray-600">{t("patientDetail.loading")}</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <p className="text-2xl text-gray-600">{t("patientDetail.noSessions")}</p>
          </div>
        ) : (
          <>
            {/* Charts */}
            <div className="grid grid-cols-1 gap-6 mb-6">
              <ProgressChart sessions={sessions} />
              <ErrorAnalytics patientId={Number(patientId)} />

              {/* Emotion Analysis Chart */}
              {emotionTrends && emotionTrends.summary.total_sessions > 0 && (
                <div className="bg-white p-6 rounded-lg shadow-md">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-2xl font-bold text-gray-800">Phân tích cảm xúc</h3>
                    <button
                      onClick={() => setShowEmotionChart(!showEmotionChart)}
                      className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
                    >
                      {showEmotionChart ? 'Ẩn chi tiết' : 'Xem chi tiết'}
                    </button>
                  </div>

                  {/* Emotion Summary Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="text-lg font-semibold text-blue-600">Cảm xúc chủ đạo</h4>
                      <p className="text-2xl font-bold text-blue-800">
                        {getEmotionLabel(emotionTrends.summary.most_common_emotion)}
                      </p>
                    </div>
                    <div className="bg-orange-50 p-4 rounded-lg">
                      <h4 className="text-lg font-semibold text-orange-600">Mức đau TB</h4>
                      <p className="text-2xl font-bold text-orange-800">
                        {Math.round(emotionTrends.summary.avg_pain_level * 100)}%
                      </p>
                    </div>
                    <div className="bg-yellow-50 p-4 rounded-lg">
                      <h4 className="text-lg font-semibold text-yellow-600">Mức mệt TB</h4>
                      <p className="text-2xl font-bold text-yellow-800">
                        {Math.round(emotionTrends.summary.avg_fatigue_level * 100)}%
                      </p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <h4 className="text-lg font-semibold text-green-600">Tổng phiên</h4>
                      <p className="text-2xl font-bold text-green-800">
                        {emotionTrends.summary.total_sessions}
                      </p>
                    </div>
                  </div>

                  {/* Emotion Distribution */}
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold mb-3">Phân bố cảm xúc</h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(emotionTrends.summary.emotion_distribution).map(([emotion, count]) => (
                        <div
                          key={emotion}
                          className={`px-3 py-2 rounded-full text-sm font-medium ${getEmotionBadgeColor(emotion)}`}
                        >
                          {getEmotionLabel(emotion)}: {count}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Detailed Timeline */}
                  {showEmotionChart && (
                    <div>
                      <h4 className="text-lg font-semibold mb-4">Timeline cảm xúc</h4>
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {emotionTrends.trends.map((trend, index) => (
                          <div key={trend.session_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center gap-4">
                              <div className="text-2xl">{getEmotionIcon(trend.predominant_emotion)}</div>
                              <div>
                                <p className="font-medium">{trend.exercise_name}</p>
                                <p className="text-sm text-gray-600">{trend.date}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-medium">
                                Đau: {Math.round(trend.avg_pain_level * 100)}% |
                                Mệt: {Math.round(trend.avg_fatigue_level * 100)}%
                              </p>
                              <p className="text-sm text-gray-600">
                                Độ chính xác: {trend.accuracy}%
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <div className="bg-white p-6 rounded-lg shadow-md text-center">
                <p className="text-gray-600 text-lg mb-2">{t("patientDetail.totalSessions")}</p>
                <p className="text-5xl font-bold text-blue-600">{sessions.length}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md text-center">
                <p className="text-gray-600 text-lg mb-2">{t("patientDetail.avgAccuracy")}</p>
                <p className="text-5xl font-bold text-green-600">
                  {(sessions.reduce((sum, s) => sum + s.accuracy, 0) / sessions.length).toFixed(1)}%
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md text-center">
                <p className="text-gray-600 text-lg mb-2">{t("patientDetail.totalReps")}</p>
                <p className="text-5xl font-bold text-purple-600">
                  {sessions.reduce((sum, s) => sum + s.total_reps, 0)}
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md text-center">
                <p className="text-gray-600 text-lg mb-2">{t("patientDetail.totalTime")}</p>
                <p className="text-5xl font-bold text-orange-600">
                  {Math.floor(sessions.reduce((sum, s) => sum + s.duration_seconds, 0) / 60)}p
                </p>
              </div>
            </div>

            {/* Session List */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">{t("patientDetail.sessionDetails")}</h2>
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
