import { FormEvent, useEffect, useMemo, useState } from 'react';
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
  'Summarize high-risk patients in my panel this week.',
  'What trend should I monitor for this selected patient?',
  'Give me a concise rehab plan for the next 7 days based on history.',
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
        `Welcome ${doctorName}! I can help you review patient trends, highlight risks, and draft next-step rehab plans. ` +
        'Select a patient on the left for focused analysis, or ask about your whole panel.',
    },
  ]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const selectedPatient = useMemo(
    () => patients.find((p) => p.id === selectedPatientId) || null,
    [patients, selectedPatientId]
  );

  useEffect(() => {
    const loadPatients = async () => {
      try {
        const data = await doctorAPI.getPatients();
        setPatients(data.patients || []);
      } catch (error) {
        setErrorText('Could not load patient list for assistant context.');
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
      ? `Current scope: ${scopePatient.full_name} (ID ${scopePatient.id}).`
      : 'Current scope: all patients in your panel.';

    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content:
          `Welcome ${doctorName}! I can help you review patient trends, highlight risks, and draft next-step rehab plans. ` +
          `${scopeText} Ask for a summary, risk signals, or next actions.`,
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
      pushMessage('assistant', data.reply || 'No response returned from assistant.');
    } catch (error) {
      setErrorText('Could not contact Doctor Assistant. Please try again.');
      pushMessage('assistant', 'Doctor Assistant is temporarily unavailable. Please retry shortly.');
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await sendMessage(input);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <div className="max-w-7xl mx-auto px-4 py-6 md:px-6 md:py-8">
        <div className="mb-6">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">Doctor Assistant</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-300">
            AI support for patient document reading, trend analysis, and next-step clinical planning.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-5">
          <aside className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white/90 dark:bg-gray-900/80 p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Patient Context</h2>
              <button
                onClick={() => choosePatient(null)}
                className="text-xs px-2.5 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                Clear
              </button>
            </div>

            {isLoadingPatients ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">Loading patients...</p>
            ) : patients.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">No patients found in your panel.</p>
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
                          ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-950/40 dark:border-indigo-500'
                          : 'border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-600'
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
              <p className="text-xs text-gray-500 dark:text-gray-400">Current scope</p>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mt-1">
                {selectedPatient ? `${selectedPatient.full_name} (ID ${selectedPatient.id})` : 'All patients in your panel'}
              </p>
            </div>
          </aside>

          <section className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white/90 dark:bg-gray-900/80 shadow-sm flex flex-col min-h-[72vh]">
            <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Assistant Workspace</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Ask for trend summaries, risk flags, adherence insights, and suggested rehab next actions.
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
                        : 'bg-gradient-to-r from-indigo-500 to-blue-500 text-white'
                    }`}
                  >
                    {message.role === 'assistant' ? renderMessageContent(message.content) : message.content}
                  </div>
                </div>
              ))}

              {isSending && (
                <div className="flex justify-start">
                  <div className="px-4 py-2 rounded-lg bg-gray-200 text-gray-700 dark:bg-gray-800 dark:text-gray-200 text-sm">
                    Assistant is analyzing...
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 space-y-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                rows={3}
                placeholder="Ask the assistant to analyze patient trends, risk signals, or recommend next rehab actions..."
                className="w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
                disabled={isSending}
              />

              <div className="flex items-center justify-between gap-3">
                <p className="text-xs text-red-600 dark:text-red-400 min-h-[16px]">{errorText || ''}</p>
                <button
                  type="submit"
                  disabled={isSending || !input.trim()}
                  className="px-4 py-2.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-indigo-500 to-blue-500 hover:from-indigo-600 hover:to-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Send
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
