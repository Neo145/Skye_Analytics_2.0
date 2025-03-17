// src/components/TeamsOverview.tsx
import React, { useState, useEffect } from 'react';
import SkyeAnalyticsApi, { Team } from '../api';

interface TeamsOverviewProps {
  onTeamSelect: (teamName: string) => void;
}

const TeamsOverview: React.FC<TeamsOverviewProps> = ({ onTeamSelect }) => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [filteredTeams, setFilteredTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const getTeams = async () => {
      try {
        setIsLoading(true);
        const data = await SkyeAnalyticsApi.getAllTeams();
        // Sort teams by win percentage in descending order
        const sortedTeams = data.sort((a, b) => b.win_percentage - a.win_percentage);
        setTeams(sortedTeams);
        setFilteredTeams(sortedTeams);
      } catch (err) {
        setError('Failed to load teams data');
      } finally {
        setIsLoading(false);
      }
    };

    getTeams();
  }, []);

  const handleTeamSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const teamName = e.target.value;
    setSelectedTeam(teamName);
    
    if (teamName) {
      onTeamSelect(teamName);
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const searchTerm = e.target.value.toLowerCase();
    const filtered = teams.filter(team => 
      team.team_name.toLowerCase().includes(searchTerm)
    );
    setFilteredTeams(filtered);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-blue-500 border-solid"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-red-500 text-center">
          <p className="text-xl font-semibold mb-2">Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center text-blue-700 mb-8">
        IPL Teams Performance Overview
      </h1>

      <div className="mb-8 flex flex-col md:flex-row gap-4 justify-between">
        <div className="w-full md:w-1/2 lg:w-1/3">
          <label htmlFor="teamSelect" className="block text-sm font-medium text-gray-700 mb-2">
            Select Team to View Details
          </label>
          <select
            id="teamSelect"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            value={selectedTeam}
            onChange={handleTeamSelect}
          >
            <option value="">-- Select a Team --</option>
            {teams.map(team => (
              <option key={team.team_name} value={team.team_name}>
                {team.team_name}
              </option>
            ))}
          </select>
        </div>

        <div className="w-full md:w-1/2 lg:w-1/3">
          <label htmlFor="teamSearch" className="block text-sm font-medium text-gray-700 mb-2">
            Search Teams
          </label>
          <input
            id="teamSearch"
            type="text"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            placeholder="Type to search..."
            onChange={handleSearch}
          />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTeams.map((team) => (
          <div 
            key={team.team_name} 
            className="bg-white shadow-md rounded-lg p-6 hover:shadow-xl transition-shadow cursor-pointer"
            onClick={() => onTeamSelect(team.team_name)}
          >
            <h2 className="text-xl font-bold mb-4 text-blue-600">
              {team.team_name}
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Seasons Played</p>
                <p className="font-bold">{team.seasons_played}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Matches</p>
                <p className="font-bold">{team.matches_played}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Matches Won</p>
                <p className="font-bold">{team.matches_won}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Win Percentage</p>
                <p className={`font-bold ${team.win_percentage > 50 ? 'text-green-600' : 'text-red-600'}`}>
                  {team.win_percentage.toFixed(2)}%
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredTeams.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No teams found matching your search criteria
        </div>
      )}
    </div>
  );
};

export default TeamsOverview;