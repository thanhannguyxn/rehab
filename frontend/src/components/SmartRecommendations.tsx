import type { Session } from '../types';
import { useTranslation } from 'react-i18next';

interface SmartRecommendationsProps {
  sessions: Session[];
}

export const SmartRecommendations = ({ sessions }: SmartRecommendationsProps) => {
  const { t } = useTranslation();
  const getRecommendations = () => {
    if (sessions.length === 0) return [];

    const recommendations: Array<{
      type: 'success' | 'warning' | 'info' | 'tip';
      title: string;
      message: string;
      icon: string;
    }> = [];

    // 1. Check recent performance trend
    const recentSessions = sessions.slice(0, 5);
    const avgAccuracy = recentSessions.reduce((sum, s) => sum + s.accuracy, 0) / recentSessions.length;

    if (avgAccuracy >= 85) {
      recommendations.push({
        type: 'success',
        title: t("smartRecommendations.performance.excellentTitle"),
        message: t("smartRecommendations.performance.excellentMessage"),
        icon: ''
      });
    } else if (avgAccuracy < 60) {
      recommendations.push({
        type: 'warning',
        title: t("smartRecommendations.performance.lowTitle"),
        message: t("smartRecommendations.performance.lowMessage"),
        icon: ''
      });
    }

    // 2. Check exercise variety
    const exerciseTypes = new Set(sessions.map(s => s.exercise_name));
    if (exerciseTypes.size === 1) {
      recommendations.push({
        type: 'tip',
        title: t("smartRecommendations.variety.title"),
        message: t("smartRecommendations.variety.message"),
        icon: ''
      });
    }

    // 3. Check consistency
    const today = new Date();
    const lastSession = new Date(sessions[0].start_time);
    const daysSinceLastSession = Math.floor((today.getTime() - lastSession.getTime()) / (1000 * 60 * 60 * 24));

    if (daysSinceLastSession > 3) {
      recommendations.push({
        type: 'info',
        title: t("smartRecommendations.consistency.inactiveTitle"),
        message: `${daysSinceLastSession} ` + t("smartRecommendations.consistency.inactiveMessage"),
        icon: ''
      });
    } else if (daysSinceLastSession === 0) {
      recommendations.push({
        type: 'success',
        title: t("smartRecommendations.consistency.todayTitle"),
        message: t("smartRecommendations.consistency.todayMessage"),
        icon: ''
      });
    }

    // 4. Analyze common errors
    const allErrors: { [key: string]: number } = {};
    sessions.forEach(s => {
      s.errors?.forEach(e => {
        allErrors[e.name] = (allErrors[e.name] || 0) + e.count;
      });
    });

    const sortedErrors = Object.entries(allErrors).sort((a, b) => b[1] - a[1]);
    if (sortedErrors.length > 0 && sortedErrors[0][1] > 10) {
      recommendations.push({
        type: 'tip',
        title: t("smartRecommendations.errors.title"),
        message: t("smartRecommendations.errors.message", {
          error: sortedErrors[0][0],
          count: sortedErrors[0][1]
        }),
        icon: ''
      });
    }

    // 5. Check total reps progress
    const last5Sessions = sessions.slice(0, 5);
    const prev5Sessions = sessions.slice(5, 10);
    if (prev5Sessions.length > 0) {
      const recentAvgReps = last5Sessions.reduce((sum, s) => sum + s.total_reps, 0) / last5Sessions.length;
      const prevAvgReps = prev5Sessions.reduce((sum, s) => sum + s.total_reps, 0) / prev5Sessions.length;
      
      if (recentAvgReps > prevAvgReps * 1.2) {
        recommendations.push({
          type: 'success',
          title: t("smartRecommendations.progress.title"),
          message: t("smartRecommendations.progress.message", {
            percent: ((recentAvgReps - prevAvgReps) / prevAvgReps * 100).toFixed(0)
          }),
          icon: ''
        });
      }
    }

    // 6. Rest day recommendation
    const sessionsThisWeek = sessions.filter(s => {
      const sessionDate = new Date(s.start_time);
      const weekAgo = new Date(today);
      weekAgo.setDate(today.getDate() - 7);
      return sessionDate >= weekAgo;
    });

    if (sessionsThisWeek.length >= 6) {
      recommendations.push({
        type: 'info',
        title: t("smartRecommendations.rest.title"),
        message: t("smartRecommendations.rest.message"),
        icon: ''
      });
    }

    return recommendations.slice(0, 4); // Limit to 4 recommendations
  };

  const recommendations = getRecommendations();

  if (recommendations.length === 0) {
    return null;
  }

  const getColorClasses = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200';
      case 'warning':
        return 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800 text-orange-800 dark:text-orange-200';
      case 'info':
        return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200';
      case 'tip':
        return 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800 text-purple-800 dark:text-purple-200';
      default:
        return 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
      <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
        <span>{t("smartRecommendations.title")}</span>
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {recommendations.map((rec, index) => (
          <div
            key={index}
            className={`p-4 rounded-lg border-2 ${getColorClasses(rec.type)} transition-transform hover:scale-[1.02]`}
          >
            <div className="flex items-start gap-3">
              <span className="text-3xl flex-shrink-0">{rec.icon}</span>
              <div>
                <h4 className="font-bold mb-1">{rec.title}</h4>
                <p className="text-sm opacity-90">{rec.message}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
