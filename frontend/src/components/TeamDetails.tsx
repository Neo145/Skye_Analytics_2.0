import React, { useState, useEffect } from 'react';
import SkyeAnalyticsApi from '../api';

interface TeamDetailsProps {
  teamName: string;
  onBackToTeams?: () => void;
}

type ActiveTabType = 'basic' | 'seasons' | 'venues' | 'opponents' | 'toss';

const TeamDetails: React.FC<TeamDetailsProps> = ({ 
  teamName, 
  onBackToTeams 
}) => {
  const [teamDetails, setTeamDetails] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTabType>('basic');

  useEffect(() => {
    const fetchTeamDetails = async () => {
      try {
        setIsLoading(true);
        const details = await SkyeAnalyticsApi.getTeamDetails(teamName);
        setTeamDetails(details);
        setIsLoading(false);
      } catch (err) {
        setError('Failed to fetch team details');
        setIsLoading(false);
      }
    };

    fetchTeamDetails();
  }, [teamName]);

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

  if (!teamDetails) {
    return null;
  }

  const renderBasicStats = () => (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4 text-blue-600">
        Basic Team Statistics
      </h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="font-semibold">Team Name:</p>
          <p>{teamDetails.basic_stats.team_name}</p>
        </div>
        <div>
          <p className="font-semibold">Seasons Played:</p>
          <p>{teamDetails.basic_stats.seasons_played}</p>
        </div>
        <div>
          <p className="font-semibold">Total Matches:</p>
          <p>{teamDetails.basic_stats.matches_played}</p>
        </div>
        <div>
          <p className="font-semibold">Matches Won:</p>
          <p>{teamDetails.basic_stats.matches_won}</p>
        </div>
        <div>
          <p className="font-semibold">Win Percentage:</p>
          <p className={`font-bold ${teamDetails.basic_stats.win_percentage > 50 ? 'text-green-600' : 'text-red-600'}`}>
            {teamDetails.basic_stats.win_percentage.toFixed(2)}%
          </p>
        </div>
        <div>
          <p className="font-semibold">First Season:</p>
          <p>{teamDetails.basic_stats.first_season}</p>
        </div>
        <div>
          <p className="font-semibold">Last Season:</p>
          <p>{teamDetails.basic_stats.last_season}</p>
        </div>
        <div>
          <p className="font-semibold">Venues Played:</p>
          <p>{teamDetails.basic_stats.venues_played}</p>
        </div>
      </div>
    </div>
  );

  const renderSeasonStats = () => (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4 text-blue-600">
        Season-wise Performance
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-blue-100">
            <tr>
              <th className="p-2 text-left">Season</th>
              <th className="p-2 text-right">Matches Played</th>
              <th className="p-2 text-right">Matches Won</th>
              <th className="p-2 text-right">Win %</th>
            </tr>
          </thead>
          <tbody>
            {teamDetails.season_stats.map((season: any) => (
              <tr key={season.season} className="border-b hover:bg-blue-50">
                <td className="p-2">{season.season}</td>
                <td className="p-2 text-right">{season.matches_played}</td>
                <td className="p-2 text-right">{season.matches_won}</td>
                <td className={`p-2 text-right font-bold ${season.win_percentage > 50 ? 'text-green-600' : 'text-red-600'}`}>
                  {season.win_percentage.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderVenueStats = () => (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4 text-blue-600">
        Venue Performance
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-blue-100">
            <tr>
              <th className="p-2 text-left">Venue Type</th>
              <th className="p-2 text-right">Matches Played</th>
              <th className="p-2 text-right">Matches Won</th>
              <th className="p-2 text-right">Win %</th>
            </tr>
          </thead>
          <tbody>
            {teamDetails.venue_stats.map((venue: any) => (
              <tr key={venue.venue_type} className="border-b hover:bg-blue-50">
                <td className="p-2">{venue.venue_type}</td>
                <td className="p-2 text-right">{venue.matches_played}</td>
                <td className="p-2 text-right">{venue.matches_won}</td>
                <td className={`p-2 text-right font-bold ${venue.win_percentage > 50 ? 'text-green-600' : 'text-red-600'}`}>
                  {venue.win_percentage.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderOpponentStats = () => (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4 text-blue-600">
        Performance Against Opponents
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-blue-100">
            <tr>
              <th className="p-2 text-left">Opponent</th>
              <th className="p-2 text-right">Matches Played</th>
              <th className="p-2 text-right">Matches Won</th>
              <th className="p-2 text-right">Win %</th>
            </tr>
          </thead>
          <tbody>
            {teamDetails.opponent_stats.map((opponent: any) => (
              <tr key={opponent.opponent} className="border-b hover:bg-blue-50">
                <td className="p-2">{opponent.opponent}</td>
                <td className="p-2 text-right">{opponent.matches_played}</td>
                <td className="p-2 text-right">{opponent.matches_won}</td>
                <td className={`p-2 text-right font-bold ${opponent.win_percentage > 50 ? 'text-green-600' : 'text-red-600'}`}>
                  {opponent.win_percentage.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderTossStats = () => (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4 text-blue-600">
        Toss Performance
      </h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="font-semibold">Total Matches:</p>
          <p>{teamDetails.toss_stats.total_matches}</p>
        </div>
        <div>
          <p className="font-semibold">Toss Wins:</p>
          <p>{teamDetails.toss_stats.toss_wins}</p>
        </div>
        <div>
          <p className="font-semibold">Toss Win %:</p>
          <p className="text-blue-600">
            {teamDetails.toss_stats.toss_win_percentage.toFixed(2)}%
          </p>
        </div>
        <div>
          <p className="font-semibold">Chose to Bat:</p>
          <p>{teamDetails.toss_stats.chose_bat}</p>
        </div>
        <div>
          <p className="font-semibold">Chose to Field:</p>
          <p>{teamDetails.toss_stats.chose_field}</p>
        </div>
        <div>
          <p className="font-semibold">Won After Winning Toss:</p>
          <p>{teamDetails.toss_stats.won_after_winning_toss}</p>
        </div>
        <div>
          <p className="font-semibold">Win Rate After Winning Toss:</p>
          <p className={`font-bold ${teamDetails.toss_stats.win_rate_after_winning_toss > 50 ? 'text-green-600' : 'text-red-600'}`}>
            {teamDetails.toss_stats.win_rate_after_winning_toss.toFixed(2)}%
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold text-blue-700">
          {teamName} Team Analytics
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

      {/* Tab Navigation */}
      <div className="flex justify-center mb-6">
        {[
          { key: 'basic', label: 'Basic Stats' },
          { key: 'seasons', label: 'Season Performance' },
          { key: 'venues', label: 'Venue Stats' },
          { key: 'opponents', label: 'Opponent Performance' },
          { key: 'toss', label: 'Toss Performance' }
        ].map((tab) => (
          <button
            key={tab.key}
            className={`
              px-4 py-2 mx-2 rounded-lg transition-colors
              ${activeTab === tab.key 
                ? 'bg-blue-600 text-white' 
                : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
              }
            `}
            onClick={() => setActiveTab(tab.key as ActiveTabType)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Conditional Rendering of Tabs */}
      <div className="mt-6">
        {activeTab === 'basic' && renderBasicStats()}
        {activeTab === 'seasons' && renderSeasonStats()}
        {activeTab === 'venues' && renderVenueStats()}
        {activeTab === 'opponents' && renderOpponentStats()}
        {activeTab === 'toss' && renderTossStats()}
      </div>
    </div>
  );
};

export default TeamDetails;