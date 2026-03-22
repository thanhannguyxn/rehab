export const PatientCardSkeleton = () => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md animate-pulse">
      
      {/* Top Section */}
      <div className="flex items-start justify-between mb-4">
        <div>
          {/* Name */}
          <div className="h-6 w-40 bg-gray-300 rounded mb-2"></div>

          {/* Age + Gender */}
          <div className="h-4 w-24 bg-gray-200 rounded"></div>
        </div>

        {/* Username badge */}
        <div className="h-6 w-16 bg-gray-300 rounded-full"></div>
      </div>

      {/* Session section */}
      <div className="bg-gray-50 p-4 rounded-lg">
        {/* Label */}
        <div className="h-4 w-32 bg-gray-200 rounded mb-3"></div>

        <div className="flex justify-between items-center">
          <div>
            {/* Exercise */}
            <div className="h-5 w-32 bg-gray-300 rounded mb-2"></div>

            {/* Date */}
            <div className="h-4 w-20 bg-gray-200 rounded"></div>
          </div>

          {/* Accuracy */}
          <div className="h-8 w-16 bg-gray-300 rounded"></div>
        </div>
      </div>
    </div>
  );
};