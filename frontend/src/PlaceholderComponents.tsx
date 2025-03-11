// // These are placeholder components for each section of the Cricket Analytics page
// import React from 'react';

// // Matches Component
// export const Matches: React.FC = () => (
//   <div className="analytics-section">
//     <h2>Match Analysis</h2>
//     <p>Comprehensive data on all cricket matches with detailed statistics and metrics.</p>
//     <div className="analytics-chart">
//       <div className="chart-title">Recent Match Results</div>
//       <div className="chart-content matches-chart"></div>
//     </div>
//     <div className="analytics-stats">
//       <div className="stat-box">
//         <h3>Total Matches</h3>
//         <p>1,208</p>
//       </div>
//       <div className="stat-box">
//         <h3>Last 30 Days</h3>
//         <p>24</p>
//       </div>
//       <div className="stat-box">
//         <h3>Upcoming</h3>
//         <p>12</p>
//       </div>
//       <div className="stat-box">
//         <h3>Average Score</h3>
//         <p>158</p>
//       </div>
//     </div>
//   </div>
// );

// // Statistics History Component
// export const StatHistory: React.FC = () => (
//   <div className="analytics-section">
//     <h2>Statistics History</h2>
//     <p>Track the evolution of cricket statistics over time with historical data analysis.</p>
//     <div className="analytics-chart">
//       <div className="chart-title">Run Rate Evolution (2010-2025)</div>
//       <div className="chart-content stat-history-chart"></div>
//     </div>
//     <div className="analytics-stats">
//       <div className="stat-box">
//         <h3>Historical Matches</h3>
//         <p>2,450</p>
//       </div>
//       <div className="stat-box">
//         <h3>Time Period</h3>
//         <p>15 Years</p>
//       </div>
//       <div className="stat-box">
//         <h3>Data Points</h3>
//         <p>85K+</p>
//       </div>
//       <div className="stat-box">
//         <h3>Tournament Records</h3>
//         <p>48</p>
//       </div>
//     </div>
//   </div>
// );

// // Predict Winner Component
// export const PredictWinner: React.FC = () => (
//   <div className="analytics-section">
//     <h2>Predict Winner</h2>
//     <p>Our advanced ML algorithms predict match outcomes with high accuracy based on historical data and current form.</p>
//     <div className="prediction-model">
//       <div className="model-header">
//         <h3>Match Prediction</h3>
//         <div className="model-accuracy">87% Accuracy</div>
//       </div>
//       <div className="teams-container">
//         <div className="team-selector">
//           <label>Team 1</label>
//           <select className="team-select">
//             <option>Mumbai Indians</option>
//             <option>Chennai Super Kings</option>
//             <option>Royal Challengers Bangalore</option>
//             <option>Kolkata Knight Riders</option>
//             <option>Delhi Capitals</option>
//           </select>
//         </div>
//         <div className="vs-indicator">VS</div>
//         <div className="team-selector">
//           <label>Team 2</label>
//           <select className="team-select">
//             <option>Chennai Super Kings</option>
//             <option>Mumbai Indians</option>
//             <option>Royal Challengers Bangalore</option>
//             <option>Kolkata Knight Riders</option>
//             <option>Delhi Capitals</option>
//           </select>
//         </div>
//       </div>
//       <div className="venue-selector">
//         <label>Venue</label>
//         <select className="venue-select">
//           <option>Wankhede Stadium</option>
//           <option>M.A. Chidambaram Stadium</option>
//           <option>Eden Gardens</option>
//           <option>M. Chinnaswamy Stadium</option>
//         </select>
//       </div>
//       <button className="predict-button">Predict Winner</button>
//       <div className="prediction-result">
//         <div className="result-bar">
//           <div className="team-a" style={{ width: '65%' }}>
//             <span>Mumbai Indians</span>
//             <span className="percentage">65%</span>
//           </div>
//           <div className="team-b" style={{ width: '35%' }}>
//             <span className="percentage">35%</span>
//             <span>Chennai Super Kings</span>
//           </div>
//         </div>
//         <div className="prediction-factors">
//           <h4>Key Factors:</h4>
//           <ul>
//             <li>Head-to-head: Mumbai Indians lead 20-14</li>
//             <li>Recent form: MI won 3 of last 5 matches</li>
//             <li>Venue advantage: MI has 68% win rate at Wankhede</li>
//           </ul>
//         </div>
//       </div>
//     </div>
//   </div>
// );

// // Player Analytics Component
// export const PlayerAnalytics: React.FC = () => (
//   <div className="analytics-section">
//     <h2>Player Analytics</h2>
//     <p>Dive deep into individual player statistics, performance trends, and comparative analysis.</p>
//     <div className="player-search">
//       <input type="text" placeholder="Search for a player..." className="player-search-input" />
//       <button className="search-button">Search</button>
//     </div>
//     <div className="player-profile">
//       <div className="player-header">
//         <div className="player-avatar"></div>
//         <div className="player-info">
//           <h3>Virat Kohli</h3>
//           <p>Right-handed Batsman • Royal Challengers Bangalore</p>
//         </div>
//       </div>
//       <div className="player-stats-grid">
//         <div className="stat-card">
//           <h4>Batting Average</h4>
//           <div className="stat-value">53.5</div>
//         </div>
//         <div className="stat-card">
//           <h4>Strike Rate</h4>
//           <div className="stat-value">136.8</div>
//         </div>
//         <div className="stat-card">
//           <h4>Total Runs</h4>
//           <div className="stat-value">6,624</div>
//         </div>
//         <div className="stat-card">
//           <h4>Centuries</h4>
//           <div className="stat-value">5</div>
//         </div>
//         <div className="stat-card">
//           <h4>Half Centuries</h4>
//           <div className="stat-value">44</div>
//         </div>
//         <div className="stat-card">
//           <h4>Sixes</h4>
//           <div className="stat-value">218</div>
//         </div>
//       </div>
//       <div className="player-chart">
//         <div className="chart-title">Performance Trend (Last 5 Seasons)</div>
//         <div className="chart-content player-performance-chart"></div>
//       </div>
//     </div>
//   </div>
// );

// // Venue Analytics Component
// export const VenueAnalytics: React.FC = () => (
//   <div className="analytics-section">
//     <h2>Venue Analytics</h2>
//     <p>Analyze how different venues impact game dynamics, strategy, and team performance.</p>
//     <div className="venue-dropdown">
//       <select className="venue-select-large">
//         <option>Wankhede Stadium, Mumbai</option>
//         <option>M.A. Chidambaram Stadium, Chennai</option>
//         <option>Eden Gardens, Kolkata</option>
//         <option>M. Chinnaswamy Stadium, Bangalore</option>
//       </select>
//     </div>
//     <div className="venue-stats">
//       <div className="venue-info">
//         <h3>Wankhede Stadium</h3>
//         <p>Mumbai, India • Capacity: 33,108</p>
//       </div>
//       <div className="venue-data-grid">
//         <div className="venue-stat-card">
//           <h4>Average 1st Innings Score</h4>
//           <div className="venue-stat-value">173</div>
//         </div>
//         <div className="venue-stat-card">
//           <h4>Average 2nd Innings Score</h4>
//           <div className="venue-stat-value">156</div>
//         </div>
//         <div className="venue-stat-card">
//           <h4>Highest Total</h4>
//           <div className="venue-stat-value">235/5</div>
//         </div>
//         <div className="venue-stat-card">
//           <h4>Lowest Total</h4>
//           <div className="venue-stat-value">87</div>
//         </div>
//       </div>
//       <div className="venue-insights">
//         <h4>Venue Insights</h4>
//         <ul>
//           <li>Batting first teams win 52% of matches</li>
//           <li>Average run rate in powerplay: 8.6 runs/over</li>
//           <li>Spinners economy rate: 7.8 runs/over</li>
//           <li>Fast bowlers economy rate: 8.9 runs/over</li>
//         </ul>
//       </div>
//       <div className="venue-chart">
//         <div className="chart-title">Runs Distribution by Inning Phase</div>
//         <div className="chart-content venue-chart-content"></div>
//       </div>
//     </div>
//   </div>
// );

// // Toss Analytics Component
// export const TossAnalytics: React.FC = () => (
//   <div className="analytics-section">
//     <h2>Toss Analytics</h2>
//     <p>Understand how the toss influences match outcomes across different venues and conditions.</p>
//     <div className="toss-overview">
//       <div className="toss-stat-container">
//         <div className="toss-stat">
//           <h3>Toss Winners' Match Win %</h3>
//           <div className="toss-value">58%</div>
//         </div>
//         <div className="toss-chart">
//           <div className="chart-title">Toss Impact on Match Result</div>
//           <div className="chart-content toss-impact-chart"></div>
//         </div>
//       </div>
//       <div className="toss-decision-stats">
//         <h3>Toss Decision Breakdown</h3>
//         <div className="decision-chart">
//           <div className="decision-bar">
//             <div className="bat-first" style={{ width: '42%' }}>
//               <span>Bat First</span>
//               <span className="percentage">42%</span>
//             </div>
//             <div className="field-first" style={{ width: '58%' }}>
//               <span className="percentage">58%</span>
//               <span>Field First</span>
//             </div>
//           </div>
//         </div>
//       </div>
//       <div className="toss-trends">
//         <h3>Toss Win Impact By Venue</h3>
//         <table className="toss-table">
//           <thead>
//             <tr>
//               <th>Venue</th>
//               <th>Toss Winner Win %</th>
//               <th>Preferred Choice</th>
//             </tr>
//           </thead>
//           <tbody>
//             <tr>
//               <td>Wankhede Stadium</td>
//               <td>64%</td>
//               <td>Field First (72%)</td>
//             </tr>
//             <tr>
//               <td>M.A. Chidambaram Stadium</td>
//               <td>58%</td>
//               <td>Bat First (65%)</td>
//             </tr>
//             <tr>
//               <td>Eden Gardens</td>
//               <td>52%</td>
//               <td>Field First (68%)</td>
//             </tr>
//             <tr>
//               <td>M. Chinnaswamy Stadium</td>
//               <td>61%</td>
//               <td>Field First (82%)</td>
//             </tr>
//           </tbody>
//         </table>
//       </div>
//     </div>
//   </div>
// );