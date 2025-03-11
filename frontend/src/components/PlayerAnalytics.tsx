import React from 'react';

const PlayerAnalytics: React.FC = () => {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6 text-blue-700">Player Analytics</h1>
      <div className="bg-white shadow-md rounded-lg p-6">
        <p className="text-gray-600">
          In-depth player performance analysis, including batting, bowling, 
          and overall career statistics. Detailed insights into individual 
          player metrics will be available soon.
        </p>
      </div>
    </div>
  );
};

export default PlayerAnalytics;