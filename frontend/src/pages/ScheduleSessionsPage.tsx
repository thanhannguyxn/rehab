import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

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
  const [isLoading, setIsLoading] = useState(true);
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);

  useEffect(() => {
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

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-blue-600 text-white p-6 shadow-lg">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Schedule Session</h1>
            <p className="text-lg mt-1">Your doctor-created rehabilitation schedule list</p>
          </div>
          <Link
            to="/exercise"
            className="bg-white text-blue-600 px-5 py-3 rounded-lg font-semibold hover:bg-blue-50 transition"
          >
            Start Exercise
          </Link>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {isLoading ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center text-lg text-gray-600">Loading schedules...</div>
        ) : schedules.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-10 text-center">
            <p className="text-2xl text-gray-700">No scheduled sessions yet</p>
            <p className="text-gray-500 mt-2">When your doctor creates one, it will appear here.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {schedules.map((item) => (
              <div key={item.id} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                  <div>
                    <p className="text-xl font-bold text-gray-900">{item.exercise_name}</p>
                    <p className="text-sm text-gray-600 mt-1">Scheduled for: {formatScheduleDate(item.scheduled_for)}</p>
                    <p className="text-sm text-gray-600">Doctor: {item.doctor_name}</p>
                    {item.note && <p className="text-sm text-gray-500 mt-1">Note: {item.note}</p>}
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                        item.is_read ? 'bg-gray-100 text-gray-700' : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {item.is_read ? 'Seen' : 'New'}
                    </span>

                    {!item.is_read && (
                      <button
                        onClick={() => markRead(item.id)}
                        className="px-3 py-2 rounded-lg text-sm font-medium border border-blue-300 text-blue-700 hover:bg-blue-50"
                      >
                        Mark as seen
                      </button>
                    )}

                    <Link
                      to="/exercise"
                      className="px-3 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700"
                    >
                      Open
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
