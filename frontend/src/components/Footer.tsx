import React from 'react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
          {/* Brand */}
          <div className="text-center md:text-left">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">
              Hệ Thống Phục Hồi Chức Năng Rehab AI
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Hệ thống phục hồi chức năng sử dụng AI để theo dõi và phân tích chuyển động,
              giúp bác sĩ và bệnh nhân quản lý quá trình điều trị hiệu quả hơn
            </p>
          </div>

          {/* Contact */}
          <div className="text-center md:text-right flex flex-col justify-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <a 
                href="mailto:support@rehab-system.com" 
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                HN 2.2
              </a>
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <a 
                href="tel:+84123456789" 
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Dự án của sinh viên Swinburne
              </a>
            </p>
          </div>
        </div>

        {/* Copyright - Separate Bottom Section */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            © {currentYear} Rehab AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
