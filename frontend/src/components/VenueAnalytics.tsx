import React, { useState, useEffect } from 'react';
import SkyeAnalyticsApi from '../api';

interface Venue {
  venue: string;
  city: string;
  matches_hosted: number;
  seasons_used: number;
  first_season: number;
  last_season: number;
}

interface VenuesResponse {
  venues: Venue[];
}

interface VenueDetails {
  venue_name: string;
  basic_stats: {
    venue: string;
    city: string;
    matches_hosted: number;
    seasons_used: number;
    first_season: number;
    last_season: number;
    teams_played: number;
  };
  match_outcomes: {
    total_matches: number;
    bat_first_count: number;
    field_first_count: number;
    bat_first_percentage: number;
    field_first_percentage: number;
    won_batting_first: number;
    won_fielding_first: number;
    batting_first_win_percentage: number | null;
    fielding_first_win_percentage: number | null;
    toss_winner_won_match: number;
    toss_winner_win_percentage: number;
  };
  season_stats: Array<{
    season: number;
    total_matches: number;
    bat_first_count: number;
    field_first_count: number;
    won_batting_first: number;
    won_fielding_first: number;
    batting_first_win_percentage: number | null;
    fielding_first_win_percentage: number | null;
  }>;
  team_stats: Array<{
    team_name: string;
    matches_played: number;
    matches_won: number;
    win_percentage: number;
    seasons: number;
  }>;
}

// Extend SkyeAnalyticsApi with venue methods
const fetchVenueDetails = async (venueName: string): Promise<VenueDetails> => {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/venues/${encodeURIComponent(venueName)}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch venue details: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching venue details: ${error}`);
    throw error;
  }
};

const fetchVenueDetailsBySeason = async (venueName: string, season: number): Promise<VenueDetails> => {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/venues/${encodeURIComponent(venueName)}?season=${season}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch venue details for season: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching venue details by season: ${error}`);
    throw error;
  }
};

const VenueAnalytics: React.FC = () => {
  const [venues, setVenues] = useState<Venue[]>([]);
  const [filteredVenues, setFilteredVenues] = useState<Venue[]>([]);
  const [selectedVenue, setSelectedVenue] = useState<string>('');
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);
  const [venueDetails, setVenueDetails] = useState<VenueDetails | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isDetailsLoading, setIsDetailsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Fetch all venues on component mount
  useEffect(() => {
    const fetchVenues = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('http://127.0.0.1:8000/api/venues/');
        if (!response.ok) {
          throw new Error(`Failed to fetch venues: ${response.status}`);
        }
        
        const data: VenuesResponse = await response.json();
        
        if (data && Array.isArray(data.venues)) {
          // Sort venues by matches hosted (descending)
          const sortedVenues = [...data.venues].sort((a: Venue, b: Venue) => b.matches_hosted - a.matches_hosted);
          setVenues(sortedVenues);
          setFilteredVenues(sortedVenues);
        } else {
          throw new Error('Invalid venue data format');
        }
      } catch (err) {
        console.error('Error fetching venues:', err);
        setError('Failed to load venue data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchVenues();
  }, []);

  // Fetch venue details when venue or season changes
  useEffect(() => {
    if (!selectedVenue) return;

    const fetchVenueData = async () => {
      try {
        setIsDetailsLoading(true);
        let data: VenueDetails;
        
        if (selectedSeason) {
          data = await fetchVenueDetailsBySeason(selectedVenue, selectedSeason);
        } else {
          data = await fetchVenueDetails(selectedVenue);
        }
        
        setVenueDetails(data);
      } catch (err) {
        console.error(`Error fetching details for ${selectedVenue}:`, err);
        setError(`Failed to load details for ${selectedVenue}`);
      } finally {
        setIsDetailsLoading(false);
      }
    };

    fetchVenueData();
  }, [selectedVenue, selectedSeason]);

  // Handle venue search
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const term = e.target.value.toLowerCase();
    setSearchTerm(term);
    
    if (!term.trim()) {
      setFilteredVenues(venues);
    } else {
      const filtered = venues.filter(venue => 
        venue.venue.toLowerCase().includes(term) || 
        venue.city.toLowerCase().includes(term)
      );
      setFilteredVenues(filtered);
    }
  };

  // Handle venue selection
  const handleVenueSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const venueName = e.target.value;
    setSelectedVenue(venueName);
    setVenueDetails(null); // Clear previous details
    
    // Find venue to get available seasons
    const venue = venues.find(v => v.venue === venueName);
    if (venue) {
      // If a season is selected but it's not within the venue's available seasons, reset it
      if (selectedSeason && (selectedSeason < venue.first_season || selectedSeason > venue.last_season)) {
        setSelectedSeason(null);
      }
    }
  };

  // Handle season selection
  const handleSeasonSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const season = e.target.value ? parseInt(e.target.value) : null;
    setSelectedSeason(season);
  };

  // Generate array of available seasons for the selected venue
  const getAvailableSeasons = (): number[] => {
    if (!selectedVenue) return [];
    
    const venue = venues.find(v => v.venue === selectedVenue);
    if (!venue) return [];
    
    const seasons = [];
    for (let year = venue.first_season; year <= venue.last_season; year++) {
      seasons.push(year);
    }
    return seasons;
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-blue-500 border-solid"></div>
      </div>
    );
  }

  if (error && !selectedVenue) {
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
        Cricket Venue Analytics
      </h1>

      {/* Search and Filter Section */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Venue Selection */}
          <div>
            <label htmlFor="venue-select" className="block text-sm font-medium text-gray-700 mb-2">
              Select Venue
            </label>
            <select
              id="venue-select"
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              value={selectedVenue}
              onChange={handleVenueSelect}
            >
              <option value="">-- Select a Venue --</option>
              {venues.map(venue => (
                <option key={venue.venue} value={venue.venue}>
                  {venue.venue} ({venue.city})
                </option>
              ))}
            </select>
          </div>

          {/* Season Filter (only shown when venue is selected) */}
          {selectedVenue && (
            <div>
              <label htmlFor="season-select" className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Season (Optional)
              </label>
              <select
                id="season-select"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                value={selectedSeason || ''}
                onChange={handleSeasonSelect}
              >
                <option value="">All Seasons</option>
                {getAvailableSeasons().map(year => (
                  <option key={year} value={year}>
                    IPL {year}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Search Box */}
          <div>
            <label htmlFor="venue-search" className="block text-sm font-medium text-gray-700 mb-2">
              Search Venues
            </label>
            <input
              id="venue-search"
              type="text"
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              placeholder="Search by venue or city..."
              value={searchTerm}
              onChange={handleSearch}
            />
          </div>
        </div>
      </div>

      {/* Venue Details Section */}
      {selectedVenue ? (
        isDetailsLoading ? (
          <div className="flex justify-center items-center py-10">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-blue-500 border-solid"></div>
          </div>
        ) : venueDetails ? (
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-6 text-blue-800">
              {venueDetails.venue_name} - {venueDetails.basic_stats.city}
              {selectedSeason && <span className="ml-2 text-blue-600">(IPL {selectedSeason})</span>}
            </h2>

            {/* Basic Venue Statistics */}
            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-4 text-blue-700">Venue Overview</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Matches Hosted</p>
                  <p className="text-2xl font-bold">{venueDetails.basic_stats.matches_hosted}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Seasons Used</p>
                  <p className="text-2xl font-bold">{venueDetails.basic_stats.seasons_used}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">First Season</p>
                  <p className="text-2xl font-bold">{venueDetails.basic_stats.first_season}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Last Season</p>
                  <p className="text-2xl font-bold">{venueDetails.basic_stats.last_season}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Teams Played</p>
                  <p className="text-2xl font-bold">{venueDetails.basic_stats.teams_played}</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Toss-Win Match Correlation</p>
                  <p className="text-2xl font-bold">{venueDetails.match_outcomes.toss_winner_win_percentage.toFixed(2)}%</p>
                </div>
              </div>
            </div>

            {/* Match Outcomes */}
            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-4 text-blue-700">Match Outcomes</h3>
              
              {/* Toss Decision Breakdown */}
              <div className="mb-6">
                <h4 className="font-medium mb-2">Toss Decision Trends</h4>
                <div className="w-full bg-gray-200 rounded-full h-2.5 mb-1">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full"
                    style={{ width: `${venueDetails.match_outcomes.bat_first_percentage}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Batting First: {venueDetails.match_outcomes.bat_first_percentage.toFixed(1)}%</span>
                  <span>Fielding First: {venueDetails.match_outcomes.field_first_percentage.toFixed(1)}%</span>
                </div>
              </div>
              
              {/* Success Rates */}
              <div>
                <h4 className="font-medium mb-2">Match Outcome by Decision</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                  {/* Batting First Success */}
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Teams Batting First Win Rate</p>
                    <div className="flex items-center">
                      <div className="w-full bg-gray-200 rounded-full h-5 mr-2">
                        <div 
                          className="bg-green-500 h-5 rounded-full"
                          style={{ width: `${venueDetails.match_outcomes.batting_first_win_percentage || 0}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">
                        {venueDetails.match_outcomes.batting_first_win_percentage === null ? 
                          'N/A' : 
                          `${venueDetails.match_outcomes.batting_first_win_percentage.toFixed(1)}%`
                        }
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {venueDetails.match_outcomes.won_batting_first} wins out of {venueDetails.match_outcomes.bat_first_count} matches
                    </p>
                  </div>
                  
                  {/* Fielding First Success */}
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Teams Fielding First Win Rate</p>
                    <div className="flex items-center">
                      <div className="w-full bg-gray-200 rounded-full h-5 mr-2">
                        <div 
                          className="bg-blue-500 h-5 rounded-full"
                          style={{ width: `${venueDetails.match_outcomes.fielding_first_win_percentage || 0}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">
                        {venueDetails.match_outcomes.fielding_first_win_percentage === null ? 
                          'N/A' : 
                          `${venueDetails.match_outcomes.fielding_first_win_percentage.toFixed(1)}%`
                        }
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {venueDetails.match_outcomes.won_fielding_first} wins out of {venueDetails.match_outcomes.field_first_count} matches
                    </p>
                  </div>
                </div>
                
                {/* Recommendation Box */}
                <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                  <h4 className="font-medium text-blue-800 mb-1">Venue Insight</h4>
                  <p className="text-sm text-gray-700">
                    {venueDetails.match_outcomes.field_first_percentage > 60 ? 
                      `Teams strongly prefer to field first at this venue (${venueDetails.match_outcomes.field_first_percentage.toFixed(1)}% of tosses).` :
                      venueDetails.match_outcomes.bat_first_percentage > 60 ?
                      `Teams strongly prefer to bat first at this venue (${venueDetails.match_outcomes.bat_first_percentage.toFixed(1)}% of tosses).` :
                      'Teams do not show a strong preference for batting or fielding first at this venue.'
                    }
                    {' '}
                    {venueDetails.match_outcomes.fielding_first_win_percentage !== null && 
                     venueDetails.match_outcomes.batting_first_win_percentage !== null && 
                     venueDetails.match_outcomes.fielding_first_win_percentage > venueDetails.match_outcomes.batting_first_win_percentage + 10 ? 
                      `Fielding first has historically been more successful with a ${venueDetails.match_outcomes.fielding_first_win_percentage.toFixed(1)}% win rate compared to ${venueDetails.match_outcomes.batting_first_win_percentage.toFixed(1)}% when batting first.` :
                     venueDetails.match_outcomes.batting_first_win_percentage !== null && 
                     venueDetails.match_outcomes.fielding_first_win_percentage !== null && 
                     venueDetails.match_outcomes.batting_first_win_percentage > venueDetails.match_outcomes.fielding_first_win_percentage + 10 ?
                      `Batting first has historically been more successful with a ${venueDetails.match_outcomes.batting_first_win_percentage.toFixed(1)}% win rate compared to ${venueDetails.match_outcomes.fielding_first_win_percentage.toFixed(1)}% when fielding first.` :
                      'There is no significant advantage to either batting or fielding first at this venue based on historical results.'
                    }
                  </p>
                </div>
              </div>
            </div>

            {/* Team Performance at Venue */}
            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-4 text-blue-700">Team Performance</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="py-3 px-4 text-left">Team</th>
                      <th className="py-3 px-4 text-left">Matches Played</th>
                      <th className="py-3 px-4 text-left">Matches Won</th>
                      <th className="py-3 px-4 text-left">Win Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {venueDetails.team_stats
                      .sort((a, b) => b.win_percentage - a.win_percentage)
                      .map((team, index) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4">{team.team_name}</td>
                        <td className="py-3 px-4">{team.matches_played}</td>
                        <td className="py-3 px-4">{team.matches_won}</td>
                        <td className={`py-3 px-4 font-medium ${team.win_percentage > 50 ? 'text-green-600' : team.win_percentage === 0 ? 'text-red-600' : ''}`}>
                          {team.win_percentage.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Season Breakdown (if not filtered by season) */}
            {!selectedSeason && venueDetails.season_stats.length > 1 && (
              <div>
                <h3 className="text-xl font-semibold mb-4 text-blue-700">Season Breakdown</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full bg-white">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="py-3 px-4 text-left">Season</th>
                        <th className="py-3 px-4 text-left">Matches</th>
                        <th className="py-3 px-4 text-left">Bat First %</th>
                        <th className="py-3 px-4 text-left">Field First %</th>
                        <th className="py-3 px-4 text-left">Bat First Win %</th>
                        <th className="py-3 px-4 text-left">Field First Win %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {venueDetails.season_stats.map((season) => (
                        <tr key={season.season} className="border-b hover:bg-gray-50">
                          <td className="py-3 px-4">{season.season}</td>
                          <td className="py-3 px-4">{season.total_matches}</td>
                          <td className="py-3 px-4">
                            {((season.bat_first_count / season.total_matches) * 100).toFixed(1)}%
                          </td>
                          <td className="py-3 px-4">
                            {((season.field_first_count / season.total_matches) * 100).toFixed(1)}%
                          </td>
                          <td className="py-3 px-4">
                            {season.batting_first_win_percentage === null ? 'N/A' : `${season.batting_first_win_percentage.toFixed(1)}%`}
                          </td>
                          <td className="py-3 px-4">
                            {season.fielding_first_win_percentage === null ? 'N/A' : `${season.fielding_first_win_percentage.toFixed(1)}%`}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white shadow-md rounded-lg p-10 text-center">
            <p className="text-gray-500">No data available for this venue{selectedSeason ? ` in season ${selectedSeason}` : ''}.</p>
          </div>
        )
      ) : (
        // Venue Cards Grid (when no venue is selected)
        <div>
          <h2 className="text-2xl font-semibold mb-4 text-blue-700">Top Cricket Venues</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredVenues.slice(0, 9).map((venue) => (
              <div 
                key={venue.venue}
                className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => setSelectedVenue(venue.venue)}
              >
                <h3 className="text-xl font-bold mb-2 text-blue-600">{venue.venue}</h3>
                <p className="text-gray-600 mb-4">{venue.city}</p>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <p className="text-sm text-gray-600">Matches Hosted</p>
                    <p className="font-bold">{venue.matches_hosted}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Seasons Used</p>
                    <p className="font-bold">{venue.seasons_used}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">First Season</p>
                    <p className="font-bold">{venue.first_season}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Last Season</p>
                    <p className="font-bold">{venue.last_season}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {filteredVenues.length > 9 && (
            <div className="text-center mt-6">
              <p className="text-gray-500">
                Showing 9 of {filteredVenues.length} venues. Select a venue from the dropdown to see more details.
              </p>
            </div>
          )}
          {filteredVenues.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No venues found matching your search criteria.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VenueAnalytics;