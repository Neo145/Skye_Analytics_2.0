import React, { useState } from 'react';
import './CricketAnalytics.css';
import Header from './Header1';

// Import the components
import TeamsOverview from './components/TeamsOverview';
import TeamDetails from './components/TeamDetails';
import TossAnalysis from './components/TossAnalysis';
import Matches from './components/Matches';
import StatHistory from './components/StatHistory';
import PredictWinner from './components/PredictWinner';
import PlayerAnalytics from './components/PlayerAnalytics';
import VenueAnalytics from './components/VenueAnalytics';

// Define content types
type ContentType = 
  'matches' | 
  'statHistory' | 
  'predictWinner' | 
  'playerAnalytics' | 
  'venueAnalytics' | 
  'tossAnalytics' | 
  'teamsOverview' | 
  'teamDetails';

const CricketAnalytics: React.FC = () => {
  const [activeContent, setActiveContent] = useState<ContentType>('matches');
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);

  const renderContent = () => {
    switch (activeContent) {
      case 'matches':
        return <Matches />;
      case 'statHistory':
        return <StatHistory />;
      case 'predictWinner':
        return <PredictWinner />;
      case 'playerAnalytics':
        return <PlayerAnalytics />;
      case 'venueAnalytics':
        return <VenueAnalytics />;
      case 'tossAnalytics':
        return <TossAnalysis />;
      case 'teamsOverview':
        return (
          <TeamsOverview 
            onTeamSelect={(teamName) => {
              setSelectedTeam(teamName);
              setActiveContent('teamDetails');
            }} 
          />
        );
      case 'teamDetails':
        return selectedTeam ? (
          <TeamDetails 
            teamName={selectedTeam}
            onBackToTeams={() => setActiveContent('teamsOverview')}
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

  return (
    <div className="cricket-analytics-page">
      <Header />
      
      <div className="cricket-hero-section">
        <div className="hero-content">
          <span className="hero-badge">IPL 2025 Ready</span>
          <h1>Cricket Intelligence Platform</h1>
          <p className="hero-tagline">Transform raw cricket data into winning insights with advanced analytics and AI-powered predictions</p>
          <div className="hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">87%</span>
              <span className="hero-stat-label">Prediction Accuracy</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">15M+</span>
              <span className="hero-stat-label">Data Points</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">Real-time</span>
              <span className="hero-stat-label">Analysis</span>
            </div>
          </div>
          <div className="hero-actions">
            <button 
              className="hero-button primary"
              onClick={() => setActiveContent('predictWinner')}
            >
              Try Predictions
            </button>
            <button 
              className="hero-button secondary"
              onClick={() => setActiveContent('matches')}
            >
              Explore Analytics
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
          className={`nav-button ${activeContent === 'matches' ? 'active' : ''}`}
          onClick={() => setActiveContent('matches')}
        >
          Matches
        </button>
        <button 
          className={`nav-button ${activeContent === 'statHistory' ? 'active' : ''}`}
          onClick={() => setActiveContent('statHistory')}
        >
          Stat History
        </button>
        <button 
          className={`nav-button ${activeContent === 'teamsOverview' ? 'active' : ''}`}
          onClick={() => setActiveContent('teamsOverview')}
        >
          Teams Overview
        </button>
        <button 
          className={`nav-button ${activeContent === 'predictWinner' ? 'active' : ''}`}
          onClick={() => setActiveContent('predictWinner')}
        >
          Predict Winner
        </button>
        <button 
          className={`nav-button ${activeContent === 'playerAnalytics' ? 'active' : ''}`}
          onClick={() => setActiveContent('playerAnalytics')}
        >
          Player Analytics
        </button>
        <button 
          className={`nav-button ${activeContent === 'venueAnalytics' ? 'active' : ''}`}
          onClick={() => setActiveContent('venueAnalytics')}
        >
          Venue Analytics
        </button>
        <button 
          className={`nav-button ${activeContent === 'tossAnalytics' ? 'active' : ''}`}
          onClick={() => setActiveContent('tossAnalytics')}
        >
          Toss Analytics
        </button>
      </div>
      
      <main className="cricket-content">
        {renderContent()}
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
            <div className="feature-icon prediction-icon"></div>
            <h3>ML Predictions</h3>
            <p>Advanced machine learning models to predict match outcomes with high accuracy</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon player-icon"></div>
            <h3>Player Insights</h3>
            <p>Deep dive into player statistics, form analysis, and performance trends</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon venue-icon"></div>
            <h3>Venue Intelligence</h3>
            <p>Understand how different venues impact game dynamics and strategies</p>
          </div>
        </div>
      </div>
      
      <div className="ml-prediction-showcase">
        <div className="ml-content">
          <h2>ML-Powered Cricket Predictions</h2>
          <p>Our state-of-the-art machine learning models analyze thousands of data points to provide accurate match predictions</p>
          <div className="accuracy-meter">
            <div className="accuracy-label">Prediction Accuracy</div>
            <div className="accuracy-bar">
              <div className="accuracy-fill" style={{ width: '87%' }}></div>
            </div>
            <div className="accuracy-value">87%</div>
          </div>
        </div>
        <div className="ml-visual"></div>
      </div>
      
      <footer className="cricket-footer">
        <p>© 2025 Skye Analytics. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default CricketAnalytics;