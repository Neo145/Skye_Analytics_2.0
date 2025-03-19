import React, { useState, useEffect } from 'react';
import { CalendarDays, MapPin, Clock, TrendingUp, ChevronDown, ChevronRight, Star, Trophy, AlertCircle, Info, Users, BarChart } from 'lucide-react';
import axios from 'axios';
import './IPL2025Matches.css';

// Base Match interface that matches your API response
interface BaseMatch {
  id: string;
  name: string;
  matchType: string;
  status: string;
  venue: string;
  date: string;
  dateTimeGMT: string;
  teams: string[];
  series_id: string;
  fantasyEnabled: boolean;
  bbbEnabled: boolean;
  hasSquad: boolean;
  matchStarted: boolean;
  matchEnded: boolean;
}

// Team statistics interface
interface TeamStat {
  team: string;
  recentForm: string[];
  topBatsman: string;
  topBowler: string;
  position: number;
}

// Head to head interface
interface HeadToHead {
  matches: number;
  team1Wins: number;
  team2Wins: number;
  noResult: number;
}

// Processed match interface that extends the base match
interface ProcessedMatch extends BaseMatch {
  formattedDate: string;
  formattedTime: string;
  matchNumber: string | null;
  isPlayoff: boolean;
  teamStats: TeamStat[];
  headToHead: HeadToHead | null;
}

// Date group interface
interface DateGroup {
  date: string;
  matches: ProcessedMatch[];
  hasMatches?: boolean;
}

// Detail tab type
interface DetailTabType {
  overview: boolean;
  stats: boolean;
  h2h: boolean;
  venue: boolean;
}

const IPL2025Matches: React.FC = () => {
  const [matches, setMatches] = useState<DateGroup[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedMatchId, setExpandedMatchId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [activeTabs, setActiveTabs] = useState<Record<string, DetailTabType>>({});
  
  useEffect(() => {
    const fetchMatches = async () => {
      try {
        setLoading(true);
        
        // In a real implementation, this would be an API call
        // const response = await axios.get('http://127.0.0.1:8000/api/cricket/matches?limit=70');
        // const data = response.data;
        
        // For demonstration, using sample data
        const data = {
          matches: [
            {
              id: "0a54b5bd-c4f5-48c6-b8aa-db27fa890b73",
              name: "Gujarat Titans vs Lucknow Super Giants, 65th Match",
              matchType: "t20",
              status: "Match not started",
              venue: "Narendra Modi Stadium, Ahmedabad",
              date: "2025-05-14",
              dateTimeGMT: "2025-05-14T14:00:00",
              teams: ["Gujarat Titans", "Lucknow Super Giants"],
              series_id: "d5a498c8-7596-4b93-8ab0-e0efc3345312",
              fantasyEnabled: false,
              bbbEnabled: false,
              hasSquad: true,
              matchStarted: false,
              matchEnded: false
            },
            {
              id: "469c4673-1449-4e20-9bc9-b358ec604fcf",
              name: "Mumbai Indians vs Delhi Capitals, 66th Match",
              matchType: "t20",
              status: "Match not started",
              venue: "Wankhede Stadium, Mumbai",
              date: "2025-05-15",
              dateTimeGMT: "2025-05-15T14:00:00",
              teams: ["Mumbai Indians", "Delhi Capitals"],
              series_id: "d5a498c8-7596-4b93-8ab0-e0efc3345312",
              fantasyEnabled: false,
              bbbEnabled: false,
              hasSquad: true,
              matchStarted: false,
              matchEnded: false
            },
            {
              id: "a860a259-b9a4-42cd-acf7-f9a650e24292",
              name: "Rajasthan Royals vs Punjab Kings, 67th Match",
              matchType: "t20",
              status: "Match not started",
              venue: "Sawai Mansingh Stadium, Jaipur",
              date: "2025-05-16",
              dateTimeGMT: "2025-05-16T14:00:00",
              teams: ["Rajasthan Royals", "Punjab Kings"],
              series_id: "d5a498c8-7596-4b93-8ab0-e0efc3345312",
              fantasyEnabled: false,
              bbbEnabled: false,
              hasSquad: true,
              matchStarted: false,
              matchEnded: false
            },
            {
              id: "1c3424f1-400a-4122-bc01-fb5ab52aa2ee",
              name: "Royal Challengers Bengaluru vs Kolkata Knight Riders, 68th Match",
              matchType: "t20",
              status: "Match not started",
              venue: "M.Chinnaswamy Stadium, Bengaluru",
              date: "2025-05-17",
              dateTimeGMT: "2025-05-17T14:00:00",
              teams: ["Royal Challengers Bengaluru", "Kolkata Knight Riders"],
              series_id: "d5a498c8-7596-4b93-8ab0-e0efc3345312",
              fantasyEnabled: false,
              bbbEnabled: false,
              hasSquad: true,
              matchStarted: false,
              matchEnded: false
            },
            {
              id: "16cd14fd-9a69-49fc-b310-585a03e1d2b2",
              name: "Gujarat Titans vs Chennai Super Kings, 69th Match",
              matchType: "t20",
              status: "Match not started",
              venue: "Narendra Modi Stadium, Ahmedabad",
              date: "2025-05-18",
              dateTimeGMT: "2025-05-18T10:00:00",
              teams: ["Gujarat Titans", "Chennai Super Kings"],
              series_id: "d5a498c8-7596-4b93-8ab0-e0efc3345312",
              fantasyEnabled: false,
              bbbEnabled: false,
              hasSquad: true,
              matchStarted: false,
              matchEnded: false
            },
            {
              id: "d3edeb1d-61f4-417d-ba88-85b608c2ba7e",
              name: "Lucknow Super Giants vs Sunrisers Hyderabad, 70th Match",
              matchType: "t20",
              status: "Match not started",
              venue: "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow",
              date: "2025-05-18",
              dateTimeGMT: "2025-05-18T14:00:00",
              teams: ["Lucknow Super Giants", "Sunrisers Hyderabad"],
              series_id: "d5a498c8-7596-4b93-8ab0-e0efc3345312",
              fantasyEnabled: false,
              bbbEnabled: false,
              hasSquad: true,
              matchStarted: false,
              matchEnded: false
            },
            {
              id: "1c2f9a38-4c3a-407b-90c1-9b78dee63cb8",
              name: "Tbc vs Tbc, Qualifier 1",
              matchType: "t20",
              status: "Match not started",
              venue: "Rajiv Gandhi International Stadium, Hyderabad",
              date: "2025-05-20",
              dateTimeGMT: "2025-05-20T14:00:00",
              teams: ["Tbc", "Tbc"],
              series_id: "d5a498c8-7596-4b93-8ab0-e0efc3345312",
              fantasyEnabled: false,
              bbbEnabled: false,
              hasSquad: false,
              matchStarted: false,
              matchEnded: false
            },
            {
              id: "40596379-a096-4513-8b6f-41df069ca70c",
              name: "Tbc vs Tbc, Eliminator",
              matchType: "t20",
              status: "Match not started",
              venue: "Rajiv Gandhi International Stadium, Hyderabad",
              date: "2025-05-21",
              dateTimeGMT: "2025-05-21T14:00:00",
              teams: ["Tbc", "Tbc"],
              series_id: "d5a498c8-7596-4b93-8ab0-e0efc3345312",
              fantasyEnabled: false,
              bbbEnabled: false,
              hasSquad: false,
              matchStarted: false,
              matchEnded: false
            },
            {
              id: "08b32e61-9c96-4f37-8f76-0b3439a80567",
              name: "Tbc vs Tbc, Qualifier 2",
              matchType: "t20",
              status: "Match not started",
              venue: "Eden Gardens, Kolkata",
              date: "2025-05-23",
              dateTimeGMT: "2025-05-23T14:00:00",
              teams: ["Tbc", "Tbc"],
              series_id: "d5a498c8-7596-4b93-8ab0-e0efc3345312",
              fantasyEnabled: false,
              bbbEnabled: false,
              hasSquad: false,
              matchStarted: false,
              matchEnded: false
            },
            {
              id: "b70371b1-6528-4af6-992c-e880ed585183",
              name: "Tbc vs Tbc, Final",
              matchType: "t20",
              status: "Match not started",
              venue: "Eden Gardens, Kolkata",
              date: "2025-05-25",
              dateTimeGMT: "2025-05-25T14:00:00",
              teams: ["Tbc", "Tbc"],
              series_id: "d5a498c8-7596-4b93-8ab0-e0efc3345312",
              fantasyEnabled: false,
              bbbEnabled: false,
              hasSquad: false,
              matchStarted: false,
              matchEnded: false
            }
          ] as BaseMatch[]
        };
        
        // Initialize active tabs for each match
        const initialActiveTabs: Record<string, DetailTabType> = {};
        data.matches.forEach(match => {
          initialActiveTabs[match.id] = {
            overview: true,
            stats: false,
            h2h: false,
            venue: false
          };
        });
        setActiveTabs(initialActiveTabs);
        
        // Process data for display
        const processedMatches: ProcessedMatch[] = data.matches.map(match => {
          const matchDate = new Date(match.dateTimeGMT);
          
          // Format date
          const formattedDate = matchDate.toLocaleDateString('en-US', {
            weekday: 'short',
            day: 'numeric',
            month: 'short'
          });
          
          // Format time
          const formattedTime = matchDate.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
          });
          
          // Generate placeholder stats for demo
          const teamStats: TeamStat[] = [];
          if (match.teams[0] !== 'Tbc') {
            teamStats.push({
              team: match.teams[0],
              recentForm: ['W', 'L', 'W', 'W', 'L'],
              topBatsman: getTopBatsman(match.teams[0]),
              topBowler: getTopBowler(match.teams[0]),
              position: getTeamPosition(match.teams[0])
            });
          }
          
          if (match.teams[1] !== 'Tbc') {
            teamStats.push({
              team: match.teams[1],
              recentForm: ['W', 'W', 'L', 'W', 'W'],
              topBatsman: getTopBatsman(match.teams[1]),
              topBowler: getTopBowler(match.teams[1]),
              position: getTeamPosition(match.teams[1])
            });
          }
          
          const extractMatchNumber = (name: string): string | null => {
            const parts = name.split(',');
            if (parts.length > 1) {
              return parts[1].trim();
            }
            return null;
          };
          
          // Add placeholder head-to-head stats
          const h2h = match.teams[0] !== 'Tbc' && match.teams[1] !== 'Tbc' ? {
            matches: Math.floor(Math.random() * 20) + 5,
            team1Wins: Math.floor(Math.random() * 10) + 2,
            team2Wins: Math.floor(Math.random() * 10) + 2,
            noResult: 0
          } : null;
          
          if (h2h) {
            h2h.noResult = h2h.matches - h2h.team1Wins - h2h.team2Wins;
          }
          
          return {
            ...match,
            formattedDate,
            formattedTime,
            matchNumber: extractMatchNumber(match.name),
            isPlayoff: match.name.includes('Qualifier') || match.name.includes('Eliminator') || match.name.includes('Final'),
            teamStats,
            headToHead: h2h
          };
        });
        
        // Group matches by date
        const groupedMatches: Record<string, DateGroup> = {};
        processedMatches.forEach(match => {
          const matchDateObj = new Date(match.date);
          const dateKey = matchDateObj.toISOString().split('T')[0];
          
          if (!groupedMatches[dateKey]) {
            groupedMatches[dateKey] = {
              date: match.formattedDate,
              matches: []
            };
          }
          
          groupedMatches[dateKey].matches.push(match);
        });
        
        // Sort dates in ascending order (earliest first)
        const sortedDates = Object.keys(groupedMatches).sort();
        const finalGroupedMatches = sortedDates.map(date => groupedMatches[date]);
        
        setMatches(finalGroupedMatches);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching matches:', err);
        setError('Failed to load matches data. Please try again later.');
        setLoading(false);
      }
    };

    fetchMatches();
    
    // Add cleanup function for any subscriptions
    return () => {
      // Clean up any subscriptions or timers if needed
    };
  }, []);

  // Helper functions to generate placeholder data
  const getTopBatsman = (team: string): string => {
    const batsmen: Record<string, string> = {
      'Chennai Super Kings': 'Ruturaj Gaikwad',
      'Delhi Capitals': 'David Warner',
      'Gujarat Titans': 'Shubman Gill',
      'Kolkata Knight Riders': 'Shreyas Iyer',
      'Lucknow Super Giants': 'KL Rahul',
      'Mumbai Indians': 'Rohit Sharma',
      'Punjab Kings': 'Shikhar Dhawan',
      'Rajasthan Royals': 'Jos Buttler',
      'Royal Challengers Bengaluru': 'Virat Kohli',
      'Sunrisers Hyderabad': 'Aiden Markram'
    };
    return batsmen[team] || 'Unknown';
  };
  
  const getTopBowler = (team: string): string => {
    const bowlers: Record<string, string> = {
      'Chennai Super Kings': 'Ravindra Jadeja',
      'Delhi Capitals': 'Kuldeep Yadav',
      'Gujarat Titans': 'Rashid Khan',
      'Kolkata Knight Riders': 'Sunil Narine',
      'Lucknow Super Giants': 'Mohsin Khan',
      'Mumbai Indians': 'Jasprit Bumrah',
      'Punjab Kings': 'Arshdeep Singh',
      'Rajasthan Royals': 'Yuzvendra Chahal',
      'Royal Challengers Bengaluru': 'Mohammed Siraj',
      'Sunrisers Hyderabad': 'Bhuvneshwar Kumar'
    };
    return bowlers[team] || 'Unknown';
  };
  
  const getTeamPosition = (team: string): number => {
    const positions: Record<string, number> = {
      'Chennai Super Kings': 3,
      'Delhi Capitals': 6,
      'Gujarat Titans': 5,
      'Kolkata Knight Riders': 2,
      'Lucknow Super Giants': 4,
      'Mumbai Indians': 7,
      'Punjab Kings': 9,
      'Rajasthan Royals': 1,
      'Royal Challengers Bengaluru': 8,
      'Sunrisers Hyderabad': 10
    };
    return positions[team] || 0;
  };

  // Toggle match details expansion
  const toggleMatchDetails = (matchId: string) => {
    if (expandedMatchId === matchId) {
      setExpandedMatchId(null);
    } else {
      setExpandedMatchId(matchId);
    }
  };

  // Toggle detail tabs
  const toggleDetailTab = (matchId: string, tab: keyof DetailTabType) => {
    setActiveTabs(prev => ({
      ...prev,
      [matchId]: {
        ...prev[matchId],
        overview: tab === 'overview',
        stats: tab === 'stats',
        h2h: tab === 'h2h',
        venue: tab === 'venue'
      }
    }));
  };

  const getStatusLabel = (match: ProcessedMatch): string => {
    if (match.isPlayoff) {
      if (match.name.includes('Final')) return 'FINAL';
      if (match.name.includes('Qualifier 1')) return 'QUALIFIER 1';
      if (match.name.includes('Qualifier 2')) return 'QUALIFIER 2';
      if (match.name.includes('Eliminator')) return 'ELIMINATOR';
    }
    return match.matchNumber || '';
  };

  const getStatusColor = (status: string): string => {
    if (status === 'Match not started') return 'bg-blue-100 text-blue-800';
    if (status.includes('won')) return 'bg-green-100 text-green-800';
    if (status === 'In Progress') return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  interface TeamColors {
    primary: string;
    text: string;
    light: string;
    border: string;
  }

  const getTeamColor = (teamName: string): TeamColors => {
    const teamColors: Record<string, TeamColors> = {
      'Chennai Super Kings': {
        primary: 'bg-yellow-500',
        text: 'text-yellow-500',
        light: 'bg-yellow-100',
        border: 'border-yellow-500'
      },
      'Delhi Capitals': {
        primary: 'bg-blue-600',
        text: 'text-blue-600',
        light: 'bg-blue-100',
        border: 'border-blue-600'
      },
      'Gujarat Titans': {
        primary: 'bg-blue-800',
        text: 'text-blue-800',
        light: 'bg-blue-100',
        border: 'border-blue-800'
      },
      'Kolkata Knight Riders': {
        primary: 'bg-purple-700',
        text: 'text-purple-700',
        light: 'bg-purple-100',
        border: 'border-purple-700'
      },
      'Lucknow Super Giants': {
        primary: 'bg-sky-600',
        text: 'text-sky-600',
        light: 'bg-sky-100',
        border: 'border-sky-600'
      },
      'Mumbai Indians': {
        primary: 'bg-blue-500',
        text: 'text-blue-500',
        light: 'bg-blue-100',
        border: 'border-blue-500'
      },
      'Punjab Kings': {
        primary: 'bg-red-600',
        text: 'text-red-600',
        light: 'bg-red-100',
        border: 'border-red-600'
      },
      'Rajasthan Royals': {
        primary: 'bg-pink-600',
        text: 'text-pink-600',
        light: 'bg-pink-100',
        border: 'border-pink-600'
      },
      'Royal Challengers Bengaluru': {
        primary: 'bg-red-700',
        text: 'text-red-700',
        light: 'bg-red-100',
        border: 'border-red-700'
      },
      'Sunrisers Hyderabad': {
        primary: 'bg-orange-600',
        text: 'text-orange-600',
        light: 'bg-orange-100',
        border: 'border-orange-600'
      },
      'Tbc': {
        primary: 'bg-gray-500',
        text: 'text-gray-500',
        light: 'bg-gray-100',
        border: 'border-gray-500'
      }
    };
    
    return teamColors[teamName] || {
      primary: 'bg-gray-800',
      text: 'text-gray-800',
      light: 'bg-gray-100',
      border: 'border-gray-800'
    };
  };

  const getTeamLogo = (teamName: string) => {
    // Placeholder for team logos
    const initials = teamName
      .split(' ')
      .map(word => word[0])
      .join('')
      .substring(0, 3);
      
    const colors = getTeamColor(teamName);
    
    return (
      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${colors.primary} text-white font-bold`}>
        {teamName === 'Tbc' ? '?' : initials}
      </div>
    );
  };

  // Filter matches based on search term and activeFilter
  const filteredMatches = matches.map(dateGroup => {
    const filteredMatchesForDate = dateGroup.matches.filter(match => {
      // Apply search filter
      const matchesSearch = 
        match.teams.some(team => team.toLowerCase().includes(searchTerm.toLowerCase())) ||
        match.venue.toLowerCase().includes(searchTerm.toLowerCase()) ||
        match.name.toLowerCase().includes(searchTerm.toLowerCase());
      
      // Apply category filter
      if (activeFilter === 'all') return matchesSearch;
      if (activeFilter === 'playoffs') {
        return matchesSearch && match.isPlayoff;
      }
      if (activeFilter === 'upcoming') {
        return matchesSearch && !match.matchStarted;
      }
      if (activeFilter === 'completed') {
        return matchesSearch && match.matchEnded;
      }
      return matchesSearch;
    });
    
    return {
      ...dateGroup,
      matches: filteredMatchesForDate,
      hasMatches: filteredMatchesForDate.length > 0
    };
  }).filter(group => group.hasMatches);

  // Function to handle prediction button click
  const handlePredictionClick = (match: ProcessedMatch, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering the card toggle
    
    // Log the action
    console.log(`Prediction requested for match: ${match.id}`);
    
    // Toggle the match details if not already expanded
    if (expandedMatchId !== match.id) {
      setExpandedMatchId(match.id);
      // Set to stats tab
      toggleDetailTab(match.id, 'stats');
    }
  };

  return (
    <div className="ipl-matches-container">
      <div className="ipl-matches-header">
        <div className="header-content">
          <h2 className="header-title">
            <Trophy className="trophy-icon" />
            IPL 2025 Schedule
          </h2>
          <p className="header-subtitle">Complete schedule and live updates for the IPL 2025 season</p>
        </div>
        
        <div className="search-container">
          <input
            type="text"
            placeholder="Search teams, venues..."
            className="search-input"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <svg xmlns="http://www.w3.org/2000/svg" className="search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>
      
      <div className="filters-container">
        <button 
          className={`filter-button ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          All Matches
        </button>
        <button 
          className={`filter-button ${activeFilter === 'upcoming' ? 'active' : ''}`}
          onClick={() => setActiveFilter('upcoming')}
        >
          Upcoming
        </button>
        <button 
          className={`filter-button ${activeFilter === 'completed' ? 'active' : ''}`}
          onClick={() => setActiveFilter('completed')}
        >
          Completed
        </button>
        <button 
          className={`filter-button ${activeFilter === 'playoffs' ? 'active' : ''}`}
          onClick={() => setActiveFilter('playoffs')}
        >
          Playoffs
        </button>
      </div>
      
      {/* Content */}
      <div className="matches-content">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading IPL 2025 match schedule...</p>
          </div>
        ) : error ? (
          <div className="error-state">
            <AlertCircle className="error-icon" />
            <h3>Error Loading Matches</h3>
            <p>{error}</p>
            <button className="retry-button" onClick={() => window.location.reload()}>Try Again</button>
          </div>
        ) : (
          <div className="matches-list">
            {filteredMatches.length === 0 ? (
              <div className="no-matches">
                <Info className="info-icon" />
                <p>No matches found matching your search</p>
              </div>
            ) : (
              filteredMatches.map((dateGroup, groupIndex) => (
                <div key={groupIndex} className="date-group">
                  <div className="date-header">
                    <CalendarDays className="calendar-icon" />
                    {dateGroup.date}
                  </div>
                  
                  <div className="matches-for-date">
                    {dateGroup.matches.map((match) => (
                      <div key={match.id} className="match-container">
                        {/* Match Card */}
                        <div 
                          className={`match-card ${expandedMatchId === match.id ? 'expanded' : ''}`}
                          onClick={() => toggleMatchDetails(match.id)}
                        >
                          <div className="match-header">
                            <div className="match-number">
                              {match.isPlayoff ? (
                                <div className="playoff-indicator">
                                  <Trophy className="playoff-icon" />
                                </div>
                              ) : (
                                <div className="regular-match">
                                  <span className="match-num">
                                    {match.matchNumber ? match.matchNumber.replace(/[^0-9]/g, '') : ''}
                                  </span>
                                </div>
                              )}
                              
                              <div className="match-meta">
                                <div className="match-type">
                                  {getStatusLabel(match)}
                                </div>
                                <div className="match-time">
                                  {match.formattedTime}
                                </div>
                              </div>
                            </div>
                            
                            <div className="match-status">
                              <span className={`status-indicator ${match.status.toLowerCase().replace(/\s+/g, '-')}`}>
                                {match.status}
                              </span>
                              {expandedMatchId === match.id ? (
                                <ChevronDown className="expand-icon" />
                              ) : (
                                <ChevronRight className="expand-icon" />
                              )}
                            </div>
                          </div>
                          
                          <div className="teams-container">
                            <div className="team team-1">
                              {getTeamLogo(match.teams[0])}
                              <span className="team-name" style={{color: getTeamColor(match.teams[0]).text.replace('text-', '')}}>
                                {match.teams[0]}
                              </span>
                            </div>
                            
                            <div className="versus">VS</div>
                            
                            <div className="team team-2">
                              <span className="team-name" style={{color: getTeamColor(match.teams[1]).text.replace('text-', '')}}>
                                {match.teams[1]}
                              </span>
                              {getTeamLogo(match.teams[1])}
                            </div>
                          </div>
                          
                          <div className="venue-info">
                            <MapPin className="venue-icon" />
                            {match.venue}
                          </div>
                        </div>
                        
                        {/* Expanded Details */}
                        {expandedMatchId === match.id && (
                          <div className="match-details">
                            <div className="details-tabs">
                              <button 
                                className={`tab-button ${activeTabs[match.id]?.overview ? 'active' : ''}`}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleDetailTab(match.id, 'overview');
                                }}
                              >
                                Overview
                              </button>
                              <button 
                                className={`tab-button ${activeTabs[match.id]?.stats ? 'active' : ''}`}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleDetailTab(match.id, 'stats');
                                }}
                              >
                                Stats
                              </button>
                              {match.headToHead && (
                                <button 
                                  className={`tab-button ${activeTabs[match.id]?.h2h ? 'active' : ''}`}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleDetailTab(match.id, 'h2h');
                                  }}
                                >
                                  Head to Head
                                </button>
                              )}
                              <button 
                                className={`tab-button ${activeTabs[match.id]?.venue ? 'active' : ''}`}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleDetailTab(match.id, 'venue');
                                }}
                              >
                                Venue
                              </button>
                            </div>
                            
                            <div className="tab-content">
                              {/* Overview Tab */}
                              {activeTabs[match.id]?.overview && (
                                <div className="overview-tab">
                                  <div className="match-info-grid">
                                    <div className="info-item">
                                      <div className="info-label">Match</div>
                                      <div className="info-value">{match.name}</div>
                                    </div>
                                    <div className="info-item">
                                      <div className="info-label">Date & Time</div>
                                      <div className="info-value">{match.formattedDate}, {match.formattedTime}</div>
                                    </div>
                                    <div className="info-item">
                                      <div className="info-label">Venue</div>
                                      <div className="info-value">{match.venue}</div>
                                    </div>
                                    <div className="info-item">
                                      <div className="info-label">Status</div>
                                      <div className="info-value">{match.status}</div>
                                    </div>
                                  </div>
                                  
                                  {match.teams[0] !== 'Tbc' && match.teams[1] !== 'Tbc' && (
                                    <div className="prediction-card">
                                      <h3 className="prediction-title">
                                        <TrendingUp className="prediction-icon" />
                                        Match Prediction
                                      </h3>
                                      
                                      <div className="prediction-content">
                                        <div className="prediction-teams">
                                          <div className="prediction-team" style={{color: getTeamColor(match.teams[0]).text.replace('text-', '')}}>
                                            {match.teams[0]}
                                          </div>
                                          <div className="prediction-label">Win Probability</div>
                                          <div className="prediction-team" style={{color: getTeamColor(match.teams[1]).text.replace('text-', '')}}>
                                            {match.teams[1]}
                                          </div>
                                        </div>
                                        
                                        <div className="prediction-bar">
                                          <div 
                                            className="team1-bar"
                                            style={{
                                              width: '58%',
                                              backgroundColor: getTeamColor(match.teams[0]).text.replace('text-', '')
                                            }}
                                          ></div>
                                          <div 
                                            className="team2-bar"
                                            style={{
                                              width: '42%',
                                              backgroundColor: getTeamColor(match.teams[1]).text.replace('text-', '')
                                            }}
                                          ></div>
                                        </div>
                                        
                                        <div className="prediction-percentages">
                                          <div className="team1-percent">58%</div>
                                          <div className="team2-percent">42%</div>
                                        </div>
                                        
                                        <button 
                                          className="prediction-button"
                                          onClick={(e) => handlePredictionClick(match, e)}
                                        >
                                          View Detailed Prediction
                                        </button>
                                      </div>
                                    </div>
                                  )}
                                  
                                  <div className="match-facts">
                                    <h3 className="facts-title">Match Facts</h3>
                                    <ul className="facts-list">
                                      {match.teams[0] !== 'Tbc' && match.teams[1] !== 'Tbc' && (
                                        <>
                                          <li className="fact-item">
                                            <div className="fact-bullet"></div>
                                            {match.teams[0]} have won 3 of their last 5 matches at {match.venue.split(',')[0]}.
                                          </li>
                                          <li className="fact-item">
                                            <div className="fact-bullet"></div>
                                            {match.teams[1]} are looking for their first win against {match.teams[0]} this season.
                                          </li>
                                          <li className="fact-item">
                                            <div className="fact-bullet"></div>
                                            Teams batting first have won 54% of the matches at this venue in IPL 2025.
                                          </li>
                                        </>
                                      )}
                                      <li className="fact-item">
                                        <div className="fact-bullet"></div>
                                        This will be the {match.matchNumber ? 'match #' + match.matchNumber.replace(/[^0-9]/g, '') : ''}
                                        {match.isPlayoff ? ' playoff game' : ''} of IPL 2025.
                                      </li>
                                    </ul>
                                  </div>
                                </div>
                              )}
                              
                              {/* Stats Tab */}
                              {activeTabs[match.id]?.stats && (
                                <div className="stats-tab">
                                  <div className="team-stats-grid">
                                    {match.teamStats.map((team, index) => (
                                      <div key={index} className="team-stat-card" style={{borderColor: getTeamColor(team.team).text.replace('text-', '')}}>
                                        <h3 className="team-stat-title" style={{color: getTeamColor(team.team).text.replace('text-', '')}}>
                                          <div className="team-stat-indicator" style={{backgroundColor: getTeamColor(team.team).text.replace('text-', '')}}></div>
                                          {team.team} (#{team.position})
                                        </h3>
                                        
                                        <div className="player-stats">
                                          <div className="player-stat">
                                            <div className="player-stat-label">Top Batsman</div>
                                            <div className="player-stat-value">
                                              <Star className="star-icon" />
                                              {team.topBatsman}
                                            </div>
                                          </div>
                                          
                                          <div className="player-stat">
                                            <div className="player-stat-label">Top Bowler</div>
                                            <div className="player-stat-value">
                                              <Star className="star-icon" />
                                              {team.topBowler}
                                            </div>
                                          </div>
                                        </div>
                                        
                                        <div className="form-container">
                                          <div className="form-label">Recent Form</div>
                                          <div className="form-indicators">
                                            {team.recentForm.map((result, i) => (
                                              <div 
                                                key={i} 
                                                className={`form-indicator ${result === 'W' ? 'win' : 'loss'}`}
                                              >
                                                {result}
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                  
                                  <div className="team-comparison">
                                    <h3 className="comparison-title">
                                      <BarChart className="comparison-icon" />
                                      Team Comparison
                                    </h3>
                                    
                                    <div className="comparison-stats">
                                      <div className="comparison-stat">
                                        <div className="stat-label">Batting Power (Avg. Runs)</div>
                                        <div className="comparison-bars">
                                          <div 
                                            className="team1-stat-bar"
                                            style={{
                                              width: '65%',
                                              backgroundColor: getTeamColor(match.teams[0]).text.replace('text-', '')
                                            }}
                                          >
                                            <span className="stat-value">175</span>
                                          </div>
                                          <div 
                                            className="team2-stat-bar"
                                            style={{
                                              width: '70%',
                                              backgroundColor: getTeamColor(match.teams[1]).text.replace('text-', '')
                                            }}
                                          >
                                            <span className="stat-value">182</span>
                                          </div>
                                        </div>
                                      </div>
                                      
                                      <div className="comparison-stat">
                                        <div className="stat-label">Bowling Economy</div>
                                        <div className="comparison-bars">
                                          <div 
                                            className="team1-stat-bar"
                                            style={{
                                              width: '72%',
                                              backgroundColor: getTeamColor(match.teams[0]).text.replace('text-', '')
                                            }}
                                          >
                                            <span className="stat-value">8.2</span>
                                          </div>
                                          <div 
                                            className="team2-stat-bar"
                                            style={{
                                              width: '68%',
                                              backgroundColor: getTeamColor(match.teams[1]).text.replace('text-', '')
                                            }}
                                          >
                                            <span className="stat-value">8.5</span>
                                          </div>
                                        </div>
                                      </div>
                                      
                                      <div className="comparison-stat">
                                        <div className="stat-label">Win % this Season</div>
                                        <div className="comparison-bars">
                                          <div 
                                            className="team1-stat-bar"
                                            style={{
                                              width: '60%',
                                              backgroundColor: getTeamColor(match.teams[0]).text.replace('text-', '')
                                            }}
                                          >
                                            <span className="stat-value">60%</span>
                                          </div>
                                          <div 
                                            className="team2-stat-bar"
                                            style={{
                                              width: '75%',
                                              backgroundColor: getTeamColor(match.teams[1]).text.replace('text-', '')
                                            }}
                                          >
                                            <span className="stat-value">75%</span>
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              )}
                              
                              {/* Head to Head Tab */}
                              {activeTabs[match.id]?.h2h && match.headToHead && (
                                <div className="h2h-tab">
                                  <div className="h2h-summary">
                                    <h3 className="h2h-title">Head to Head Stats</h3>
                                    
                                    <div className="h2h-stats">
                                      <div className="team1-wins">
                                        <div className="wins-count" style={{color: getTeamColor(match.teams[0]).text.replace('text-', '')}}>
                                          {match.headToHead.team1Wins}
                                        </div>
                                        <div className="wins-label">Wins</div>
                                      </div>
                                      
                                      <div className="total-matches">
                                        <div className="matches-count">
                                          {match.headToHead.matches}
                                        </div>
                                        <div className="matches-label">Matches</div>
                                      </div>
                                      
                                      <div className="team2-wins">
                                        <div className="wins-count" style={{color: getTeamColor(match.teams[1]).text.replace('text-', '')}}>
                                          {match.headToHead.team2Wins}
                                        </div>
                                        <div className="wins-label">Wins</div>
                                      </div>
                                    </div>
                                    
                                    <div className="h2h-bar">
                                      <div 
                                        className="team1-h2h"
                                        style={{
                                          width: `${(match.headToHead.team1Wins / match.headToHead.matches) * 100}%`,
                                          backgroundColor: getTeamColor(match.teams[0]).text.replace('text-', '')
                                        }}
                                      ></div>
                                    </div>
                                    
                                    {match.headToHead.noResult > 0 && (
                                      <div className="no-result">
                                        No Result: {match.headToHead.noResult} matches
                                      </div>
                                    )}
                                  </div>
                                  
                                  <div className="h2h-details">
                                    <h3 className="details-title">Recent Encounters</h3>
                                    
                                    <div className="recent-matches">
                                      <div className="recent-match">
                                        <div className="match-date">15 Apr 2025</div>
                                        <div className="match-teams">
                                          <span style={{color: getTeamColor(match.teams[0]).text.replace('text-', '')}}>{match.teams[0]}</span>
                                          <span> beat </span>
                                          <span style={{color: getTeamColor(match.teams[1]).text.replace('text-', '')}}>{match.teams[1]}</span>
                                        </div>
                                        <div className="match-result">by 34 runs</div>
                                      </div>
                                      
                                      <div className="recent-match">
                                        <div className="match-date">28 Mar 2025</div>
                                        <div className="match-teams">
                                          <span style={{color: getTeamColor(match.teams[1]).text.replace('text-', '')}}>{match.teams[1]}</span>
                                          <span> beat </span>
                                          <span style={{color: getTeamColor(match.teams[0]).text.replace('text-', '')}}>{match.teams[0]}</span>
                                        </div>
                                        <div className="match-result">by 5 wickets</div>
                                      </div>
                                      
                                      <div className="recent-match">
                                        <div className="match-date">12 May 2024</div>
                                        <div className="match-teams">
                                          <span style={{color: getTeamColor(match.teams[0]).text.replace('text-', '')}}>{match.teams[0]}</span>
                                          <span> beat </span>
                                          <span style={{color: getTeamColor(match.teams[1]).text.replace('text-', '')}}>{match.teams[1]}</span>
                                        </div>
                                        <div className="match-result">by 7 wickets</div>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              )}
                              
                              {/* Venue Tab */}
                              {activeTabs[match.id]?.venue && (
                                <div className="venue-tab">
                                  <h3 className="venue-title">Venue Analysis</h3>
                                  
                                  <div className="venue-stats">
                                    <div className="venue-stat">
                                      <div className="venue-stat-label">Batting First Win %</div>
                                      <div className="venue-stat-bar-container">
                                        <div className="venue-stat-bar batting-first" style={{width: '54%'}}></div>
                                      </div>
                                      <div className="venue-stat-value">54%</div>
                                    </div>
                                    
                                    <div className="venue-stat">
                                      <div className="venue-stat-label">Bowling First Win %</div>
                                      <div className="venue-stat-bar-container">
                                        <div className="venue-stat-bar bowling-first" style={{width: '46%'}}></div>
                                      </div>
                                      <div className="venue-stat-value">46%</div>
                                    </div>
                                  </div>
                                  
                                  <div className="venue-metrics">
                                    <div className="venue-metric">
                                      <div className="metric-label">Average 1st Innings Score</div>
                                      <div className="metric-value">172</div>
                                    </div>
                                    
                                    <div className="venue-metric">
                                      <div className="metric-label">Highest Total</div>
                                      <div className="metric-value">243/6</div>
                                    </div>
                                    
                                    <div className="venue-metric">
                                      <div className="metric-label">Lowest Total</div>
                                      <div className="metric-value">92</div>
                                    </div>
                                    
                                    <div className="venue-metric">
                                      <div className="metric-label">Average Run Rate</div>
                                      <div className="metric-value">8.6</div>
                                    </div>
                                  </div>
                                  
                                  <div className="venue-insights">
                                    <h3 className="insights-title">Venue Insights</h3>
                                    <div className="insights-content">
                                      <p>This venue has slightly favored teams batting first with 54% of matches won by the team setting a target.</p>
                                      <p>The average first innings score at this stadium is 172, with teams typically needing to score above 180 to have a strong chance of defending.</p>
                                      <p>The pitch tends to help spinners in the middle overs, with an average economy of 7.2 compared to 8.9 for fast bowlers.</p>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default IPL2025Matches;