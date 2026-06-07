import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { doctorAPI } from '../utils/api';

interface Props {
  exerciseId: string;
  exerciseName: string;
  onClose: () => void;
}

export function AssignExerciseModal({ exerciseId, exerciseName, onClose }: Props) {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['exercise-assignments', exerciseId],
    queryFn: () => doctorAPI.getExerciseAssignments(exerciseId),
  });

  const patients = data?.patients ?? [];

  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [note, setNote] = useState('');

  useEffect(() => {
    if (patients.length) {
      setSelected(new Set(patients.filter(p => p.assigned).map(p => p.id)));
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: () => doctorAPI.assignExercise(exerciseId, Array.from(selected), note || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exercise-assignments', exerciseId] });
      onClose();
    },
  });

  const toggle = (id: number) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md">
        {/* Header */}
        <div className="p-5 border-b dark:border-gray-700">
          <h2 className="text-lg font-bold text-gray-800 dark:text-white">Giao bài tập cho bệnh nhân</h2>
          <p className="text-sm text-[#0369a1] dark:text-blue-400 mt-0.5">{exerciseName}</p>
        </div>

        {/* Patient list */}
        <div className="p-5 max-h-72 overflow-y-auto">
          {isLoading ? (
            <p className="text-gray-400 text-sm text-center py-4">Đang tải...</p>
          ) : patients.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-4">Chưa có bệnh nhân nào.</p>
          ) : (
            <div className="space-y-2">
              {patients.map(p => (
                <label
                  key={p.id}
                  className="flex items-center gap-3 p-3 rounded-xl cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                >
                  <input
                    type="checkbox"
                    checked={selected.has(p.id)}
                    onChange={() => toggle(p.id)}
                    className="w-4 h-4 accent-[#0369a1]"
                  />
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white text-sm">{p.full_name}</p>
                    <p className="text-xs text-gray-400">@{p.username}</p>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Note */}
        <div className="px-5 pb-3">
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Ghi chú cho bệnh nhân (tùy chọn)..."
            rows={2}
            className="w-full text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-white rounded-lg px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-[#0369a1]"
          />
        </div>

        {/* Actions */}
        <div className="p-5 pt-2 flex gap-3">
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="flex-1 bg-[#0369a1] hover:bg-[#0284c7] text-white font-semibold py-2.5 rounded-xl transition disabled:opacity-50"
          >
            {mutation.isPending ? 'Đang lưu...' : `Lưu (${selected.size} bệnh nhân)`}
          </button>
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
          >
            Hủy
          </button>
        </div>
      </div>
    </div>
  );
}
