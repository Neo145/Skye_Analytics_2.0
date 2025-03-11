import React, { useState, useEffect } from 'react';
import SkyeAnalyticsApi, { Team } from '../api';

interface TeamsOverviewProps {
  onTeamSelect?: (teamName: string) => void;
}

const TeamsOverview: React.FC<TeamsOverviewProps> = ({ onTeamSelect }) => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        setIsLoading(true);
        const fetchedTeams = await SkyeAnalyticsApi.getAllTeams();
        
        // Sort teams by win percentage in descending order
        const sortedTeams = fetchedTeams.sort((a, b) => 
          b.win_percentage - a.win_percentage
        );
        
        setTeams(sortedTeams);
        setIsLoading(false);
      } catch (err) {
        setError('Failed to fetch teams');
        setIsLoading(false);
      }
    };

    fetchTeams();
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

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-center text-blue-700 mb-8">
        IPL Teams Performance Overview
      </h1>
      
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {teams.map((team) => (
          <div 
            key={team.team_name} 
            className="bg-white shadow-md rounded-lg p-6 hover:shadow-xl transition-shadow cursor-pointer"
            onClick={() => onTeamSelect && onTeamSelect(team.team_name)}
          >
            <h2 className="text-2xl font-bold mb-4 text-blue-600">
              {team.team_name}
            </h2>
            <div className="grid grid-cols-2 gap-2">
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
    </div>
  );
};

export default TeamsOverview;