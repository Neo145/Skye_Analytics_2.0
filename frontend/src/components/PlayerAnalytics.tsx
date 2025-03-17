import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './PlayerAnalytics.css';
import './PlayerVisualizations.css';

// Base URL for API
const BASE_URL = 'http://127.0.0.1:8000/api';

// Define interfaces for player data
interface Player {
  player_name: string;
  role: string;
  balls_faced: number;
  runs_scored: number;
  balls_bowled: number;
  wickets: number;
  has_won_pom: boolean;
}

interface TopPlayer {
  player_name: string;
  matches: number;
  [key: string]: any; // For dynamic stats like runs, sixes, etc.
}

interface TopPlayersResponse {
  category: string;
  season: number | null;
  players: TopPlayer[];
  count: number;
}

interface PlayerDetailedStats {
  player_name: string;
  role: string;
  batting_stats: {
    matches: number;
    innings: number;
    runs: number;
    balls_faced: number;
    strike_rate: number;
    average: number;
    fours: number;
    sixes: number;
    highest_score: number;
    fifties: number;
    hundreds: number;
  };
  bowling_stats: {
    matches: number;
    innings: number;
    balls_bowled: number;
    runs_conceded: number;
    wickets: number;
    economy: number;
    average: number;
    strike_rate: number;
    best_figures: string;
  };
  player_of_match_count: number;
  seasons_played: number[];
}

// API service class
class SkyeAnalyticsApi {
  /**
   * Get all players
   * @returns Promise with all players data
   */
  static async getAllPlayers(): Promise<{players: Player[]}> {
    try {
      const response = await axios.get(`${BASE_URL}/players/all`);
      return response.data;
    } catch (error) {
      console.error('Error fetching all players:', error);
      throw error;
    }
  }

  /**
   * Get top players by a specific statistical category for a season
   * @param category The statistical category (sixes, fours, runs, etc.)
   * @param season The IPL season year
   * @param limit Maximum number of players to return
   * @returns Promise with top players data
   */
  static async getTopPlayers(category: string, season: number, limit: number = 10): Promise<TopPlayersResponse> {
    try {
      const response = await axios.get(`${BASE_URL}/players/top/${category}`, {
        params: { season, limit }
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching top players for ${category}:`, error);
      throw error;
    }
  }

  /**
   * Get detailed stats for a specific player
   * @param playerName The name of the player
   * @returns Promise with detailed player stats
   */
  static async getPlayerDetails(playerName: string): Promise<PlayerDetailedStats> {
    try {
      // In a real implementation, this would call the actual API
      // For now, we'll use mock data
      const mockPlayerDetails: PlayerDetailedStats = {
        player_name: playerName,
        role: 'All-Rounder', // This would come from the API
        batting_stats: {
          matches: 85,
          innings: 81,
          runs: 2654,
          balls_faced: 1832,
          strike_rate: 144.87,
          average: 34.46,
          fours: 225,
          sixes: 123,
          highest_score: 89,
          fifties: 19,
          hundreds: 0
        },
        bowling_stats: {
          matches: 85,
          innings: 35,
          balls_bowled: 564,
          runs_conceded: 842,
          wickets: 31,
          economy: 8.95,
          average: 27.16,
          strike_rate: 18.19,
          best_figures: "3/15"
        },
        player_of_match_count: 7,
        seasons_played: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
      };
      
      return mockPlayerDetails;
    } catch (error) {
      console.error(`Error fetching details for player ${playerName}:`, error);
      throw error;
    }
  }
}

const PlayerAnalytics: React.FC = () => {
  // State variables
  const [players, setPlayers] = useState<Player[]>([]);
  const [filteredPlayers, setFilteredPlayers] = useState<Player[]>([]);
  const [topPlayers, setTopPlayers] = useState<TopPlayer[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('sixes');
  const [selectedSeason, setSelectedSeason] = useState<number>(2024);
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const [playerDetails, setPlayerDetails] = useState<PlayerDetailedStats | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isTopPlayersLoading, setIsTopPlayersLoading] = useState<boolean>(false);
  const [isPlayerDetailsLoading, setIsPlayerDetailsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Seasons array for dropdown (adjust based on your data)
  const seasons = Array.from({ length: 17 }, (_, i) => 2008 + i);
  
  // Available statistics categories
  const categories = [
    { value: 'sixes', label: 'Most Sixes' },
    { value: 'fours', label: 'Most Fours' },
    { value: 'runs', label: 'Most Runs' },
    { value: 'wickets', label: 'Most Wickets' },
    { value: 'catches', label: 'Most Catches' },
    { value: 'strike_rate', label: 'Best Strike Rate (min 100 runs)' },
    { value: 'economy', label: 'Best Economy (min 10 overs)' },
    { value: 'batting_average', label: 'Best Batting Average (min 100 runs)' },
    { value: 'bowling_average', label: 'Best Bowling Average (min 5 wickets)' }
  ];

  // Available player roles for filtering
  const roles = [
    { value: 'all', label: 'All Roles' },
    { value: 'Batsman', label: 'Batsmen' },
    { value: 'Bowler', label: 'Bowlers' },
    { value: 'All-Rounder', label: 'All-Rounders' },
    { value: 'Wicket Keeper', label: 'Wicket Keepers' }
  ];

  // Fetch all players on component mount
  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        setIsLoading(true);
        const response = await SkyeAnalyticsApi.getAllPlayers();
        if (response && Array.isArray(response.players)) {
          setPlayers(response.players);
          setFilteredPlayers(response.players);
        } else {
          throw new Error('Invalid player data format');
        }
      } catch (err) {
        console.error('Error fetching players:', err);
        setError('Failed to load player data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPlayers();
  }, []);

  // Fetch top players when category or season changes
  useEffect(() => {
    const fetchTopPlayers = async () => {
      try {
        setIsTopPlayersLoading(true);
        const response = await SkyeAnalyticsApi.getTopPlayers(selectedCategory, selectedSeason, 10);
        if (response && Array.isArray(response.players)) {
          setTopPlayers(response.players);
        } else {
          console.error('Unexpected top players response format:', response);
          setTopPlayers([]);
        }
      } catch (err) {
        console.error(`Error fetching top players for ${selectedCategory}:`, err);
        setTopPlayers([]);
      } finally {
        setIsTopPlayersLoading(false);
      }
    };

    if (selectedCategory && selectedSeason) {
      fetchTopPlayers();
    }
  }, [selectedCategory, selectedSeason]);

  // Fetch player details when a player is selected
  useEffect(() => {
    const fetchPlayerDetails = async () => {
      if (!selectedPlayer) return;
      
      try {
        setIsPlayerDetailsLoading(true);
        const details = await SkyeAnalyticsApi.getPlayerDetails(selectedPlayer);
        setPlayerDetails(details);
      } catch (err) {
        console.error(`Error fetching details for ${selectedPlayer}:`, err);
        setError(`Failed to load details for ${selectedPlayer}`);
      } finally {
        setIsPlayerDetailsLoading(false);
      }
    };

    fetchPlayerDetails();
  }, [selectedPlayer]);

  // Handle search term change
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const term = e.target.value.toLowerCase();
    setSearchTerm(term);
    
    filterPlayers(term, roleFilter);
  };

  // Handle role filter change
  const handleRoleFilter = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const role = e.target.value;
    setRoleFilter(role);
    
    filterPlayers(searchTerm, role);
  };

  // Filter players based on search term and role
  const filterPlayers = (term: string, role: string) => {
    let filtered = players;
    
    // Apply search filter
    if (term) {
      filtered = filtered.filter(player => 
        player.player_name.toLowerCase().includes(term)
      );
    }
    
    // Apply role filter
    if (role !== 'all') {
      filtered = filtered.filter(player => player.role === role);
    }
    
    setFilteredPlayers(filtered);
  };

  // Handle category change
  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCategory(e.target.value);
  };

  // Handle season change
  const handleSeasonChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedSeason(parseInt(e.target.value));
  };

  // Handle player selection
  const handlePlayerSelect = (playerName: string) => {
    setSelectedPlayer(playerName);
  };

  // Handle back button click
  const handleBackToList = () => {
    setSelectedPlayer(null);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-blue-500 border-solid"></div>
      </div>
    );
  }

  // Error state
  if (error && !selectedPlayer) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-red-500 text-center">
          <p className="text-xl font-semibold mb-2">Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  // Get category label for display
  const getCategoryLabel = (value: string) => {
    const category = categories.find(c => c.value === value);
    return category ? category.label : value;
  };

  // Format player stat based on category
  const formatPlayerStat = (player: TopPlayer, category: string) => {
    switch (category) {
      case 'strike_rate':
      case 'economy':
      case 'batting_average':
      case 'bowling_average':
        return player[category]?.toFixed(2) || '0.00';
      default:
        return player[category] || '0';
    }
  };

  // Calculate batting strike rate
  const calculateStrikeRate = (runs: number, balls: number): string => {
    if (balls === 0) return '0.00';
    return ((runs / balls) * 100).toFixed(2);
  };

  // Get appropriate CSS class for strike rate
  const getStrikeRateClass = (strikeRate: number) => {
    if (strikeRate >= 150) return 'text-green-600 font-bold';
    if (strikeRate >= 130) return 'text-green-500';
    if (strikeRate >= 110) return 'text-blue-500';
    if (strikeRate >= 90) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center text-blue-700 mb-8">
        Player Analytics
      </h1>

      {selectedPlayer ? (
        // Player details view
        <div className="bg-white shadow-md rounded-lg p-6">
          {isPlayerDetailsLoading ? (
            <div className="flex justify-center items-center py-10">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-blue-500 border-solid"></div>
            </div>
          ) : playerDetails ? (
            <>
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-semibold text-blue-800">
                    {playerDetails.player_name}
                    {playerDetails.player_of_match_count > 0 && (
                      <span className="ml-2 bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">
                        {playerDetails.player_of_match_count}x Player of Match
                      </span>
                    )}
                  </h2>
                  <p className="text-gray-600">{playerDetails.role}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Seasons: {playerDetails.seasons_played.join(', ')}
                  </p>
                </div>
                <button
                  onClick={handleBackToList}
                  className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Back to Players
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Batting Stats */}
                <div>
                  <h3 className="text-xl font-semibold mb-4 text-blue-700 border-b pb-2">
                    Batting Statistics
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Matches</p>
                      <p className="text-xl font-bold">{playerDetails.batting_stats.matches}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Innings</p>
                      <p className="text-xl font-bold">{playerDetails.batting_stats.innings}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Runs</p>
                      <p className="text-xl font-bold">{playerDetails.batting_stats.runs}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Average</p>
                      <p className="text-xl font-bold">{playerDetails.batting_stats.average.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Strike Rate</p>
                      <p className={`text-xl font-bold ${getStrikeRateClass(playerDetails.batting_stats.strike_rate)}`}>
                        {playerDetails.batting_stats.strike_rate.toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Highest Score</p>
                      <p className="text-xl font-bold">{playerDetails.batting_stats.highest_score}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Fours</p>
                      <p className="text-xl font-bold">{playerDetails.batting_stats.fours}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Sixes</p>
                      <p className="text-xl font-bold">{playerDetails.batting_stats.sixes}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">50s / 100s</p>
                      <p className="text-xl font-bold">
                        {playerDetails.batting_stats.fifties} / {playerDetails.batting_stats.hundreds}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Bowling Stats */}
                <div>
                  <h3 className="text-xl font-semibold mb-4 text-blue-700 border-b pb-2">
                    Bowling Statistics
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Matches</p>
                      <p className="text-xl font-bold">{playerDetails.bowling_stats.matches}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Innings</p>
                      <p className="text-xl font-bold">{playerDetails.bowling_stats.innings}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Wickets</p>
                      <p className="text-xl font-bold">{playerDetails.bowling_stats.wickets}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Economy</p>
                      <p className={`text-xl font-bold ${playerDetails.bowling_stats.economy < 7.5 ? 'text-green-600' : playerDetails.bowling_stats.economy > 9 ? 'text-red-500' : 'text-yellow-500'}`}>
                        {playerDetails.bowling_stats.economy.toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Average</p>
                      <p className="text-xl font-bold">{playerDetails.bowling_stats.average.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Strike Rate</p>
                      <p className="text-xl font-bold">{playerDetails.bowling_stats.strike_rate.toFixed(2)}</p>
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600">Best Bowling Figures</p>
                    <p className="text-xl font-bold">{playerDetails.bowling_stats.best_figures}</p>
                  </div>
                </div>
              </div>

              {/* Performance Chart/Visualization goes here */}
              <div className="mt-8 p-4 bg-blue-50 rounded-lg">
                <h3 className="text-xl font-semibold mb-4 text-blue-700">
                  Performance Insights
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium mb-2">Batting Contribution</h4>
                    <div className="relative pt-1">
                      <div className="flex mb-2 items-center justify-between">
                        <div>
                          <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-blue-600 bg-blue-200">
                            Strike Rate vs. Average
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="text-xs font-semibold inline-block text-blue-600">
                            {playerDetails.batting_stats.strike_rate.toFixed(2)}
                          </span>
                        </div>
                      </div>
                      <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-blue-200">
                        <div 
                          style={{ width: `${Math.min(playerDetails.batting_stats.strike_rate / 2, 100)}%` }} 
                          className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500"
                        ></div>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Bowling Effectiveness</h4>
                    <div className="relative pt-1">
                      <div className="flex mb-2 items-center justify-between">
                        <div>
                          <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-green-600 bg-green-200">
                            Economy Rate
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="text-xs font-semibold inline-block text-green-600">
                            {playerDetails.bowling_stats.economy.toFixed(2)}
                          </span>
                        </div>
                      </div>
                      <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-green-200">
                        <div 
                          style={{ width: `${Math.max(100 - (playerDetails.bowling_stats.economy * 8), 10)}%` }} 
                          className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-green-500"
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mt-4 text-sm text-gray-700">
                  <p>
                    <strong>{playerDetails.player_name}</strong> is a {playerDetails.role.toLowerCase()} who has participated in {playerDetails.batting_stats.matches} matches across {playerDetails.seasons_played.length} seasons. 
                    {playerDetails.batting_stats.strike_rate > 140 ? 
                      ` With an impressive strike rate of ${playerDetails.batting_stats.strike_rate.toFixed(2)}, they are an excellent aggressive batter.` : 
                      playerDetails.batting_stats.strike_rate > 120 ? 
                      ` With a solid strike rate of ${playerDetails.batting_stats.strike_rate.toFixed(2)}, they are a reliable batter.` : 
                      ''
                    }
                    {playerDetails.bowling_stats.wickets > 50 ? 
                      ` As a bowler, they've taken ${playerDetails.bowling_stats.wickets} wickets with an economy of ${playerDetails.bowling_stats.economy.toFixed(2)}.` : 
                      playerDetails.bowling_stats.wickets > 20 ? 
                      ` They have contributed ${playerDetails.bowling_stats.wickets} wickets with their bowling.` : 
                      ''
                    }
                    {playerDetails.player_of_match_count > 5 ? 
                      ` A match-winner who has earned Player of the Match ${playerDetails.player_of_match_count} times.` : 
                      ''
                    }
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500">No detailed stats available for this player.</p>
            </div>
          )}
        </div>
      ) : (
        // Player list and top players view
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Top Players Section */}
          <div className="lg:col-span-2 order-2 lg:order-1">
            <div className="bg-white shadow-md rounded-lg p-6 mb-8">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
                <h2 className="text-2xl font-semibold text-blue-700 mb-4 sm:mb-0">
                  Top Players: {getCategoryLabel(selectedCategory)}
                </h2>
                <div className="flex flex-col sm:flex-row gap-4">
                  <select
                    className="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={selectedCategory}
                    onChange={handleCategoryChange}
                  >
                    {categories.map(category => (
                      <option key={category.value} value={category.value}>
                        {category.label}
                      </option>
                    ))}
                  </select>
                  <select
                    className="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={selectedSeason}
                    onChange={handleSeasonChange}
                  >
                    {seasons.map(season => (
                      <option key={season} value={season}>
                        Season {season}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {isTopPlayersLoading ? (
                <div className="flex justify-center items-center py-10">
                  <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-blue-500 border-solid"></div>
                </div>
              ) : topPlayers.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full bg-white">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="py-3 px-4 text-left">Rank</th>
                        <th className="py-3 px-4 text-left">Player</th>
                        <th className="py-3 px-4 text-left">Matches</th>
                        <th className="py-3 px-4 text-left">{getCategoryLabel(selectedCategory)}</th>
                        {selectedCategory === 'sixes' || selectedCategory === 'fours' ? (
                          <th className="py-3 px-4 text-left">Runs</th>
                        ) : null}
                      </tr>
                    </thead>
                    <tbody>
                      {topPlayers.map((player, index) => (
                        <tr 
                          key={index} 
                          className="border-b hover:bg-gray-50 cursor-pointer"
                          onClick={() => handlePlayerSelect(player.player_name)}
                        >
                          <td className="py-3 px-4 font-medium">
                            {index === 0 ? (
                              <span className="bg-yellow-500 text-white px-2 py-1 rounded-full">1</span>
                            ) : index === 1 ? (
                              <span className="bg-gray-400 text-white px-2 py-1 rounded-full">2</span>
                            ) : index === 2 ? (
                              <span className="bg-amber-700 text-white px-2 py-1 rounded-full">3</span>
                            ) : (
                              <span>{index + 1}</span>
                            )}
                          </td>
                          <td className="py-3 px-4 font-medium">{player.player_name}</td>
                          <td className="py-3 px-4">{player.matches}</td>
                          <td className="py-3 px-4 font-bold text-blue-600">
                            {formatPlayerStat(player, selectedCategory)}
                          </td>
                          {selectedCategory === 'sixes' || selectedCategory === 'fours' ? (
                            <td className="py-3 px-4">{player.runs}</td>
                          ) : null}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-6 text-center text-gray-500">
                  No player data available for this category and season.
                </div>
              )}
            </div>
            {/* Player Quick Stats */}
            <div className="bg-white shadow-md rounded-lg p-6">
              <h2 className="text-2xl font-semibold text-blue-700 mb-6">
                Player Quick Stats
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredPlayers.slice(0, 9).map((player, index) => (
                  <div 
                    key={index}
                    className="p-4 border rounded-lg hover:shadow-md cursor-pointer transition-shadow"
                    onClick={() => handlePlayerSelect(player.player_name)}
                  >
                    <h3 className="font-bold text-lg text-blue-700 mb-2">{player.player_name}</h3>
                    <p className="text-gray-700 text-sm mb-2">{player.role}</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-gray-600">Runs:</p>
                        <p className="font-medium">{player.runs_scored}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">SR:</p>
                        <p className={`font-medium ${getStrikeRateClass(player.balls_faced === 0 ? 0 : parseFloat(calculateStrikeRate(player.runs_scored, player.balls_faced)))}`}>
                          {calculateStrikeRate(player.runs_scored, player.balls_faced)}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-600">Wickets:</p>
                        <p className="font-medium">{player.wickets}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">POM:</p>
                        <p className="font-medium">{player.has_won_pom ? 'Yes' : 'No'}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {filteredPlayers.length > 9 && (
                <div className="text-center mt-6">
                  <p className="text-gray-500">
                    Showing 9 of {filteredPlayers.length} players. Use the search to find more players.
                  </p>
                </div>
              )}
              {filteredPlayers.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No players found matching your search criteria.
                </div>
              )}
            </div>
          </div>

          {/* Search and Filters Section */}
          <div className="lg:col-span-1 order-1 lg:order-2">
            <div className="bg-white shadow-md rounded-lg p-6 sticky top-4">
              <h2 className="text-xl font-semibold text-blue-700 mb-4">
                Find Players
              </h2>
              <div className="mb-4">
                <label htmlFor="player-search" className="block text-sm font-medium text-gray-700 mb-2">
                  Search by Name
                </label>
                <input
                  id="player-search"
                  type="text"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter player name..."
                  value={searchTerm}
                  onChange={handleSearch}
                />
              </div>
              
              <div className="mb-6">
                <label htmlFor="role-filter" className="block text-sm font-medium text-gray-700 mb-2">
                  Filter by Role
                </label>
                <select
                  id="role-filter"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  value={roleFilter}
                  onChange={handleRoleFilter}
                >
                  {roles.map(role => (
                    <option key={role.value} value={role.value}>
                      {role.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-lg mb-6">
                <h3 className="font-medium text-blue-800 mb-2">Player Stats</h3>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">Total Players:</span>
                  <span className="font-bold">{players.length}</span>
                </div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">Batsmen:</span>
                  <span className="font-bold">{players.filter(p => p.role === 'Batsman').length}</span>
                </div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">Bowlers:</span>
                  <span className="font-bold">{players.filter(p => p.role === 'Bowler').length}</span>
                </div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">All-Rounders:</span>
                  <span className="font-bold">{players.filter(p => p.role === 'All-Rounder').length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Wicket Keepers:</span>
                  <span className="font-bold">{players.filter(p => p.role === 'Wicket Keeper').length}</span>
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-5 rounded-lg text-white">
                <h3 className="font-bold text-lg mb-2">Player Analysis</h3>
                <p className="text-sm mb-4">
                  Explore detailed statistics, performance trends, and match-winning contributions of IPL players across all seasons.
                </p>
                <ul className="text-sm list-disc list-inside">
                  <li className="mb-1">Compare player performances</li>
                  <li className="mb-1">Analyze batting and bowling stats</li>
                  <li className="mb-1">Identify match-winners</li>
                  <li className="mb-1">Track performance evolution</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayerAnalytics;
