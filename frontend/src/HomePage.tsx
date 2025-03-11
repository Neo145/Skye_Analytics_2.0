import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';
import Header from './Header';

const HomePage: React.FC = () => {
  return (
    <>
      <Header />
      <div className="homepage-container">
        {/* Hero Section with Call to Action Buttons */}
        <section className="hero-section">
          <div className="hero-content">
            <h1>Skye Analytics</h1>
            <h2>AI-Powered Predictions for Cricket & Stocks</h2>
            <p className="hero-message">
              Leverage cutting-edge machine learning models to gain actionable insights.
              Our predictive analytics transforms complex data into clear, winning strategies.
            </p>
            <div className="cta-buttons">
              <Link  to="/cricket" className="cta-button cricket">
                <span className="icon">🏏</span>
                Cricket Analytics
              </Link>
              <button className="cta-button stock">
                <span className="icon">📈</span>
                Stock Analytics
              </button>
            </div>
            <div className="hero-highlight">
              <div className="badge">Live</div>
              <p>Special IPL coverage with real-time predictions starting March 22nd!</p>
            </div>
          </div>
          <div className="hero-graphic">
            <div className="analytics-visual">
              <div className="circle-1"></div>
              <div className="circle-2"></div>
              <div className="data-point dp-1"></div>
              <div className="data-point dp-2"></div>
              <div className="data-point dp-3"></div>
              <div className="data-line dl-1"></div>
              <div className="data-line dl-2"></div>
              <div className="prediction-line"></div>
            </div>
          </div>
        </section>

        {/* ML Models Section */}
        <section className="ml-models-section">
          <div className="section-header">
            <h2>Advanced ML Prediction Models</h2>
            <p>Our proprietary machine learning algorithms deliver industry-leading prediction accuracy</p>
          </div>
          
          <div className="models-grid">
            <div className="model-card">
              <div className="model-icon match-predictor"></div>
              <h3>Match Outcome Predictor</h3>
              <div className="accuracy-meter">
                <div className="accuracy-bar" style={{width: '92%'}}></div>
                <span className="accuracy-text">92% Accuracy</span>
              </div>
              <p>Advanced neural networks analyze historical match data, current form, player stats, and venue conditions to predict match outcomes with exceptional accuracy.</p>
              <ul className="model-features">
                <li>Real-time in-game prediction updates</li>
                <li>Head-to-head analysis integration</li>
                <li>Weather impact assessment</li>
              </ul>
            </div>
            
            <div className="model-card">
              <div className="model-icon player-performance"></div>
              <h3>Player Performance Forecast</h3>
              <div className="accuracy-meter">
                <div className="accuracy-bar" style={{width: '89%'}}></div>
                <span className="accuracy-text">89% Accuracy</span>
              </div>
              <p>Our ensemble learning models predict individual player performances by analyzing technical strengths, recent form, and matchup-specific statistics.</p>
              <ul className="model-features">
                <li>Position-specific performance metrics</li>
                <li>Form curve analysis</li>
                <li>Opposition-specific performance predictions</li>
              </ul>
            </div>
            
            <div className="model-card">
              <div className="model-icon stock-trend"></div>
              <h3>Stock Trend Analyzer</h3>
              <div className="accuracy-meter">
                <div className="accuracy-bar" style={{width: '87%'}}></div>
                <span className="accuracy-text">87% Accuracy</span>
              </div>
              <p>Time-series forecasting models powered by LSTM networks predict market movements by analyzing historical patterns, news sentiment, and macroeconomic indicators.</p>
              <ul className="model-features">
                <li>Multi-timeframe prediction windows</li>
                <li>Volatility forecasting</li>
                <li>Sector-specific trend analysis</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Analytics Overview */}
        <section className="overview-section">
          <div className="dual-color-header">
            <div className="line-blue"></div>
            <h2>Comprehensive Analytics Solutions</h2>
            <div className="line-green"></div>
          </div>
          
          <div className="solutions-grid">
            <div className="solution-card cricket-card">
              <div className="card-header">
                <h3>Cricket Analytics</h3>
                <span className="status active">Active</span>
              </div>
              <p>Deep analysis of cricket matches, teams, and players with predictive insights and performance metrics.</p>
              <ul className="feature-list">
                <li>Team performance tracking across tournaments</li>
                <li>Player statistics and form analysis</li>
                <li>Match prediction models</li>
                <li>Venue-specific performance insights</li>
                <li>Head-to-head analysis</li>
              </ul>
              <button className="explore-button">Explore Now</button>
            </div>
            
            <div className="solution-card stock-card">
              <div className="card-header">
                <h3>Stock Market Analytics</h3>
                <span className="status coming-soon">Coming Soon</span>
              </div>
              <p>Advanced stock market analysis tools to identify trends, optimize portfolios, and maximize returns.</p>
              <ul className="feature-list">
                <li>Real-time market data analysis</li>
                <li>Technical indicator visualization</li>
                <li>Portfolio performance tracking</li>
                <li>Risk assessment models</li>
                <li>Market trend predictions</li>
              </ul>
              <button className="explore-button disabled">Join Waitlist</button>
            </div>
          </div>
        </section>

        {/* Data Process Section */}
        <section className="data-process-section">
          <div className="dual-color-header reversed">
            <div className="line-green"></div>
            <h2>How Our ML Predictions Work</h2>
            <div className="line-blue"></div>
          </div>
          
          <div className="process-steps">
            <div className="process-step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3>Data Collection</h3>
                <p>We collect and cleanse vast datasets from multiple sources including historical matches, player statistics, venue data, and external factors.</p>
              </div>
            </div>
            
            <div className="process-step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3>Feature Engineering</h3>
                <p>Our experts transform raw data into meaningful features that capture complex patterns and relationships between different variables.</p>
              </div>
            </div>
            
            <div className="process-step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3>Model Training</h3>
                <p>Multiple machine learning algorithms are trained on historical data, with continuous optimization through advanced techniques like gradient boosting.</p>
              </div>
            </div>
            
            <div className="process-step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h3>Validation & Testing</h3>
                <p>Models undergo rigorous validation against real-world outcomes to ensure prediction accuracy and reliability.</p>
              </div>
            </div>
            
            <div className="process-step">
              <div className="step-number">5</div>
              <div className="step-content">
                <h3>Real-Time Predictions</h3>
                <p>Our system delivers actionable predictions through an intuitive interface, updated in real-time as new data becomes available.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Current Focus Section */}
        <section className="focus-section">
          <div className="section-header">
            <h2>Current Focus: IPL Season 2025</h2>
            <p>Comprehensive coverage with real-time predictions and in-depth analysis</p>
          </div>
          <div className="stats-grid">
            <div className="stat-box">
              <h3>All Matches</h3>
              <p>Complete coverage of every IPL game</p>
            </div>
            <div className="stat-box">
              <h3>Real-Time</h3>
              <p>Live prediction updates during games</p>
            </div>
            <div className="stat-box">
              <h3>All Teams</h3>
              <p>Detailed analysis for every franchise</p>
            </div>
            <div className="stat-box">
              <h3>ML Powered</h3>
              <p>Industry-leading prediction accuracy</p>
            </div>
          </div>
        </section>

        {/* Call to Action */}
        <section className="final-cta">
          <div className="cta-content">
            <h2>Ready to Transform Your Analytics Experience?</h2>
            <p>Join Skye Analytics today and discover the power of ML-driven insights</p>
            <button className="primary-button">Get Started Now</button>
          </div>
          <div className="cta-visual">
            <div className="visual-element ve-1"></div>
            <div className="visual-element ve-2"></div>
            <div className="visual-element ve-3"></div>
          </div>
        </section>

        {/* Footer */}
        <footer className="footer">
          <div className="footer-content">
            <div className="footer-brand">
              <div className="footer-logo">
                <span className="logo-blue">Skye</span>
                <span className="logo-green">Analytics</span>
              </div>
              <p>Transforming data into winning decisions through advanced ML models</p>
            </div>
            <div className="footer-links">
              <div className="link-column">
                <h4>Products</h4>
                <ul>
                  <li><a href="#">Cricket Analytics</a></li>
                  <li><a href="#">Stock Analytics</a></li>
                  <li><a href="#">Custom Solutions</a></li>
                </ul>
              </div>
              <div className="link-column">
                <h4>Company</h4>
                <ul>
                  <li><a href="#">About Us</a></li>
                  <li><a href="#">Contact</a></li>
                  <li><a href="#">Careers</a></li>
                </ul>
              </div>
              <div className="link-column">
                <h4>Resources</h4>
                <ul>
                  <li><a href="#">Blog</a></li>
                  <li><a href="#">Documentation</a></li>
                  <li><a href="#">Support</a></li>
                </ul>
              </div>
            </div>
          </div>
          <div className="copyright">
            <p>&copy; 2025 Skye Analytics. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </>
  );
};

export default HomePage;