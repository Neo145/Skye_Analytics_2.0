// src/components/TeamDetails.tsx
import React, { useState, useEffect } from 'react';
import SkyeAnalyticsApi from '../api';

interface TeamDetailsProps {
  teamName: string;
  onBackToTeams?: () => void;
}

type ActiveTabType = 'basic' | 'seasons' | 'venues' | 'opponents' | 'toss';

const TeamDetails: React.FC<TeamDetailsProps> = ({ teamName, onBackToTeams }) => {
  const [teamDetails, setTeamDetails] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTabType>('basic');

  useEffect(() => {
    const fetchTeamDetails = async () => {
      try {
        setIsLoading(true);
        const details = await SkyeAnalyticsApi.getTeamDetails(teamName);
        setTeamDetails(details);
      } catch (err) {
        setError(`Failed to fetch details for ${teamName}`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTeamDetails();
  }, [teamName]);

  const tabs = [
    { key: 'basic', label: 'Basic Stats' },
    { key: 'seasons', label: 'Season Performance' },
    { key: 'venues', label: 'Venue Stats' },
    { key: 'opponents', label: 'Opponent Performance' },
    { key: 'toss', label: 'Toss Performance' }
  ];

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-blue-500 border-solid"></div>
      </div>
    );
  }

  if (error || !teamDetails) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-red-500 text-center">
          <p className="text-xl font-semibold mb-2">Error</p>
          <p>{error || `Failed to load data for ${teamName}`}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-blue-700">
          {teamDetails.team_name} Team Analytics
        </h1>
        {onBackToTeams && (
          <button 
            onClick={onBackToTeams}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Back to Teams
          </button>
        )}
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden mb-8">
        <div className="flex border-b overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              className={`px-4 py-3 font-medium whitespace-nowrap ${
                activeTab === tab.key as ActiveTabType
                  ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600' 
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
              onClick={() => setActiveTab(tab.key as ActiveTabType)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'basic' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Seasons Played</p>
                  <p className="text-2xl font-bold">{teamDetails.basic_stats.seasons_played}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Matches Played</p>
                  <p className="text-2xl font-bold">{teamDetails.basic_stats.matches_played}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Matches Won</p>
                  <p className="text-2xl font-bold">{teamDetails.basic_stats.matches_won}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Win Percentage</p>
                  <p className={`text-2xl font-bold ${teamDetails.basic_stats.win_percentage > 50 ? 'text-green-600' : 'text-red-600'}`}>
                    {teamDetails.basic_stats.win_percentage.toFixed(2)}%
                  </p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">First Season</p>
                  <p className="text-2xl font-bold">{teamDetails.basic_stats.first_season}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Last Season</p>
                  <p className="text-2xl font-bold">{teamDetails.basic_stats.last_season}</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'seasons' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Season Performance</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="py-3 px-4 text-left">Season</th>
                      <th className="py-3 px-4 text-left">Matches Played</th>
                      <th className="py-3 px-4 text-left">Matches Won</th>
                      <th className="py-3 px-4 text-left">Win Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {teamDetails.season_stats.map((season: any) => (
                      <tr key={season.season} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4">{season.season}</td>
                        <td className="py-3 px-4">{season.matches_played}</td>
                        <td className="py-3 px-4">{season.matches_won}</td>
                        <td className={`py-3 px-4 font-medium ${season.win_percentage > 50 ? 'text-green-600' : 'text-red-600'}`}>
                          {season.win_percentage.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'venues' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Venue Stats</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="py-3 px-4 text-left">Venue Type</th>
                      <th className="py-3 px-4 text-left">Matches Played</th>
                      <th className="py-3 px-4 text-left">Matches Won</th>
                      <th className="py-3 px-4 text-left">Win Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {teamDetails.venue_stats.map((venue: any, index: number) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4">{venue.venue_type}</td>
                        <td className="py-3 px-4">{venue.matches_played}</td>
                        <td className="py-3 px-4">{venue.matches_won}</td>
                        <td className={`py-3 px-4 font-medium ${venue.win_percentage > 50 ? 'text-green-600' : 'text-red-600'}`}>
                          {venue.win_percentage.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'opponents' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Performance Against Opponents</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="py-3 px-4 text-left">Opponent</th>
                      <th className="py-3 px-4 text-left">Matches Played</th>
                      <th className="py-3 px-4 text-left">Matches Won</th>
                      <th className="py-3 px-4 text-left">Win Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {teamDetails.opponent_stats.map((opponent: any, index: number) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4">{opponent.opponent}</td>
                        <td className="py-3 px-4">{opponent.matches_played}</td>
                        <td className="py-3 px-4">{opponent.matches_won}</td>
                        <td className={`py-3 px-4 font-medium ${opponent.win_percentage > 50 ? 'text-green-600' : 'text-red-600'}`}>
                          {opponent.win_percentage.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'toss' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Toss Performance</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Total Matches</p>
                  <p className="text-2xl font-bold">{teamDetails.toss_stats.total_matches}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Toss Wins</p>
                  <p className="text-2xl font-bold">{teamDetails.toss_stats.toss_wins}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Toss Win Percentage</p>
                  <p className="text-2xl font-bold">{teamDetails.toss_stats.toss_win_percentage.toFixed(2)}%</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Chose Bat</p>
                  <p className="text-2xl font-bold">{teamDetails.toss_stats.chose_bat}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Chose Field</p>
                  <p className="text-2xl font-bold">{teamDetails.toss_stats.chose_field}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Win Rate After Winning Toss</p>
                  <p className={`text-2xl font-bold ${teamDetails.toss_stats.win_rate_after_winning_toss > 50 ? 'text-green-600' : 'text-red-600'}`}>
                    {teamDetails.toss_stats.win_rate_after_winning_toss.toFixed(2)}%
                  </p>
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold mb-2">Toss Decision Analysis</h3>
                <p className="text-sm text-gray-700 mb-3">
                  This team chooses to {teamDetails.toss_stats.chose_bat > teamDetails.toss_stats.chose_field ? 'bat' : 'field'} first more often when winning the toss 
                  ({Math.max(teamDetails.toss_stats.chose_bat, teamDetails.toss_stats.chose_field)} times out of {teamDetails.toss_stats.toss_wins} toss wins).
                </p>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-blue-600 h-2.5 rounded-full" 
                    style={{ width: `${(teamDetails.toss_stats.chose_bat / teamDetails.toss_stats.toss_wins) * 100}%` }}
                  ></div>
                </div>
                <div className="flex justify-between mt-1 text-xs text-gray-500">
                  <span>Chose to Bat: {((teamDetails.toss_stats.chose_bat / teamDetails.toss_stats.toss_wins) * 100).toFixed(1)}%</span>
                  <span>Chose to Field: {((teamDetails.toss_stats.chose_field / teamDetails.toss_stats.toss_wins) * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeamDetails;