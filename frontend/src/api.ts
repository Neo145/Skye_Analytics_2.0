import axios from 'axios';

// Base URL for the API
const BASE_URL = 'https://skye-analytics-2-0.onrender.com/api';

// Interfaces for different data types
export interface Team {
  team_name: string;
  seasons_played: number;
  matches_played: number;
  matches_won: number;
  win_percentage: number;
}

export interface Venue {
  venue: string;
  city: string;
  matches_hosted: number;
  seasons_used: number;
  first_season: number;
  last_season: number;
}

export interface Match {
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

export interface TossAnalysis {
  overall_stats: {
    total_matches: number;
    chose_bat: number | null;
    chose_field: number | null;
    chose_bat_percentage: number | null;
    chose_field_percentage: number | null;
    won_after_batting: number | null;
    won_after_fielding: number | null;
    won_after_batting_percentage: number | null;
    won_after_fielding_percentage: number | null;
    toss_winner_won_match: number | null;
    toss_winner_win_percentage: number | null;
  };
  season_stats: any[];
  team_stats: any[];
  venue_stats: any[];
  filters_applied: {
    season?: number;
    team?: string;
    venue?: string;
  };
}

export interface HeadToHeadRecord {
  team_a: string;
  team_b: string;
  matches_played: number;
  team_a_wins: number;
  team_b_wins: number;
  no_results: number;
  team_a_win_percentage: number;
  team_b_win_percentage: number;
}

// Determine API Base URL
const isLocalDevelopment = window.location.hostname === 'localhost';
const API_BASE = isLocalDevelopment 
  ? 'http://localhost:8000/api' 
  : BASE_URL;

// Create an axios instance with default configurations
const axiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Error handling interceptor
axiosInstance.interceptors.response.use(
  response => response,
  error => {
    const errorMessage = error.response?.data?.detail || error.message;
    console.error('API Error:', errorMessage);
    return Promise.reject(errorMessage);
  }
);

// API Service Class
export class SkyeAnalyticsApi {
  // Teams Endpoints
  static async getAllTeams(): Promise<Team[]> {
    try {
      const response = await axiosInstance.get('/teams/');
      return response.data.teams;
    } catch (error) {
      console.error('Error fetching teams:', error);
      throw error;
    }
  }

  static async getTeamDetails(teamName: string): Promise<any> {
    try {
      const response = await axiosInstance.get(`/teams/${encodeURIComponent(teamName)}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching details for team ${teamName}:`, error);
      throw error;
    }
  }

  // Venues Endpoints
  static async getAllVenues(): Promise<Venue[]> {
    try {
      const response = await axiosInstance.get('/venues/');
      return response.data.venues;
    } catch (error) {
      console.error('Error fetching venues:', error);
      throw error;
    }
  }

  // Matches Endpoints
  static async getAllMatches(): Promise<Match[]> {
    try {
      const response = await axiosInstance.get('/matches/');
      return response.data.matches;
    } catch (error) {
      console.error('Error fetching matches:', error);
      throw error;
    }
  }

  static async getMatchesBySeason(season: number): Promise<any> {
    try {
      const response = await axiosInstance.get(`/matches/seasons/${season}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching matches for season ${season}:`, error);
      throw error;
    }
  }

  // Toss Analysis Endpoints
  static async getTossAnalysis(params?: {
    season?: number;
    team?: string;
    venue?: string;
  }): Promise<TossAnalysis> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.season) queryParams.append('season', params.season.toString());
      if (params?.team) queryParams.append('team', params.team);
      if (params?.venue) queryParams.append('venue', params.venue);

      const response = await axiosInstance.get(`/toss/analysis?${queryParams}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching toss analysis:', error);
      throw error;
    }
  }

  static async getTossTrends(): Promise<any[]> {
    try {
      const response = await axiosInstance.get('/toss/trends');
      return response.data.decision_trends;
    } catch (error) {
      console.error('Error fetching toss trends:', error);
      throw error;
    }
  }

  // Head-to-Head Endpoints
  static async getAllHeadToHeadRecords(): Promise<HeadToHeadRecord[]> {
    try {
      const response = await axiosInstance.get('/head-to-head/');
      return response.data.head_to_head_records;
    } catch (error) {
      console.error('Error fetching head-to-head records:', error);
      throw error;
    }
  }

  static async getHeadToHeadBetweenTeams(team1: string, team2: string, season?: number): Promise<any> {
    try {
      const url = season 
        ? `/head-to-head/${encodeURIComponent(team1)}/${encodeURIComponent(team2)}?season=${season}`
        : `/head-to-head/${encodeURIComponent(team1)}/${encodeURIComponent(team2)}`;
      
      const response = await axiosInstance.get(url);
      return response.data;
    } catch (error) {
      console.error(`Error fetching head-to-head for ${team1} vs ${team2}:`, error);
      throw error;
    }
  }

  static async getStrongestRivalries(minMatches: number = 5): Promise<any[]> {
    try {
      const response = await axiosInstance.get(`/head-to-head/strongest-rivalries?min_matches=${minMatches}`);
      return response.data.rivalries;
    } catch (error) {
      console.error('Error fetching strongest rivalries:', error);
      throw error;
    }
  }
  
  // Prediction Endpoints
  static async predictMatch(team1Id: number, team2Id: number, venueId: number, seasonYear: number = 2024): Promise<any> {
    try {
      const response = await axiosInstance.get(`/predictions/match/${team1Id}/${team2Id}/${venueId}?season_year=${seasonYear}`);
      return response.data;
    } catch (error) {
      console.error('Error predicting match outcome:', error);
      throw error;
    }
  }
  
  static async getFantasyTeam(team1Id: number, team2Id: number, venueId: number, budget: number = 100): Promise<any> {
    try {
      const response = await axiosInstance.post('/predictions/fantasy-team', {
        team1_id: team1Id,
        team2_id: team2Id,
        venue_id: venueId,
        budget: budget
      });
      return response.data;
    } catch (error) {
      console.error('Error optimizing fantasy team:', error);
      throw error;
    }
  }
  
  static async getPlayerPrediction(playerId: number, team1Id: number, team2Id: number, 
                                  venueId: number, playerTeamId: number): Promise<any> {
    try {
      const response = await axiosInstance.get(
        `/predictions/player/${playerId}?team1_id=${team1Id}&team2_id=${team2Id}&venue_id=${venueId}&player_team_id=${playerTeamId}`
      );
      return response.data;
    } catch (error) {
      console.error(`Error predicting player performance for player ${playerId}:`, error);
      throw error;
    }
  }
}

// Export as default for easier importing
export default SkyeAnalyticsApi;