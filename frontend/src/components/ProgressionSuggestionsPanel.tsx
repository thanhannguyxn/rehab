import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { doctorAPI } from '../utils/api';
import type { ProgressionSuggestion } from '../utils/types';

const EXERCISE_LABELS: Record<string, string> = {
  arm_raise: 'Nâng tay',
  squat: 'Gập gối',
  calf_raise: 'Nâng gót chân',
  single_leg_stand: 'Đứng một chân',
};

function exerciseLabel(name: string): string {
  return EXERCISE_LABELS[name] ?? name;
}

function DeltaBadge({ from, to, unit }: { from: number | null; to: number | null; unit: string }) {
  if (from == null || to == null) return <span className="text-gray-400">—</span>;
  const better = to > from;
  return (
    <span className="font-semibold">
      {from}{unit} → <span className={better ? 'text-green-600' : 'text-orange-500'}>{to}{unit}</span>
    </span>
  );
}

function SuggestionCard({
  s,
  onAction,
}: {
  s: ProgressionSuggestion;
  onAction: (id: number, action: 'approve' | 'reject', note: string) => void;
}) {
  const [note, setNote] = useState('');
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <p className="font-bold text-gray-800 dark:text-white text-base">{s.patient_name}</p>
          <p className="text-sm text-[#0369a1] dark:text-blue-400 font-medium">{exerciseLabel(s.exercise_name)}</p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-2xl font-bold text-green-600">{s.avg_accuracy.toFixed(0)}%</p>
          <p className="text-xs text-gray-500">{s.trigger_session_count} buổi liên tiếp</p>
        </div>
      </div>

      {/* Deltas */}
      <div className="grid grid-cols-3 gap-2 text-sm mb-3">
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 text-center">
          <p className="text-xs text-gray-500 mb-1">Số lần</p>
          <DeltaBadge from={s.current_reps} to={s.suggested_reps} unit=" reps" />
        </div>
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 text-center">
          <p className="text-xs text-gray-500 mb-1">Độ khó</p>
          <DeltaBadge from={s.current_difficulty} to={s.suggested_difficulty} unit="" />
        </div>
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 text-center">
          <p className="text-xs text-gray-500 mb-1">Nghỉ (giây)</p>
          <DeltaBadge from={s.current_rest_seconds} to={s.suggested_rest_seconds} unit="s" />
        </div>
      </div>

      {/* Note input toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 underline mb-2"
      >
        {expanded ? 'Ẩn ghi chú' : 'Thêm ghi chú bác sĩ'}
      </button>

      {expanded && (
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Ghi chú (tùy chọn)..."
          rows={2}
          className="w-full text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-white rounded-lg px-3 py-2 mb-3 resize-none focus:outline-none focus:ring-2 focus:ring-[#0369a1]"
        />
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => onAction(s.id, 'approve', note)}
          className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold py-2 rounded-lg transition"
        >
          Duyệt
        </button>
        <button
          onClick={() => onAction(s.id, 'reject', note)}
          className="flex-1 bg-red-100 hover:bg-red-200 text-red-700 dark:bg-red-900/30 dark:hover:bg-red-900/50 dark:text-red-400 text-sm font-semibold py-2 rounded-lg transition"
        >
          Từ chối
        </button>
      </div>
    </div>
  );
}

export function ProgressionSuggestionsPanel() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['progression-suggestions', 'pending'],
    queryFn: () => doctorAPI.getProgressionSuggestions('pending'),
    refetchInterval: 60_000,
  });

  const suggestions: ProgressionSuggestion[] = data?.suggestions ?? [];

  const approveMutation = useMutation({
    mutationFn: ({ id, note }: { id: number; note: string }) =>
      doctorAPI.approveProgression(id, note || undefined),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['progression-suggestions'] }),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, note }: { id: number; note: string }) =>
      doctorAPI.rejectProgression(id, note || undefined),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['progression-suggestions'] }),
  });

  const handleAction = (id: number, action: 'approve' | 'reject', note: string) => {
    if (action === 'approve') approveMutation.mutate({ id, note });
    else rejectMutation.mutate({ id, note });
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-md p-6 border dark:border-gray-800 mb-8">
      {/* Title row */}
      <div className="flex items-center gap-3 mb-5">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Đề Xuất Tăng Cấp Độ</h2>
        {suggestions.length > 0 && (
          <span className="bg-orange-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
            {suggestions.length} mới
          </span>
        )}
      </div>

      {isLoading ? (
        <p className="text-gray-400 text-sm">Đang tải...</p>
      ) : suggestions.length === 0 ? (
        <p className="text-gray-500 dark:text-gray-400 text-sm py-4 text-center">
          Không có đề xuất nào đang chờ duyệt.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {suggestions.map((s) => (
            <SuggestionCard key={s.id} s={s} onAction={handleAction} />
          ))}
        </div>
      )}
    </div>
  );
}
