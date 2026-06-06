import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface GuestCoachPopupProps {
  visible?: boolean;
}

export function GuestCoachPopup({ visible = true }: GuestCoachPopupProps) {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const closeAndMarkSeen = () => {
    setIsOpen(false);
    localStorage.setItem('guestCoachWelcomeSeen', '1');
  };

  useEffect(() => {
    if (!visible) {
      return;
    }

    const hasSeenWelcome = localStorage.getItem('guestCoachWelcomeSeen') === '1';
    if (!hasSeenWelcome) {
      setIsOpen(true);
    }
  }, [visible]);

  if (!visible) {
    return null;
  }

  return (
    <div className="fixed bottom-6 right-6 z-[70]">
      {isOpen && (
        <div className="mb-4 w-[22rem] sm:w-[26rem] rounded-[1.75rem] bg-white/95 dark:bg-gray-900/95 shadow-[0_30px_60px_-25px_rgba(17,24,39,0.55)] border border-gray-200/80 dark:border-gray-700/70 p-4 sm:p-5">
          <div className="relative pl-16 sm:pl-20">
            <button
              onClick={closeAndMarkSeen}
              aria-label="Close welcome message"
              className="absolute -top-1 right-0 h-8 w-8 rounded-full text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 dark:text-gray-400 dark:hover:text-gray-100 transition-colors"
            >
              ×
            </button>

            <div className="absolute left-0 top-0">
              <div className="relative h-12 w-12 sm:h-14 sm:w-14 rounded-full bg-[#0B1545] flex items-center justify-center text-white shadow-md">
                <svg className="h-6 w-6 sm:h-7 sm:w-7" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 4a2 2 0 00-2 2v4h6V4H6zm8 0v6h6V6a2 2 0 00-2-2h-4zM4 14v4a2 2 0 002 2h4v-6H4zm10 6h4a2 2 0 002-2v-4h-6v6z" />
                </svg>
              </div>
              <div className="absolute -right-1 top-8 h-10 w-10 sm:h-11 sm:w-11 rounded-full border-[2px] border-[#3B4DDB] bg-white dark:bg-gray-900 flex items-center justify-center text-[#3B4DDB] shadow">
                <svg className="h-5 w-5 sm:h-6 sm:w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.8}
                    d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.87 9.87 0 01-4.25-.95L3 20l1.39-3.72A7.93 7.93 0 013 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
              </div>
            </div>

            <p className="text-xl sm:text-2xl font-medium text-gray-900 dark:text-gray-100">Rehab Bot</p>
            <div className="mt-2 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/80 dark:border-gray-700/60 px-4 py-4">
              <p className="text-xl sm:text-2xl leading-snug text-gray-900 dark:text-gray-100">
                Hi welcome to our Rehabilitation system
              </p>
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
              <button
                onClick={closeAndMarkSeen}
                className="rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 py-2 px-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                Later
              </button>
              <button
                onClick={() => navigate('/login-choice')}
                className="rounded-lg bg-[#0369a1] hover:bg-[#0284c7] text-white font-semibold py-2.5 px-4 transition-colors"
              >
                Chat with Coach
              </button>
            </div>
          </div>
        </div>
      )}

      <button
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Open guest coach"
        className="relative h-14 w-14 rounded-full bg-[#0369a1] hover:bg-[#0284c7] text-white shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center"
      >
        <svg className="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.87 9.87 0 01-4.25-.95L3 20l1.39-3.72A7.93 7.93 0 013 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        {!isOpen && <span className="absolute -top-1 -right-1 h-3.5 w-3.5 rounded-full bg-emerald-400 border-2 border-white" />}
      </button>
    </div>
  );
}
