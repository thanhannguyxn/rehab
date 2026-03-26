import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { agentAPI } from '../utils/api';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

const RATE_LIMIT_COOLDOWN_SECONDS = 15;
const WELCOME_MSG = "I'm your Doctor Assistant. Ask about patient trends, clinical insights, or schedule exercises for your patients!";

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

export function DoctorAssistantChat() {
  const { user } = useAuth();
  const doctorName = user?.full_name?.trim() || user?.username || 'Doctor';

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    {
      id: 'welcome',
      role: 'assistant',
      content: `Welcome ${doctorName}! ${WELCOME_MSG}`,
    },
  ]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [cooldownUntil, setCooldownUntil] = useState<number>(0);
  const [isClearing, setIsClearing] = useState(false);

  // Load conversation history from backend on first open
  useEffect(() => {
    if (!isOpen) return;

    const loadHistory = async () => {
      try {
        const history = await agentAPI.getDoctorChatHistory(40);
        if (history.length === 0) return;

        const restored: ChatMessage[] = [
          {
            id: 'welcome',
            role: 'assistant',
            content: `Welcome back ${doctorName}! ${WELCOME_MSG}`,
          },
        ];

        for (const entry of history) {
          restored.push({
            id: String(entry.id),
            role: entry.role as 'user' | 'assistant',
            content: entry.content,
          });
        }

        setMessages(restored);
      } catch {
        // On error, keep the welcome message
      }
    };

    loadHistory();
  }, [isOpen, doctorName]);

  const remainingCooldown = useMemo(() => {
    const seconds = Math.ceil((cooldownUntil - Date.now()) / 1000);
    return seconds > 0 ? seconds : 0;
  }, [cooldownUntil, isSending, messages.length]);

  const canSend = input.trim().length > 0 && !isSending && remainingCooldown === 0;

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

  const handleSend = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || !canSend) return;

    setErrorText(null);
    pushMessage('user', trimmed);
    setInput('');
    setIsSending(true);

    try {
      const data = await agentAPI.doctorChat(trimmed);
      pushMessage('assistant', data.reply || 'No response returned from assistant.');
    } catch (error: unknown) {
      const err = error as { response?: { status?: number } };
      const status = err?.response?.status;
      if (status === 429) {
        setCooldownUntil(Date.now() + RATE_LIMIT_COOLDOWN_SECONDS * 1000);
        setErrorText(`Rate limit reached. Please retry in ${RATE_LIMIT_COOLDOWN_SECONDS}s.`);
      } else {
        setErrorText('Could not contact Doctor Assistant. Please try again.');
      }
      pushMessage(
        'assistant',
        'Doctor Assistant is temporarily unavailable. Please review patient dashboards and retry shortly.'
      );
    } finally {
      setIsSending(false);
    }
  };

  const handleClearChat = async () => {
    if (isClearing) return;
    setIsClearing(true);
    try {
      await agentAPI.clearDoctorChatHistory();
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: `Welcome ${doctorName}! ${WELCOME_MSG}`,
        },
      ]);
    } catch {
      setErrorText('Could not clear chat history. Please try again.');
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-8 right-8 w-14 h-14 rounded-full bg-gradient-to-r from-indigo-500 to-blue-500 hover:from-indigo-600 hover:to-blue-600 text-white shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center z-40"
        aria-label="Open Doctor Assistant"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/40 z-40" onClick={() => setIsOpen(false)} />
      )}

      {isOpen && (
        <div className="fixed bottom-8 right-8 w-96 h-[620px] bg-white dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-2xl flex flex-col z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Doctor Assistant</h3>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Clinical planning and patient summary support
              </p>
            </div>
            <div className="flex items-center gap-1">
              {/* Clear chat button */}
              <button
                onClick={handleClearChat}
                disabled={isClearing}
                title="Clear chat history"
                className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-gray-500 dark:text-gray-400 disabled:opacity-50"
                aria-label="Clear chat"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                aria-label="Close Doctor Assistant"
              >
                <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Message list */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50 dark:bg-black/30">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[80%] px-4 py-2 rounded-lg text-sm leading-relaxed ${
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
                  Assistant is thinking...
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSend} className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={3}
              placeholder="Ask about a patient trend, risk signal, or next clinical action..."
              className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={isSending || remainingCooldown > 0}
            />
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs text-gray-600 dark:text-gray-400 min-h-[16px] flex-1">
                {remainingCooldown > 0 ? `Retry in ${remainingCooldown}s` : errorText || ''}
              </p>
              <button
                type="submit"
                disabled={!canSend}
                className="px-4 py-2 rounded-lg text-sm font-semibold bg-gradient-to-r from-indigo-500 to-blue-500 hover:from-indigo-600 hover:to-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                Send
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
