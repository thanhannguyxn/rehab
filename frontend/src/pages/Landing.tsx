import { useNavigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { useRef } from 'react';
import { useInView } from '../hooks/useInView';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from 'react-i18next';
import { GuestCoachPopup } from '../components/GuestCoachPopup';

export const Landing = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useTranslation();
  
  // Handler for CTA buttons
  const handleGetStarted = () => {
    if (user) {
      navigate('/exercise');
    } else {
      navigate('/login-choice');
    }
  };

  // Refs for scroll animations
  const heroRef = useRef<HTMLElement>(null);
  const featuresRef = useRef<HTMLElement>(null);
  const howItWorksRef = useRef<HTMLElement>(null);
  const exercisesRef = useRef<HTMLElement>(null);
  const ctaRef = useRef<HTMLElement>(null);

  // Check if sections are in view
  const isHeroInView = useInView(heroRef, 0.1);
  const isFeaturesInView = useInView(featuresRef, 0.1);
  const isHowItWorksInView = useInView(howItWorksRef, 0.1);
  const isExercisesInView = useInView(exercisesRef, 0.1);
  const isCtaInView = useInView(ctaRef, 0.1);

  return (
    <div className="min-h-screen bg-white dark:bg-black text-gray-900 dark:text-white transition-colors duration-300">
      {/* Navbar Component */}
      <Navbar />
      {!user && <GuestCoachPopup />}

      {/* Hero Section - Full Screen */}
      <section 
        ref={heroRef}
        id="home" 
        className={`relative min-h-screen flex items-center justify-center overflow-hidden transition-all duration-700 ${
          isHeroInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        {/* Background */}
        <div className="absolute inset-0 bg-gray-100 dark:bg-gray-900 transition-colors duration-300"></div>
        
        <div className="relative max-w-6xl mx-auto px-6 py-20 text-center z-10">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-gray-200/80 dark:bg-gray-800/50 backdrop-blur-sm border border-gray-300 dark:border-gray-700 px-4 py-2 rounded-full mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-600 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#0369a1]"></span>
            </span>
            <span className="text-sm text-gray-700 dark:text-gray-300 font-medium">{t("landing.heroBadge")}</span>
          </div>

          {/* Main Heading */}
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-black mb-6 leading-tight">
            <span className="block text-gray-900 dark:text-white mb-2">{t("landing.heroTitle1")}</span>
            <span className="block text-[#0369a1] dark:text-blue-600">
              {t("landing.heroTitle2")}
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed">
            {t("landing.heroSubtitle")}
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row justify-center gap-4 mb-16">
            <button
              onClick={handleGetStarted}
              className="group bg-[#0369a1] hover:bg-[#0284c7] text-white px-8 py-4 rounded-xl font-bold text-lg transition shadow-xl shadow-[#0369a1]/30 hover:shadow-2xl hover:shadow-[#0369a1]/40 transform hover:scale-105"
            >
              {t("landing.getStarted")}
              <span className="inline-block ml-2 group-hover:translate-x-1 transition-transform">→</span>
            </button>
            <a
              href="https://www.youtube.com/watch?v=srit68t8LGs&t=34s"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white px-8 py-4 rounded-xl font-bold text-lg transition"
            >
              {t("landing.watchTutorial")}
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-8 max-w-3xl mx-auto pt-8 border-t border-gray-300 dark:border-gray-800">
            <div>
              <div className="text-3xl md:text-4xl font-bold text-[#0369a1] dark:text-blue-600 mb-1">
                4+
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-500 font-medium">{t("landing.stats1Title")}</div>
            </div>
            <div>
              <div className="text-3xl md:text-4xl font-bold text-[#0369a1] dark:text-blue-600 mb-1">
                95%+
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-500 font-medium">{t("landing.stats2Title")}</div>
            </div>
            <div>
              <div className="text-3xl md:text-4xl font-bold text-[#0369a1] dark:text-blue-600 mb-1">
                {t("landing.stats3Subtitle")}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-500 font-medium">{t("landing.stats3Title")}</div>
            </div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <svg className="w-6 h-6 text-gray-400 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* Features Section */}
      <section 
        ref={featuresRef}
        id="features" 
        className={`py-32 bg-gray-50 dark:bg-black transition-all duration-700 ${
          isFeaturesInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-20">
            <h2 className="text-5xl md:text-6xl font-black text-gray-900 dark:text-white mb-6">
              {t("landing.featuresTitle")}
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              {t("landing.featuresSubtitle")}
            </p>
          </div>

          {/* Feature Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Feature 1 */}
            <div className="group bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 hover:border-[#0369a1]/50 p-8 rounded-2xl hover:shadow-2xl hover:shadow-[#0369a1]/20 transition-all duration-300">
              <div className="bg-[#0369a1]/20 p-4 rounded-xl w-fit mb-6 group-hover:scale-110 transition-transform">
                <svg className="w-8 h-8 text-[#0369a1] dark:text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">{t("landing.gridTitle1")}</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                {t("landing.gridSubtitle1")}
              </p>
            </div>

            {/* Feature 2 */}
            <div className="group bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 hover:border-[#0369a1]/50 p-8 rounded-2xl hover:shadow-2xl hover:shadow-[#0369a1]/20 transition-all duration-300">
              <div className="bg-[#0369a1]/20 p-4 rounded-xl w-fit mb-6 group-hover:scale-110 transition-transform">
                <svg className="w-8 h-8 text-[#0369a1] dark:text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">{t("landing.gridTitle2")}</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                {t("landing.gridSubtitle2")}
              </p>
            </div>

            {/* Feature 3 */}
            <div className="group bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 hover:border-[#0369a1]/50 p-8 rounded-2xl hover:shadow-2xl hover:shadow-[#0369a1]/20 transition-all duration-300">
              <div className="bg-[#0369a1]/20 p-4 rounded-xl w-fit mb-6 group-hover:scale-110 transition-transform">
                <svg className="w-8 h-8 text-[#0369a1] dark:text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">{t("landing.gridTitle3")}</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                {t("landing.gridSubtitle3")}
              </p>
            </div>

            {/* Feature 4 */}
            <div className="group bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 hover:border-[#0369a1]/50 p-8 rounded-2xl hover:shadow-2xl hover:shadow-[#0369a1]/20 transition-all duration-300">
              <div className="bg-[#0369a1]/20 p-4 rounded-xl w-fit mb-6 group-hover:scale-110 transition-transform">
                <svg className="w-8 h-8 text-[#0369a1] dark:text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">{t("landing.gridTitle4")}</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                {t("landing.gridSubtitle4")}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section 
        ref={howItWorksRef}
        id="how-it-works" 
        className={`py-32 bg-white dark:bg-gray-900 relative overflow-hidden transition-all duration-700 ${
          isHowItWorksInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        {/* Background Decoration */}
        <div className="absolute top-0 left-0 w-full h-1 bg-[#0369a1] opacity-40"></div>
        
        <div className="max-w-7xl mx-auto px-6 relative">
          {/* Section Header */}
          <div className="text-center mb-20">
            <h2 className="text-5xl md:text-6xl font-black text-gray-900 dark:text-white mb-6">
              {t("landing.howItWorks")}
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              {t("landing.howItWorksSubtitle")}
            </p>
          </div>

          {/* Steps */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Connecting Lines */}
            <div className="hidden md:block absolute top-24 left-0 right-0 h-0.5 bg-[#0369a1] opacity-30"></div>

            {/* Step 1 */}
            <div className="relative">
              <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-8 rounded-2xl text-center relative z-10 transition-colors duration-300">
                <div className="bg-[#0369a1] text-white w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-6 shadow-lg shadow-[#0369a1]/50">
                  1
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t("landing.step1Title")}</h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  {t("landing.step1Subtitle")}
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="relative">
              <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-8 rounded-2xl text-center relative z-10 transition-colors duration-300">
                <div className="bg-[#0369a1] text-white w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-6 shadow-lg shadow-[#0369a1]/50">
                  2
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t("landing.step2Title")}</h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  {t("landing.step2Subtitle")}
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="relative">
              <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-8 rounded-2xl text-center relative z-10 transition-colors duration-300">
                <div className="bg-[#0369a1] text-white w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-6 shadow-lg shadow-[#0369a1]/50">
                  3
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t("landing.step3Title")}</h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  {t("landing.step3Subtitle")}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Exercises Section */}
      <section 
        ref={exercisesRef}
        className={`py-32 bg-gray-100 dark:bg-black transition-all duration-700 ${
          isExercisesInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-20">
            <h2 className="text-5xl md:text-6xl font-black text-gray-900 dark:text-white mb-6">
              {t("landing.exercisesTitle")}
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              {t("landing.exercisesSubtitle")}
            </p>
          </div>

          {/* Exercise Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              { name: t("landing.exercise1Title"), desc: t("landing.exercise1Subtitle") },
              { name: t("landing.exercise2Title"), desc: t("landing.exercise2Subtitle") },
              { name: t("landing.exercise3Title"), desc: t("landing.exercise3Subtitle") },
              { name: t("landing.exercise4Title"), desc: t("landing.exercise4Subtitle") },
            ].map((exercise, idx) => (
              <div key={idx} className="group bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 hover:border-[#0369a1]/50 p-8 rounded-2xl hover:shadow-2xl hover:shadow-[#0369a1]/20 transition-all duration-300 cursor-pointer">
                <div className="flex items-center gap-4 mb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">{exercise.name}</h3>
                    <p className="text-gray-600 dark:text-gray-400">{exercise.desc}</p>
                  </div>
                </div>
                <div className="flex items-center text-[#0369a1] dark:text-blue-600 font-semibold group-hover:translate-x-2 transition-transform">
                  {t("landing.findOutMore")} →
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section 
        ref={ctaRef}
        className={`py-32 bg-gray-50 dark:bg-gray-900 relative overflow-hidden transition-all duration-700 ${
          isCtaInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}
      >
        {/* Background Glow */}
        
        <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
          <h2 className="text-5xl md:text-6xl font-black text-gray-900 dark:text-white mb-6">
            {t("landing.ctaTitle")}
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-12 leading-relaxed">
            {t("landing.ctaSubtitle")}
          </p>
          <button
            onClick={handleGetStarted}
            className="inline-flex items-center gap-2 bg-[#0369a1] hover:bg-[#0284c7] text-white px-10 py-5 rounded-xl font-bold text-xl transition shadow-2xl shadow-[#0369a1]/40 hover:shadow-[#0369a1]/60 transform hover:scale-105"
          >
            {t("landing.ctaButton")}
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </div>
      </section>
    </div>
  );
};