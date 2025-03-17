import React, { useState } from 'react';
import './Header.css';

const Header: React.FC = () => {
  const [menuOpen, setMenuOpen] = useState(false);

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  return (
    <header className="site-header">
      <div className="header-container">
        <div className="logo-container">
          <div className="logo">
            <span className="logo-blue">Skye</span>
            <span className="logo-green">Analytics</span>
          </div>
          <p className="tagline">Data-Driven Insights</p>
        </div>
        
        <button className="mobile-menu-btn" onClick={toggleMenu}>
          <span></span>
          <span></span>
          <span></span>
        </button>
        
        <nav className={`main-nav ${menuOpen ? 'open' : ''}`}>
          <ul className="nav-links">
            <li><a href="#" className="active">Home</a></li>
            <li><a href="/cricket">Cricket Analytics</a></li>
            <li><a href="#">Stock Analytics</a></li>
            <li><a href="#">About</a></li>
            <li><a href="#">Contact</a></li>
          </ul>
          <div className="nav-buttons">
            <button className="login-btn">Log In</button>
            <button className="signup-btn">Sign Up</button>
          </div>
        </nav>
      </div>
    </header>
  );
};

export default Header;

