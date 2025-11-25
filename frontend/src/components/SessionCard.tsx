import type { Session } from '../types';

interface SessionCardProps {
  session: Session;
  previousSession?: Session; // For comparison
}

export const SessionCard = ({ session, previousSession }: SessionCardProps) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}p ${secs}s`;
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 80) return 'text-green-600';
    if (accuracy >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceBadge = (accuracy: number) => {
    if (accuracy >= 90) {
      return {
        text: 'Xuất sắc',
        className: 'bg-yellow-400 text-yellow-900'
      };
    }
    if (accuracy >= 80) {
      return {
        text: 'Tốt',
        className: 'bg-green-400 text-green-900'
      };
    }
    if (accuracy >= 60) {
      return {
        text: 'Trung bình',
        className: 'bg-blue-400 text-blue-900'
      };
    }
    return {
      text: 'Cần cải thiện',
      className: 'bg-orange-400 text-orange-900'
    };
  };

  const getTop3Errors = () => {
    if (!session.errors || session.errors.length === 0) return [];
    return [...session.errors]
      .sort((a, b) => b.count - a.count)
      .slice(0, 3);
  };

  const getComparison = () => {
    if (!previousSession) return null;
    
    const accuracyDiff = session.accuracy - previousSession.accuracy;
    const totalErrorsCurrent = session.errors?.reduce((sum, e) => sum + e.count, 0) || 0;
    const totalErrorsPrev = previousSession.errors?.reduce((sum, e) => sum + e.count, 0) || 0;
    const errorDiff = totalErrorsCurrent - totalErrorsPrev;
    
    return { accuracyDiff, errorDiff };
  };

  const badge = getPerformanceBadge(session.accuracy);
  const top3Errors = getTop3Errors();
  const comparison = getComparison();

  return (
    <div className="relative bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 border border-gray-200 dark:border-gray-700">
      {/* Performance Badge */}
      <span className={`absolute top-4 right-4 ${badge.className} px-3 py-1 rounded-full text-sm font-bold shadow-md`}>
        {badge.text}
      </span>

      <div className="flex justify-between items-start mb-4 pr-32">
        <div>
          <h3 className="text-xl font-bold text-gray-800 dark:text-white">{session.exercise_name}</h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm">{formatDate(session.start_time)}</p>
        </div>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 p-4 rounded-lg text-center">
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Tổng số lần</p>
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{session.total_reps}</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 p-4 rounded-lg text-center">
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Đúng kỹ thuật</p>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">{session.correct_reps}</p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 p-4 rounded-lg text-center">
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Thời gian</p>
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {formatDuration(session.duration_seconds)}
          </p>
        </div>
        <div className="bg-gradient-to-br from-teal-50 to-teal-100 dark:from-teal-900/30 dark:to-teal-800/30 p-4 rounded-lg text-center">
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Độ chính xác</p>
          <p className={`text-2xl font-bold ${getAccuracyColor(session.accuracy)}`}>
            {session.accuracy.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Top 3 Errors */}
      {top3Errors.length > 0 && (
        <div className="mb-4 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
          <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <span>Lỗi phổ biến nhất:</span>
          </p>
          <div className="space-y-2">
            {top3Errors.map((error, index) => (
              <div key={index} className="flex items-center gap-3 bg-white dark:bg-gray-800 p-2 rounded">
                <span className="flex-1 text-sm text-gray-700 dark:text-gray-300">{error.name}</span>
                <span className="font-bold text-red-600 dark:text-red-400 text-sm">
                  {error.count}x
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comparison with Previous Session */}
      {comparison && (
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
            <span>So với lần trước:</span>
          </p>
          <div className="flex gap-4 flex-wrap">
            {/* Accuracy comparison */}
            <div className="flex items-center gap-2">
              {comparison.accuracyDiff > 0 ? (
                <>
                  <span className="text-sm text-green-600 dark:text-green-400">
                    Độ chính xác +{comparison.accuracyDiff.toFixed(1)}%
                  </span>
                </>
              ) : comparison.accuracyDiff < 0 ? (
                <>
                  <span className="text-sm text-red-600 dark:text-red-400">
                    Độ chính xác {comparison.accuracyDiff.toFixed(1)}%
                  </span>
                </>
              ) : (
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Độ chính xác không đổi
                </span>
              )}
            </div>

            {/* Error comparison */}
            <div className="flex items-center gap-2">
              {comparison.errorDiff < 0 ? (
                <>
                  <span className="text-green-600 dark:text-green-400 font-bold">✓</span>
                  <span className="text-sm text-green-600 dark:text-green-400">
                    Giảm {Math.abs(comparison.errorDiff)} lỗi
                  </span>
                </>
              ) : comparison.errorDiff > 0 ? (
                <>
                  <span className="text-sm text-orange-600 dark:text-orange-400">
                    Tăng {comparison.errorDiff} lỗi
                  </span>
                </>
              ) : (
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Số lỗi không đổi
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
