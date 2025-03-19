import React, { useState, useEffect } from 'react';
import SkyeAnalyticsApi from '../api';

interface TrendFilter {
  season?: number | null;
  team?: string | null;
  venue?: string | null;
}

const MatchTrends: React.FC = () => {
  const [filter, setFilter] = useState<TrendFilter>({
    season: null,
    team: null,
    venue: null
  });
  const [seasons, setSeasons] = useState<number[]>([]);
  const [teams, setTeams] = useState<string[]>([]);
  const [venues, setVenues] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [trendData, setTrendData] = useState<any>(null);

  // Fetch filter options on component mount
  useEffect(() => {
    const fetchFilterOptions = async () => {
      try {
        setIsLoading(true);
        // Get available seasons (hardcoded for demo)
        setSeasons([2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]);
        
        // Get available teams
        const teamsData = await SkyeAnalyticsApi.getAllTeams();
        setTeams(teamsData.map(team => team.team_name));
        
        // Get available venues
        const venuesData = await SkyeAnalyticsApi.getAllVenues();
        setVenues(venuesData.map(venue => venue.venue));
        
        setIsLoading(false);
      } catch (err) {
        setError('Failed to load filter options. Please try again.');
        setIsLoading(false);
      }
    };

    fetchFilterOptions();
  }, []);

  // Fetch trend data when filters change
  useEffect(() => {
    const fetchTrendData = async () => {
      try {
        setIsLoading(true);
        
        // Here you would call your API for trend data
        // For example: const data = await SkyeAnalyticsApi.getMatchTrends(filter);
        
        // Mock data for demonstration
        const mockTrendData = {
          runsScoredTrend: [
            { season: 2008, avgFirstInnings: 158, avgSecondInnings: 148 },
            { season: 2009, avgFirstInnings: 153, avgSecondInnings: 145 },
            { season: 2010, avgFirstInnings: 161, avgSecondInnings: 152 },
            // ... more seasons
            { season: 2024, avgFirstInnings: 182, avgSecondInnings: 168 }
          ],
          winRateByToss: {
            overall: 52.8,
            battingFirst: 48.2,
            fieldingFirst: 56.4
          },
          powerplayTrends: [
            { season: 2008, avgPowerplayRuns: 46.2, avgPowerplayWickets: 1.4 },
            { season: 2009, avgPowerplayRuns: 45.8, avgPowerplayWickets: 1.5 },
            // ... more seasons
            { season: 2024, avgPowerplayRuns: 54.2, avgPowerplayWickets: 1.8 }
          ],
          boundaryPercentage: {
            overall: 51.6,
            powerplay: 62.8,
            middle: 48.3,
            death: 57.9
          }
        };
        
        setTrendData(mockTrendData);
        setIsLoading(false);
      } catch (err) {
        setError('Failed to load trend data. Please try again.');
        setIsLoading(false);
      }
    };

    if (!isLoading || trendData === null) {
      fetchTrendData();
    }
  }, [filter]);

  const handleFilterChange = (name: string, value: any) => {
    setFilter(prev => ({
      ...prev,
      [name]: value === '' ? null : value
    }));
  };

  if (isLoading && !trendData) {
    return (
      <div className="analytics-section">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading trend data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-section">
        <div className="error-container">
          <h3>Error Loading Data</h3>
          <p>{error}</p>
          <button onClick={() => setError(null)} className="retry-button">Try Again</button>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-section match-trends">
      <h2>Match Trends Analysis</h2>
      <p>Discover patterns and trends across IPL seasons, teams, and venues.</p>
      
      <div className="filters-container">
        <div className="filter-group">
          <label htmlFor="season-filter">Season:</label>
          <select 
            id="season-filter"
            value={filter.season || ''}
            onChange={(e) => handleFilterChange('season', e.target.value ? parseInt(e.target.value) : '')}
            className="filter-select"
          >
            <option value="">All Seasons</option>
            {seasons.map(season => (
              <option key={season} value={season}>{season}</option>
            ))}
          </select>
        </div>
        
        <div className="filter-group">
          <label htmlFor="team-filter">Team:</label>
          <select 
            id="team-filter"
            value={filter.team || ''}
            onChange={(e) => handleFilterChange('team', e.target.value)}
            className="filter-select"
          >
            <option value="">All Teams</option>
            {teams.map(team => (
              <option key={team} value={team}>{team}</option>
            ))}
          </select>
        </div>
        
        <div className="filter-group">
          <label htmlFor="venue-filter">Venue:</label>
          <select 
            id="venue-filter"
            value={filter.venue || ''}
            onChange={(e) => handleFilterChange('venue', e.target.value)}
            className="filter-select"
          >
            <option value="">All Venues</option>
            {venues.map(venue => (
              <option key={venue} value={venue}>{venue}</option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="trends-grid">
        {/* Runs Scored Trend */}
        <div className="trend-card">
          <h3>Runs Scoring Trend</h3>
          <div className="chart-container">
            <div className="chart-placeholder runs-trend-chart">
              {/* This would be replaced with an actual chart component */}
              <div className="chart-note">
                Avg. First Innings: 170.2 runs<br />
                Avg. Second Innings: 156.8 runs
              </div>
            </div>
          </div>
          <div className="trend-insight">
            <span className="insight-badge">Insight</span>
            <p>Average first innings scores have increased by 15% over the last 5 seasons, while second innings scores show higher variability.</p>
          </div>
        </div>
        
        {/* Win Rate by Toss */}
        <div className="trend-card">
          <h3>Win Rate by Toss Decision</h3>
          <div className="chart-container">
            <div className="chart-placeholder toss-win-chart">
              {/* This would be replaced with an actual chart component */}
              <div className="chart-note">
                Batting First: 48.2% wins<br />
                Fielding First: 56.4% wins
              </div>
            </div>
          </div>
          <div className="trend-insight">
            <span className="insight-badge">Insight</span>
            <p>Teams choosing to field first after winning the toss have maintained a consistent advantage across seasons.</p>
          </div>
        </div>
        
        {/* Powerplay Trends */}
        <div className="trend-card">
          <h3>Powerplay Performance Trends</h3>
          <div className="chart-container">
            <div className="chart-placeholder powerplay-chart">
              {/* This would be replaced with an actual chart component */}
              <div className="chart-note">
                Avg. Powerplay Runs: 54.2<br />
                Avg. Powerplay Wickets: 1.8
              </div>
            </div>
          </div>
          <div className="trend-insight">
            <span className="insight-badge">Insight</span>
            <p>Powerplay scoring rates have increased steadily since 2019, with teams now averaging 9+ runs per over without losing additional wickets.</p>
          </div>
        </div>
        
        {/* Boundary Percentage */}
        <div className="trend-card">
          <h3>Boundary Percentage by Phase</h3>
          <div className="chart-container">
            <div className="chart-placeholder boundary-chart">
              {/* This would be replaced with an actual chart component */}
              <div className="chart-note">
                Powerplay: 62.8%<br />
                Middle Overs: 48.3%<br />
                Death Overs: 57.9%
              </div>
            </div>
          </div>
          <div className="trend-insight">
            <span className="insight-badge">Insight</span>
            <p>The proportion of runs scored from boundaries has increased in the death overs (16-20), highlighting improved finishing skills.</p>
          </div>
        </div>
      </div>
      
      <div className="season-comparison">
        <h3>Season-by-Season Comparison</h3>
        <div className="season-table-container">
          <table className="season-table">
            <thead>
              <tr>
                <th>Season</th>
                <th>Avg. Match Total</th>
                <th>Avg. 1st Innings</th>
                <th>Avg. 2nd Innings</th>
                <th>Chasing Win %</th>
                <th>Highest Total</th>
                <th>Lowest Total</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>2024</td>
                <td>347.8</td>
                <td>182.3</td>
                <td>165.5</td>
                <td>56.4%</td>
                <td>257</td>
                <td>89</td>
              </tr>
              <tr>
                <td>2023</td>
                <td>338.2</td>
                <td>176.8</td>
                <td>161.4</td>
                <td>52.7%</td>
                <td>246</td>
                <td>92</td>
              </tr>
              <tr>
                <td>2022</td>
                <td>325.6</td>
                <td>170.2</td>
                <td>155.4</td>
                <td>54.9%</td>
                <td>235</td>
                <td>96</td>
              </tr>
              <tr>
                <td>2021</td>
                <td>320.4</td>
                <td>164.8</td>
                <td>155.6</td>
                <td>55.3%</td>
                <td>232</td>
                <td>94</td>
              </tr>
              <tr>
                <td>2020</td>
                <td>317.5</td>
                <td>162.3</td>
                <td>155.2</td>
                <td>51.8%</td>
                <td>228</td>
                <td>98</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <div className="key-findings">
        <h3>Key Findings</h3>
        <div className="findings-grid">
          <div className="finding-card">
            <div className="finding-icon"></div>
            <h4>Run Rate Evolution</h4>
            <p>Overall run rates have increased by 12% over the past decade, with the most significant jump occurring after 2018.</p>
          </div>
          <div className="finding-card">
            <div className="finding-icon"></div>
            <h4>Toss Impact</h4>
            <p>Toss impact varies significantly by venue, with some grounds showing up to 70% win rate advantage for the toss winner.</p>
          </div>
          <div className="finding-card">
            <div className="finding-icon"></div>
            <h4>Batting Approach</h4>
            <p>Teams have become more aggressive in the powerplay, with the average powerplay score increasing by 15 runs since 2015.</p>
          </div>
          <div className="finding-card">
            <div className="finding-icon"></div>
            <h4>Chase Success</h4>
            <p>Teams successfully chasing scores above 180 has doubled in the last five seasons compared to the first decade of the IPL.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchTrends;