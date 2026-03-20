import { ErrorBoundary } from 'react-error-boundary';
import { useTranslation } from 'react-i18next';

function ErrorFallback() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-md text-center">
        <h2 className="text-2xl font-bold text-red-600 mb-4">
          {t('errorFallback.title')}
        </h2>
        <p className="text-gray-600">
          {t('errorFallback.message')}
        </p>
      </div>
    </div>
  );
}

export const AppErrorBoundary = ({ children }: { children: React.ReactNode }) => {
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, info) => {
        console.error('Error caught:', error, info);
      }}
    >
      {children}
    </ErrorBoundary>
  );
};