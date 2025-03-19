import React, { useState } from 'react';
import './CricketAnalytics.css';
import Header from './Header1';

// Import the components
import TeamsOverview from './components/TeamsOverview';
import TeamDetails from './components/TeamDetails';
import TossAnalysis from './components/TossAnalysis';
import Matches from './components/Matches';
import StatHistory from './components/StatHistory';
import PlayerAnalytics from './components/PlayerAnalytics';
import VenueAnalytics from './components/VenueAnalytics';
import MatchTrends from './components/MatchTrends';
import PredictWinner from './components/PredictWinner';
import IPL2025Matches from './components/IPL2025Matches'; // Import the new component

// Import API service
import SkyeAnalyticsApi from './api';

// Define main tab types
type MainTabType = 'predictionModel' | 'matchTrends' | 'iplHistory' | 'ipl2025'; // Added new tab type

// Define IPL History subtab types
type IplHistorySubTabType = 
  'matches' | 
  'statHistory' | 
  'teamsOverview' | 
  'playerAnalytics' | 
  'venueAnalytics' | 
  'tossAnalytics' | 
  'teamDetails';

const CricketAnalytics: React.FC = () => {
  const [activeMainTab, setActiveMainTab] = useState<MainTabType>('iplHistory');
  const [activeIplHistorySubTab, setActiveIplHistorySubTab] = useState<IplHistorySubTabType>('matches');
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const renderIplHistoryContent = () => {
    if (isLoading) {
      return <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading analytics data...</p>
      </div>;
    }

    if (error) {
      return <div className="error-container">
        <h3>Error Loading Data</h3>
        <p>{error}</p>
        <button onClick={() => setError(null)} className="retry-button">Try Again</button>
      </div>;
    }

    switch (activeIplHistorySubTab) {
      case 'matches':
        return <Matches />;
      case 'statHistory':
        return <StatHistory />;
      case 'teamsOverview':
        return (
          <TeamsOverview 
            onTeamSelect={(teamName) => {
              setSelectedTeam(teamName);
              setActiveIplHistorySubTab('teamDetails');
            }} 
          />
        );
      case 'playerAnalytics':
        return <PlayerAnalytics />;
      case 'venueAnalytics':
        return <VenueAnalytics />;
      case 'tossAnalytics':
        return <TossAnalysis />;
      case 'teamDetails':
        return selectedTeam ? (
          <TeamDetails 
            teamName={selectedTeam}
            onBackToTeams={() => setActiveIplHistorySubTab('teamsOverview')}
          />
        ) : (
          <div className="text-center text-gray-600 p-8">
            Select a team to view details
          </div>
        );
      default:
        return <Matches />;
    }
  };

  const renderMainContent = () => {
    switch (activeMainTab) {
      case 'predictionModel':
        return <PredictWinner />;
      case 'matchTrends':
        return <MatchTrends />;
      case 'ipl2025': // New case for IPL 2025 matches
        return <IPL2025Matches />;
      case 'iplHistory':
        return (
          <div className="ipl-history-container">
            <div className="sub-navigation">
              <button 
                className={`sub-nav-button ${activeIplHistorySubTab === 'matches' ? 'active' : ''}`}
                onClick={() => setActiveIplHistorySubTab('matches')}
              >
                Matches
              </button>
              <button 
                className={`sub-nav-button ${activeIplHistorySubTab === 'statHistory' ? 'active' : ''}`}
                onClick={() => setActiveIplHistorySubTab('statHistory')}
              >
                Stat History
              </button>
              <button 
                className={`sub-nav-button ${activeIplHistorySubTab === 'teamsOverview' ? 'active' : ''}`}
                onClick={() => setActiveIplHistorySubTab('teamsOverview')}
              >
                Team Overview
              </button>
              <button 
                className={`sub-nav-button ${activeIplHistorySubTab === 'playerAnalytics' ? 'active' : ''}`}
                onClick={() => setActiveIplHistorySubTab('playerAnalytics')}
              >
                Player Analytics
              </button>
              <button 
                className={`sub-nav-button ${activeIplHistorySubTab === 'venueAnalytics' ? 'active' : ''}`}
                onClick={() => setActiveIplHistorySubTab('venueAnalytics')}
              >
                Venue Analytics
              </button>
              <button 
                className={`sub-nav-button ${activeIplHistorySubTab === 'tossAnalytics' ? 'active' : ''}`}
                onClick={() => setActiveIplHistorySubTab('tossAnalytics')}
              >
                Toss Analytics
              </button>
            </div>
            <div className="sub-content">
              {renderIplHistoryContent()}
            </div>
          </div>
        );
      default:
        return <div>Select a tab to view content</div>;
    }
  };

  return (
    <div className="cricket-analytics-page">
      <Header />
      
      <div className="cricket-hero-section">
        <div className="hero-content">
          <span className="hero-badge">IPL 2025 Ready</span>
          <h1>Cricket Intelligence Platform</h1>
          <p className="hero-tagline">Transform raw cricket data into winning insights with advanced analytics and data-driven visualizations</p>
          <div className="hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">15M+</span>
              <span className="hero-stat-label">Data Points</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">All IPL</span>
              <span className="hero-stat-label">Seasons Covered</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">Real-time</span>
              <span className="hero-stat-label">Analysis</span>
            </div>
          </div>
          <div className="hero-actions">
            <button 
              className="hero-button primary"
              onClick={() => setActiveMainTab('predictionModel')}
            >
              Try Predictions
            </button>
            <button 
              className="hero-button secondary"
              onClick={() => setActiveMainTab('matchTrends')}
            >
              Explore Trends
            </button>
          </div>
        </div>
        <div className="hero-visual">
          <div className="cricket-stats-visual-enhanced">
            <div className="visual-glow"></div>
            <div className="visual-dots"></div>
            <div className="visual-line"></div>
            <div className="visual-accent"></div>
          </div>
        </div>
      </div>
      
      <div className="cricket-navigation">
        <button 
          className={`nav-button ${activeMainTab === 'ipl2025' ? 'active' : ''}`}
          onClick={() => setActiveMainTab('ipl2025')}
        >
          IPL 2025
        </button>
        <button 
          className={`nav-button ${activeMainTab === 'predictionModel' ? 'active' : ''}`}
          onClick={() => setActiveMainTab('predictionModel')}
        >
          Prediction Model
        </button>
        <button 
          className={`nav-button ${activeMainTab === 'matchTrends' ? 'active' : ''}`}
          onClick={() => setActiveMainTab('matchTrends')}
        >
          Match Trends
        </button>
        <button 
          className={`nav-button ${activeMainTab === 'iplHistory' ? 'active' : ''}`}
          onClick={() => setActiveMainTab('iplHistory')}
        >
          IPL History
        </button>
      </div>
      
      <main className="cricket-content">
        {renderMainContent()}
      </main>
      
      <div className="cricket-features">
        <h2>Our Analytics Features</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon matches-icon"></div>
            <h3>Match Analysis</h3>
            <p>Comprehensive data on all cricket matches with detailed performance metrics</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon trends-icon"></div>
            <h3>Match Trends</h3>
            <p>Discover patterns and insights across seasons, teams, and tournaments</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon prediction-icon"></div>
            <h3>Predictive Analytics</h3>
            <p>AI-powered predictions for match outcomes based on historical data</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon player-icon"></div>
            <h3>Player Insights</h3>
            <p>Deep dive into player statistics, form analysis, and performance trends</p>
          </div>
        </div>
      </div>
      
      <div className="data-showcase">
        <div className="data-content">
          <h2>Comprehensive Cricket Data Analysis</h2>
          <p>Our platform analyzes thousands of data points to provide the most comprehensive cricket analytics experience</p>
          <div className="data-highlights">
            <div className="data-metric">
              <div className="metric-value">All</div>
              <div className="metric-label">IPL Seasons</div>
            </div>
            <div className="data-metric">
              <div className="metric-value">10+</div>
              <div className="metric-label">Analytics Views</div>
            </div>
            <div className="data-metric">
              <div className="metric-value">Live</div>
              <div className="metric-label">Match Coverage</div>
            </div>
          </div>
        </div>
        <div className="data-visual"></div>
      </div>
      
      <footer className="cricket-footer">
        <p>© 2025 Skye Analytics. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default CricketAnalytics;