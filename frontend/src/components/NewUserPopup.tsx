

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const NewUserPopup = ({ isOpen, onClose }: Props) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 dark:bg-black/90 backdrop-blur-sm flex items-center justify-center z-[60] p-4">
      <div className="bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-3xl shadow-2xl max-w-lg w-full p-8 text-center relative overflow-hidden animate-slide-in-right">
        <div className="absolute top-0 left-0 w-full h-2 bg-[#0284c7]"></div>
        <div className="w-20 h-20 bg-blue-50 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-10 h-10 text-[#0284c7]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Lưu ý
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-300 mb-8 leading-relaxed">
          Vui lòng thực hiện 1 trong 4 bài tập đánh giá dưới đây. Dựa trên kết quả tập luyện của bạn, bác sĩ và AI sẽ phân tích và giao các bài tập tiếp theo phù hợp nhất với tình trạng sức khoẻ thực tế.
        </p>
        <button
          onClick={onClose}
          className="w-full bg-[#0369a1] hover:bg-[#0284c7] text-white font-bold py-4 rounded-xl text-xl transition shadow-lg transform hover:scale-105"
        >
          Đã hiểu
        </button>
      </div>
    </div>
  );
};
