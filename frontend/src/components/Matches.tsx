import React, { useState, useEffect } from 'react';
import './Matches.css';

interface OverallStats {
  total_matches: number;
  venues_used: number;
  team_combinations: number;
  bat_first_count: number;
  field_first_count: number;
  bat_first_percentage: number;
  field_first_percentage: number;
  won_batting_first: number;
  won_fielding_first: number;
  toss_winner_won_match: number;
  toss_winner_win_percentage: number;
}

interface SeasonStat {
  season: number;
  total_matches: number;
  venues_used: number;
  bat_first_count: number;
  field_first_count: number;
  won_batting_first: number;
  won_fielding_first: number;
  toss_winner_win_percentage: number;
}

interface Match {
  filename: string;
  match_date: string;
  venue: string;
  city: string;
  team1: string;
  team2: string;
  toss_winner: string;
  toss_decision: string;
  winner: string;
  margin: string;
  player_of_match: string;
}

interface MatchesResponse {
  overall_stats: OverallStats;
  season_stats: SeasonStat[];
  team_stats?: any[];
  venue_stats?: any[];
  filters_applied?: any;
}

interface SeasonMatchesResponse {
  season: number;
  matches: Match[];
  stats?: any;
  team_stats?: any[];
}

const Matches: React.FC = () => {
  const [overallStats, setOverallStats] = useState<OverallStats | null>(null);
  const [seasonStats, setSeasonStats] = useState<SeasonStat[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);
  const [seasonMatches, setSeasonMatches] = useState<Match[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSeasonMatchesLoading, setIsSeasonMatchesLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch overall match stats
  useEffect(() => {
    const fetchMatchStats = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('http://127.0.0.1:8000/api/matches/');
        if (!response.ok) {
          throw new Error(`Failed to fetch match stats: ${response.status}`);
        }
        
        const data: MatchesResponse = await response.json();
        
        if (data && data.overall_stats && Array.isArray(data.season_stats)) {
          setOverallStats(data.overall_stats);
          // Sort seasons newest to oldest
          const sortedSeasons = [...data.season_stats].sort((a, b) => b.season - a.season);
          setSeasonStats(sortedSeasons);
          
          // Default to latest season
          if (sortedSeasons.length > 0) {
            setSelectedSeason(sortedSeasons[0].season);
          }
        } else {
          throw new Error('Invalid match data format');
        }
      } catch (err) {
        console.error('Error fetching match stats:', err);
        setError('Failed to load match statistics');
      } finally {
        setIsLoading(false);
      }
    };

    fetchMatchStats();
  }, []);

  // Fetch matches for selected season
  useEffect(() => {
    if (!selectedSeason) return;
    
    const fetchSeasonMatches = async () => {
      try {
        setIsSeasonMatchesLoading(true);
        const response = await fetch(`http://127.0.0.1:8000/api/matches/seasons/${selectedSeason}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch season matches: ${response.status}`);
        }
        
        const data: SeasonMatchesResponse = await response.json();
        
        if (data && Array.isArray(data.matches)) {
          // Sort matches by date, newest first
          const sortedMatches = [...data.matches].sort((a, b) => {
            // Safely handle date comparison
            const dateA = new Date(a.match_date).getTime() || 0;
            const dateB = new Date(b.match_date).getTime() || 0;
            return dateB - dateA;
          });
          setSeasonMatches(sortedMatches);
        } else {
          throw new Error('Invalid season matches data format');
        }
      } catch (err) {
        console.error('Error fetching season matches:', err);
        setError(`Failed to load matches for season ${selectedSeason}`);
        setSeasonMatches([]);
      } finally {
        setIsSeasonMatchesLoading(false);
      }
    };

    fetchSeasonMatches();
  }, [selectedSeason]);

  const handleSeasonChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const season = parseInt(e.target.value);
    if (!isNaN(season)) {
      setSelectedSeason(season);
    } else {
      setSelectedSeason(null);
      setSeasonMatches([]);
    }
  };

  // Parse the margin object from string
  const parseMargin = (marginStr: string): string => {
    try {
      if (!marginStr) return "N/A";
      const marginObj = JSON.parse(marginStr.replace(/'/g, '"'));
      const key = Object.keys(marginObj)[0];
      return `${marginObj[key]} ${key}`;
    } catch (e) {
      return marginStr || "N/A";
    }
  };

  // Get the current season stat
  const getCurrentSeasonStat = (): SeasonStat | undefined => {
    if (!selectedSeason) return undefined;
    return seasonStats.find(s => s.season === selectedSeason);
  };

  const getMatchResultClass = (match: Match): string => {
    if (!match.winner || !match.toss_winner) return '';
    return match.winner === match.toss_winner ? 'text-green-600' : 'text-blue-600';
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-blue-500 border-solid"></div>
      </div>
    );
  }

  if (error && !overallStats) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-red-500 text-center">
          <p className="text-xl font-semibold mb-2">Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const currentSeasonStat = getCurrentSeasonStat();

  // Safe calculation helper functions to avoid division by zero
  const calculatePercentage = (numerator: number, denominator: number): number => {
    if (!denominator) return 0;
    return (numerator / denominator) * 100;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center text-blue-700 mb-8">
        IPL Match Analysis
      </h1>

      {/* Overall Statistics Dashboard */}
      {overallStats && (
        <div className="bg-white shadow-md rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">Overall Match Statistics</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Total Matches</p>
              <p className="text-2xl font-bold">{overallStats.total_matches}</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Venues Used</p>
              <p className="text-2xl font-bold">{overallStats.venues_used}</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Team Combinations</p>
              <p className="text-2xl font-bold">{overallStats.team_combinations}</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Toss-Win Match Correlation</p>
              <p className="text-2xl font-bold">{overallStats.toss_winner_win_percentage.toFixed(2)}%</p>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-2">Batting vs Fielding First</h3>
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex-1">
                <div className="w-full bg-gray-200 rounded-full h-2.5 mb-1">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full"
                    style={{ width: `${overallStats.bat_first_percentage}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Batting First: {overallStats.bat_first_percentage.toFixed(1)}%</span>
                  <span>Fielding First: {overallStats.field_first_percentage.toFixed(1)}%</span>
                </div>
              </div>
              
              <div className="flex-1">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Won Batting First</p>
                    <p className="font-bold">
                      {overallStats.won_batting_first} / {overallStats.bat_first_count} ({calculatePercentage(overallStats.won_batting_first, overallStats.bat_first_count).toFixed(1)}%)
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Won Fielding First</p>
                    <p className="font-bold">
                      {overallStats.won_fielding_first} / {overallStats.field_first_count} ({calculatePercentage(overallStats.won_fielding_first, overallStats.field_first_count).toFixed(1)}%)
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Season Selector */}
      <div className="mb-8">
        <label htmlFor="seasonSelect" className="block text-lg font-medium text-gray-700 mb-2">
          Select Season
        </label>
        <select
          id="seasonSelect"
          className="w-full md:w-1/3 p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          value={selectedSeason || ''}
          onChange={handleSeasonChange}
        >
          <option value="">-- Select a Season --</option>
          {seasonStats.map(season => (
            <option key={season.season} value={season.season}>
              IPL {season.season}
            </option>
          ))}
        </select>
      </div>

      {/* Selected Season Statistics */}
      {currentSeasonStat && (
        <div className="bg-white shadow-md rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">Season {selectedSeason} Statistics</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Total Matches</p>
              <p className="text-2xl font-bold">{currentSeasonStat.total_matches}</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Venues Used</p>
              <p className="text-2xl font-bold">{currentSeasonStat.venues_used}</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Toss-Win Match %</p>
              <p className="text-2xl font-bold">{currentSeasonStat.toss_winner_win_percentage.toFixed(2)}%</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Fielding First %</p>
              <p className="text-2xl font-bold">
                {calculatePercentage(currentSeasonStat.field_first_count, currentSeasonStat.total_matches).toFixed(1)}%
              </p>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-2">Batting vs Fielding First Success Rate</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Teams Batting First</p>
                <div className="flex items-center">
                  <div className="w-full bg-gray-200 rounded-full h-5 mr-2">
                    <div 
                      className="bg-green-500 h-5 rounded-full"
                      style={{ 
                        width: `${calculatePercentage(
                          currentSeasonStat.won_batting_first,
                          currentSeasonStat.bat_first_count
                        )}%` 
                      }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium">
                    {calculatePercentage(
                      currentSeasonStat.won_batting_first,
                      currentSeasonStat.bat_first_count
                    ).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {currentSeasonStat.won_batting_first} wins out of {currentSeasonStat.bat_first_count} matches
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Teams Fielding First</p>
                <div className="flex items-center">
                  <div className="w-full bg-gray-200 rounded-full h-5 mr-2">
                    <div 
                      className="bg-blue-500 h-5 rounded-full"
                      style={{ 
                        width: `${calculatePercentage(
                          currentSeasonStat.won_fielding_first,
                          currentSeasonStat.field_first_count
                        )}%` 
                      }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium">
                    {calculatePercentage(
                      currentSeasonStat.won_fielding_first,
                      currentSeasonStat.field_first_count
                    ).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {currentSeasonStat.won_fielding_first} wins out of {currentSeasonStat.field_first_count} matches
                </p>
              </div>
            </div>
          </div>

          {/* Season Insights */}
          <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
            <h4 className="font-medium text-blue-800 mb-1">Season Insight</h4>
            <p className="text-sm text-gray-700">
              {currentSeasonStat.field_first_count > currentSeasonStat.bat_first_count ? 
                `Teams preferred to field first this season (${calculatePercentage(currentSeasonStat.field_first_count, currentSeasonStat.total_matches).toFixed(1)}% of matches).` : 
                `Teams preferred to bat first this season (${calculatePercentage(currentSeasonStat.bat_first_count, currentSeasonStat.total_matches).toFixed(1)}% of matches).`
              }
              {' '}
              {calculatePercentage(currentSeasonStat.won_fielding_first, currentSeasonStat.field_first_count) > 
               calculatePercentage(currentSeasonStat.won_batting_first, currentSeasonStat.bat_first_count) ? 
                `Fielding first was more successful with a ${calculatePercentage(currentSeasonStat.won_fielding_first, currentSeasonStat.field_first_count).toFixed(1)}% win rate compared to ${calculatePercentage(currentSeasonStat.won_batting_first, currentSeasonStat.bat_first_count).toFixed(1)}% when batting first.` : 
                `Batting first was more successful with a ${calculatePercentage(currentSeasonStat.won_batting_first, currentSeasonStat.bat_first_count).toFixed(1)}% win rate compared to ${calculatePercentage(currentSeasonStat.won_fielding_first, currentSeasonStat.field_first_count).toFixed(1)}% when fielding first.`
              }
              {' '}
              {currentSeasonStat.toss_winner_win_percentage > 50 ? 
                `Winning the toss was a significant advantage (${currentSeasonStat.toss_winner_win_percentage.toFixed(1)}% win rate).` : 
                `Winning the toss did not provide a significant advantage (${currentSeasonStat.toss_winner_win_percentage.toFixed(1)}% win rate).`
              }
            </p>
          </div>
        </div>
      )}

      {/* Season Matches */}
      {selectedSeason && (
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">Season {selectedSeason} Matches</h2>
          
          {isSeasonMatchesLoading ? (
            <div className="flex justify-center items-center py-10">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-blue-500 border-solid"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="py-3 px-4 text-left">Date</th>
                    <th className="py-3 px-4 text-left">Teams</th>
                    <th className="py-3 px-4 text-left">Venue</th>
                    <th className="py-3 px-4 text-left">Toss</th>
                    <th className="py-3 px-4 text-left">Result</th>
                    <th className="py-3 px-4 text-left">Player of Match</th>
                  </tr>
                </thead>
                <tbody>
                  {seasonMatches.map((match, index) => (
                    <tr key={match.filename || index} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">{match.match_date}</td>
                      <td className="py-3 px-4 font-medium">
                        {match.team1} vs {match.team2}
                      </td>
                      <td className="py-3 px-4">
                        {match.venue}
                        {match.city && <br />}
                        {match.city && <span className="text-xs text-gray-500">{match.city}</span>}
                      </td>
                      <td className="py-3 px-4">
                        {match.toss_winner}
                        <br />
                        <span className="text-xs text-gray-500">
                          (chose to {match.toss_decision})
                        </span>
                      </td>
                      <td className={`py-3 px-4 font-medium ${getMatchResultClass(match)}`}>
                        {match.winner}
                        <br />
                        <span className="text-xs">
                          won by {parseMargin(match.margin)}
                        </span>
                      </td>
                      <td className="py-3 px-4">{match.player_of_match}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {seasonMatches.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No matches available for this season
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Matches;