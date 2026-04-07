export const PatientHistorySkeleton = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-black">
      <div className="max-w-7xl mx-auto p-6 animate-pulse">

        {/* Title */}
        <div className="mb-8">
          <div className="h-12 w-96 bg-gray-300 dark:bg-gray-700 rounded mb-2"></div>
          <div className="h-6 w-64 bg-gray-200 dark:bg-gray-600 rounded"></div>
        </div>

        {/* Recommendations */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 mb-6">
          <div className="h-6 w-48 bg-gray-300 dark:bg-gray-700 rounded mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 w-full bg-gray-200 dark:bg-gray-600 rounded"></div>
            <div className="h-4 w-5/6 bg-gray-200 dark:bg-gray-600 rounded"></div>
          </div>
        </div>

        {/* Heatmap */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 mb-6">
          <div className="h-6 w-40 bg-gray-300 dark:bg-gray-700 rounded mb-4"></div>
          <div className="grid grid-cols-7 gap-2">
            {Array.from({ length: 35 }).map((_, i) => (
              <div key={i} className="h-6 bg-gray-200 dark:bg-gray-600 rounded"></div>
            ))}
          </div>
        </div>

        {/* Weekly Goal */}
        <div className="bg-gray-300 dark:bg-gray-700 rounded-xl p-6 mb-6">
          <div className="h-6 w-40 bg-gray-400 rounded mb-3"></div>
          <div className="h-4 w-full bg-gray-400 rounded"></div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-6">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-white dark:bg-gray-800 p-6 rounded-lg">
              <div className="h-4 w-24 bg-gray-300 dark:bg-gray-700 rounded mb-3"></div>
              <div className="h-10 w-16 bg-gray-400 dark:bg-gray-600 rounded mx-auto"></div>
            </div>
          ))}
        </div>

        {/* Session List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
          <div className="h-6 w-48 bg-gray-300 dark:bg-gray-700 rounded mb-4"></div>

          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="p-4 border rounded-lg">
                <div className="h-4 w-1/3 bg-gray-300 dark:bg-gray-700 rounded mb-2"></div>
                <div className="h-3 w-1/2 bg-gray-200 dark:bg-gray-600 rounded"></div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};