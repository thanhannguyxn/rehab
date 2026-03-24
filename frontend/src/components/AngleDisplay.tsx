import type { PoseAngles } from '../types';
import { useTranslation } from 'react-i18next';

interface AngleDisplayProps {
  angles?: PoseAngles;
  exerciseType: string;
  isDetected: boolean; // THÊM: Biết có detect được người không
}

export const AngleDisplay = ({ angles, exerciseType, isDetected }: AngleDisplayProps) => {
  const { t } = useTranslation();

  const labelByKey: Record<string, string> = {
    left_knee: t("angleDisplay.labels.leftKnee"),
    right_knee: t("angleDisplay.labels.rightKnee"),
    left_shoulder: t("angleDisplay.labels.leftShoulder"),
    right_shoulder: t("angleDisplay.labels.rightShoulder"),
    left_ankle: t("angleDisplay.labels.leftAnkle"),
    right_ankle: t("angleDisplay.labels.rightAnkle"),
  };

  const getAngleColor = (angle: number, target: number, direction: 'up' | 'down') => {
    if (direction === 'up') {
      if (angle >= target) return 'text-green-700 bg-green-100 dark:text-green-400 dark:bg-green-900/30';
      if (angle >= target - 20) return 'text-yellow-700 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30';
      return 'text-red-700 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
    } else {
      if (angle <= target) return 'text-green-700 bg-green-100 dark:text-green-400 dark:bg-green-900/30';
      if (angle <= target + 20) return 'text-yellow-700 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30';
      return 'text-red-700 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
    }
  };

  const getProgressPercent = (angle: number, target: number, direction: 'up' | 'down') => {
    if (direction === 'up') {
      return Math.min((angle / target) * 100, 100);
    } else {
      return Math.min(((180 - angle) / (180 - target)) * 100, 100);
    }
  };

  // Determine which angles to display based on exercise type
  const angleConfigs: Array<{ key: string; label: string; target: number; direction: 'up' | 'down' }> = [];

  if (exerciseType === 'arm_raise') {
    angleConfigs.push(
      { key: 'left_shoulder', label: t("angleDisplay.labels.leftShoulder"), target: 160, direction: 'up' },
      { key: 'right_shoulder', label: t("angleDisplay.labels.rightShoulder"), target: 160, direction: 'up' }
    );
  } else if (exerciseType === 'squat') {
    angleConfigs.push(
      { key: 'left_knee', label: t("angleDisplay.labels.leftKnee"), target: 90, direction: 'down' },
      { key: 'right_knee', label: t("angleDisplay.labels.rightKnee"), target: 90, direction: 'down' }
    );
  } else if (exerciseType === 'single_leg_stand') {
    angleConfigs.push(
        { key: 'left_knee', label: t("angleDisplay.labels.leftKnee"), target: 90, direction: 'down' },
        { key: 'right_knee', label: t("angleDisplay.labels.rightKnee"), target: 90, direction: 'down' }
    );
  } else if (exerciseType === 'calf_raise') {
    angleConfigs.push(
        { key: 'left_ankle', label: t("angleDisplay.labels.leftAnkle"), target: 140, direction: 'up' },
        { key: 'right_ankle', label: t("angleDisplay.labels.rightAnkle"), target: 140, direction: 'up' }
    );
  }

  // Fallback for new/custom exercises that do not have a predefined display mapping.
  if (angleConfigs.length === 0 && angles) {
    const fallbackOrder = ['left_knee', 'right_knee', 'left_shoulder', 'right_shoulder', 'left_ankle', 'right_ankle'];
    const usableKeys = fallbackOrder.filter((key) => typeof angles[key] === 'number');

    for (const key of usableKeys.slice(0, 4)) {
      const target = key.includes('shoulder') ? 160 : key.includes('ankle') ? 140 : 90;
      const direction: 'up' | 'down' = key.includes('shoulder') || key.includes('ankle') ? 'up' : 'down';
      angleConfigs.push({
        key,
        label: labelByKey[key] || key,
        target,
        direction,
      });
    }
  }
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg p-6 shadow-md border border-gray-200 dark:border-gray-700">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        {t("angleDisplay.title")}
      </h3>

      {!isDetected ? (
        // Hiển thị khi chưa detect được người
        <div className="text-center py-8">
          <div className="text-6xl mb-4">🎥</div>
          <p className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">
            {t("angleDisplay.notDetected.title")}
          </p>
          <p className="text-base text-gray-600 dark:text-gray-400">
            {t("angleDisplay.notDetected.subtitle")}
          </p>
        </div>
      ) : !angles ? (
        // Đang detect nhưng chưa có angles
        <div className="text-center py-8">
          <div className="animate-pulse">
            <p className="text-lg text-gray-700 dark:text-gray-300">{t("angleDisplay.analyzing")}</p>
          </div>
        </div>
      ) : (
        // Hiển thị angles
        <div className="space-y-4">
          {angleConfigs.map((config) => {
            const angleValue = angles[config.key] || 0;
            const colorClass = getAngleColor(angleValue, config.target, config.direction);
            const progress = getProgressPercent(angleValue, config.target, config.direction);

            return (
              <div key={config.key} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-base font-semibold text-gray-800 dark:text-gray-200">
                    {config.label}
                  </span>
                  <span className={`text-2xl font-bold px-3 py-1 rounded-lg ${colorClass}`}>
                    {Math.round(angleValue)}°
                  </span>
                </div>
                
                {/* Progress bar */}
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${
                      progress >= 100
                        ? 'bg-green-500 dark:bg-green-600'
                        : progress >= 80
                        ? 'bg-yellow-500 dark:bg-yellow-600'
                        : 'bg-red-500 dark:bg-red-600'
                    }`}
                    style={{ width: `${Math.max(progress, 5)}%` }}
                  />
                </div>
                
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                  <span>{t("angleDisplay.current")}: {Math.round(angleValue)}°</span>
                  <span>{t("angleDisplay.target")}: {config.target}°</span>
                </div>
              </div>
            );
          })}

            {/* Tip */}
            <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-700 dark:text-gray-400 italic">
                {exerciseType === 'arm_raise' 
                ? t("angleDisplay.tips.armRaise")
                : exerciseType === 'squat'
                ? t("angleDisplay.tips.squat")
                : exerciseType === 'single_leg_stand'
                ? t("angleDisplay.tips.singleLegStand")
                : exerciseType === 'calf_raise' 
                ? t("angleDisplay.tips.calfRaise")
                : ''
                }
            </p>
            </div>
        </div>
      )}
    </div>
  );
};