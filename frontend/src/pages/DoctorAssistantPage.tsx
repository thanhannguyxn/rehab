import { FormEvent, useEffect, useMemo, useState, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import type { Patient } from '../types';
import { agentAPI, doctorAPI } from '../utils/api';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

function renderMessageContent(content: string) {
  const lines = content.split('\n').map((line) => line.trim()).filter(Boolean);
  if (lines.length <= 1) {
    return <div className="whitespace-pre-wrap">{content}</div>;
  }

  return (
    <div className="space-y-1">
      {lines.map((line, idx) => {
        const cleanLine = line.replace(/^[-*]\s+/, '');
        const isBullet = /^[-*]\s+/.test(line);
        return (
          <div key={idx} className="whitespace-pre-wrap">
            {isBullet ? `• ${cleanLine}` : cleanLine}
          </div>
        );
      })}
    </div>
  );
}

const STARTER_PROMPTS = [
  'Tóm tắt bệnh nhân nguy cơ cao trong tuần này.',
  'Xu hướng nào cần theo dõi cho bệnh nhân đang chọn?',
  'Lập kế hoạch phục hồi ngắn gọn cho 7 ngày tới dựa trên lịch sử.',
];

export function DoctorAssistantPage() {
  const { user } = useAuth();
  const doctorName = user?.full_name?.trim() || user?.username || 'Doctor';

  const [searchParams, setSearchParams] = useSearchParams();
  const selectedFromQuery = searchParams.get('patientId');
  const initialPatientId = selectedFromQuery ? Number(selectedFromQuery) : null;

  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(
    Number.isFinite(initialPatientId) ? initialPatientId : null
  );
  const [isLoadingPatients, setIsLoadingPatients] = useState(true);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        `Xin chào Bác sĩ ${doctorName}! Tôi có thể giúp bạn xem xu hướng bệnh nhân, nhận diện rủi ro và lập kế hoạch phục hồi tiếp theo. ` +
        'Chọn bệnh nhân bên trái để phân tích chi tiết, hoặc hỏi về toàn bộ danh sách của bạn.',
    },
  ]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const selectedPatient = useMemo(
    () => patients.find((p) => p.id === selectedPatientId) || null,
    [patients, selectedPatientId]
  );

  const didFetch = useRef(false);

  useEffect(() => {
    if (didFetch.current) return;
    didFetch.current = true;
    const loadPatients = async () => {
      try {
        const data = await doctorAPI.getPatients();
        setPatients(data.patients || []);
      } catch (error) {
        setErrorText('Không thể tải danh sách bệnh nhân.');
      } finally {
        setIsLoadingPatients(false);
      }
    };

    loadPatients();
  }, []);

  const pushMessage = (role: 'user' | 'assistant', content: string) => {
    setMessages((prev) => [
      ...prev,
      {
        id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        role,
        content,
      },
    ]);
  };

  const resetThreadForScope = (patientId: number | null) => {
    const scopePatient = patientId ? patients.find((p) => p.id === patientId) : null;
    const scopeText = scopePatient
      ? `Đang xem: ${scopePatient.full_name} (ID ${scopePatient.id}).`
      : 'Đang xem: toàn bộ bệnh nhân của bạn.';

    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content:
          `Xin chào Bác sĩ ${doctorName}! Tôi có thể giúp bạn xem xu hướng bệnh nhân, nhận diện rủi ro và lập kế hoạch phục hồi tiếp theo. ` +
          `${scopeText} Hỏi về tóm tắt, tín hiệu rủi ro hoặc hành động tiếp theo.`,
      },
    ]);
    setErrorText(null);
    setInput('');
  };

  const choosePatient = (patientId: number | null) => {
    if (selectedPatientId === patientId) {
      return;
    }

    setSelectedPatientId(patientId);
    const nextParams = new URLSearchParams(searchParams);
    if (patientId) {
      nextParams.set('patientId', String(patientId));
    } else {
      nextParams.delete('patientId');
    }
    setSearchParams(nextParams);
    resetThreadForScope(patientId);
  };

  const sendMessage = async (messageText: string) => {
    const trimmed = messageText.trim();
    if (!trimmed || isSending) {
      return;
    }

    setErrorText(null);
    pushMessage('user', trimmed);
    setInput('');
    setIsSending(true);

    try {
      const data = await agentAPI.doctorChat(trimmed, selectedPatientId || undefined);
      pushMessage('assistant', data.reply || 'Trợ lý không trả về phản hồi.');
    } catch (error) {
      setErrorText('Không thể kết nối Trợ Lý Bác Sĩ. Vui lòng thử lại.');
      pushMessage('assistant', 'Trợ Lý Bác Sĩ tạm thời không khả dụng. Vui lòng thử lại sau.');
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await sendMessage(input);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="max-w-7xl mx-auto px-4 py-6 md:px-6 md:py-8">
        <div className="mb-6">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">Trợ Lý Bác Sĩ</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-300">
            Hỗ trợ AI phân tích hồ sơ bệnh nhân, xu hướng điều trị và lập kế hoạch lâm sàng.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-5">
          <aside className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white/90 dark:bg-gray-900/80 p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Danh Sách Bệnh Nhân</h2>
              <button
                onClick={() => choosePatient(null)}
                className="text-xs px-2.5 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                Xóa chọn
              </button>
            </div>

            {isLoadingPatients ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">Đang tải...</p>
            ) : patients.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">Không tìm thấy bệnh nhân nào.</p>
            ) : (
              <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
                {patients.map((patient) => {
                  const active = selectedPatientId === patient.id;
                  return (
                    <button
                      key={patient.id}
                      onClick={() => choosePatient(patient.id)}
                      className={`w-full text-left p-3 rounded-xl border transition ${
                        active
                          ? 'border-blue-600 bg-blue-50 dark:bg-[#075985]/20 dark:border-[#0369a1]'
                          : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-[#0284c7]'
                      }`}
                    >
                      <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{patient.full_name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">ID: {patient.id}</p>
                      {patient.last_session && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                          Last: {patient.last_session.exercise} ({patient.last_session.accuracy.toFixed(1)}%)
                        </p>
                      )}
                    </button>
                  );
                })}
              </div>
            )}

            <div className="mt-4 p-3 rounded-xl bg-gray-50 dark:bg-gray-800/70 border border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 dark:text-gray-400">Phạm vi hiện tại</p>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mt-1">
                {selectedPatient ? `${selectedPatient.full_name} (ID ${selectedPatient.id})` : 'Tất cả bệnh nhân của bạn'}
              </p>
            </div>
          </aside>

          <section className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white/90 dark:bg-gray-900/80 shadow-sm flex flex-col min-h-[72vh]">
            <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Không Gian Làm Việc</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Hỏi về xu hướng, tín hiệu rủi ro, tuân thủ điều trị và bước lâm sàng tiếp theo.
              </p>
            </div>

            <div className="px-5 pt-4 pb-2 flex flex-wrap gap-2 border-b border-gray-200/70 dark:border-gray-700/70">
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(prompt)}
                  disabled={isSending}
                  className="text-xs sm:text-sm px-3 py-1.5 rounded-full border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50"
                >
                  {prompt}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3 bg-gray-50/70 dark:bg-black/20">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[85%] px-4 py-3 rounded-xl text-sm leading-relaxed ${
                      message.role === 'assistant'
                        ? 'bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
                        : 'bg-[#0369a1] text-white'
                    }`}
                  >
                    {message.role === 'assistant' ? renderMessageContent(message.content) : message.content}
                  </div>
                </div>
              ))}

              {isSending && (
                <div className="flex justify-start">
                  <div className="px-4 py-2 rounded-lg bg-gray-200 text-gray-700 dark:bg-gray-800 dark:text-gray-200 text-sm">
                    Trợ lý đang phân tích...
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 space-y-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                rows={3}
                placeholder="Hỏi trợ lý về xu hướng bệnh nhân, tín hiệu rủi ro hoặc kế hoạch phục hồi tiếp theo..."
                className="w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[#0369a1]"
                disabled={isSending}
              />

              <div className="flex items-center justify-between gap-3">
                <p className="text-xs text-red-600 dark:text-red-400 min-h-[16px]">{errorText || ''}</p>
                <button
                  type="submit"
                  disabled={isSending || !input.trim()}
                  className="px-4 py-2.5 rounded-lg text-sm font-semibold bg-[#0369a1] hover:bg-[#0284c7] text-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Gửi
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
