import React, { useState, useEffect } from 'react';
import SkyeAnalyticsApi from '../api';

const TossAnalysis: React.FC = () => {
  const [tossTrends, setTossTrends] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTossTrends = async () => {
      try {
        setIsLoading(true);
        const trends = await SkyeAnalyticsApi.getTossTrends();
        setTossTrends(trends);
        setIsLoading(false);
      } catch (err) {
        setError('Failed to fetch toss trends');
        setIsLoading(false);
      }
    };

    fetchTossTrends();
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center h-screen text-red-500">
        {error}
      </div>
    );
  }

  // Calculate overall trends
  const calculateOverallTrends = () => {
    const totalSeasons = tossTrends.length;
    const batFirstTrend = tossTrends.reduce((sum, trend) => sum + trend.chose_bat_percentage, 0) / totalSeasons;
    const fieldFirstTrend = tossTrends.reduce((sum, trend) => sum + trend.chose_field_percentage, 0) / totalSeasons;

    return {
      avgBatFirst: batFirstTrend,
      avgFieldFirst: fieldFirstTrend,
      recentTrend: tossTrends.slice(-5).map(trend => ({
        season: trend.season,
        batFirstPercentage: trend.chose_bat_percentage,
        fieldFirstPercentage: trend.chose_field_percentage
      }))
    };
  };

  const overallTrends = calculateOverallTrends();

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-center text-blue-700 mb-8">
        IPL Toss Decision Trends Analysis
      </h1>

      {/* Overall Toss Trends Summary */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h2 className="text-2xl font-bold mb-4 text-blue-600">
          Overall Toss Trends
        </h2>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-lg mb-2">Avg. Bat First</h3>
            <p className="text-2xl font-bold text-green-600">
              {overallTrends.avgBatFirst.toFixed(2)}%
            </p>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-lg mb-2">Avg. Field First</h3>
            <p className="text-2xl font-bold text-blue-600">
              {overallTrends.avgFieldFirst.toFixed(2)}%
            </p>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-lg mb-2">Trend Direction</h3>
            <p className={`text-xl font-bold ${
              overallTrends.avgFieldFirst > 50 
                ? 'text-blue-600' 
                : 'text-green-600'
            }`}>
              {overallTrends.avgFieldFirst > 50 
                ? 'Prefer Fielding' 
                : 'Prefer Batting'}
            </p>
          </div>
        </div>
      </div>

      {/* Detailed Toss Trends */}
      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-2xl font-bold mb-4 text-blue-600">
          Seasonal Toss Decision Trends
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-blue-100">
              <tr>
                <th className="p-2 text-left">Season</th>
                <th className="p-2 text-right">Total Matches</th>
                <th className="p-2 text-right">Bat First %</th>
                <th className="p-2 text-right">Field First %</th>
                <th className="p-2 text-right">Trend</th>
              </tr>
            </thead>
            <tbody>
              {tossTrends.map((trend) => (
                <tr 
                  key={trend.season} 
                  className="border-b hover:bg-blue-50"
                >
                  <td className="p-2">{trend.season}</td>
                  <td className="p-2 text-right">{trend.total_matches}</td>
                  <td className="p-2 text-right text-green-600">
                    {trend.chose_bat_percentage.toFixed(2)}%
                  </td>
                  <td className="p-2 text-right text-blue-600">
                    {trend.chose_field_percentage.toFixed(2)}%
                  </td>
                  <td className="p-2 text-right">
                    <span className={`
                      px-2 py-1 rounded-full text-xs font-bold
                      ${trend.chose_field_percentage > 50 
                        ? 'bg-blue-200 text-blue-800' 
                        : 'bg-green-200 text-green-800'
                      }
                    `}>
                      {trend.chose_field_percentage > 50 
                        ? 'Field First' 
                        : 'Bat First'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Toss Decision Insights */}
      <div className="mt-8 bg-white shadow-md rounded-lg p-6">
        <h2 className="text-2xl font-bold mb-4 text-blue-600">
          Toss Decision Insights
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-semibold text-lg mb-2">Key Observations</h3>
            <ul className="list-disc list-inside space-y-2">
              <li>
                <strong>Fielding Trend:</strong> Recent seasons show a strong preference for fielding first
              </li>
              <li>
                <strong>Strategic Shift:</strong> Teams increasingly prefer chasing over setting a target
              </li>
              <li>
                <strong>Pitch Conditions:</strong> Suggests evolving pitch and playing conditions
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-lg mb-2">Potential Reasons</h3>
            <ul className="list-disc list-inside space-y-2">
              <li>Better understanding of pitch behavior</li>
              <li>Improved death bowling strategies</li>
              <li>Rise of day-night matches influencing decisions</li>
              <li>Impact of dew factor in later stages of matches</li>
            </ul>
          </div>
        </div>

        {/* Recent Trend Highlight */}
        <div className="mt-6 bg-blue-50 p-4 rounded-lg">
          <h3 className="font-semibold text-lg mb-2 text-blue-700">
            Recent 5 Seasons Trend
          </h3>
          <div className="flex space-x-2">
            {overallTrends.recentTrend.map((trend) => (
              <div 
                key={trend.season} 
                className="flex-1 bg-white p-3 rounded-lg shadow-sm"
              >
                <p className="text-sm font-bold text-gray-600">{trend.season}</p>
                <div className="flex items-center mt-1">
                  <div 
                    className="h-2 bg-green-500 rounded-l" 
                    style={{width: `${trend.batFirstPercentage}%`}}
                  />
                  <div 
                    className="h-2 bg-blue-500 rounded-r" 
                    style={{width: `${trend.fieldFirstPercentage}%`}}
                  />
                </div>
                <div className="flex justify-between text-xs mt-1">
                  <span className="text-green-600">Bat: {trend.batFirstPercentage.toFixed(0)}%</span>
                  <span className="text-blue-600">Field: {trend.fieldFirstPercentage.toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TossAnalysis;