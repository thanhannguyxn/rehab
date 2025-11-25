import React from 'react';
import { useLocation } from 'react-router-dom';
import { Navbar } from './Navbar';
import Footer from './Footer';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  
  // Không hiển thị navbar trên trang landing
  const isLandingPage = location.pathname === '/';
  const isLoginPage = location.pathname.includes('/login');
  
  // Hiển thị navbar cho các trang dashboard và protected routes
  const showNavbar = !isLandingPage && !isLoginPage;
  
  // Chỉ ẩn footer ở trang login và login choice
  const showFooter = !isLoginPage;

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {showNavbar && <Navbar />}
      <main className="flex-grow">
        {children}
      </main>
      {showFooter && <Footer />}
    </div>
  );
};

export default Layout;
