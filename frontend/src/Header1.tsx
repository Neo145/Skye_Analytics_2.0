import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Header1.css';

const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <header className="header">
      <div className="header-container">
        <div className="logo-container">
          <Link to="/" className="logo-link">
            <div className="logo">
              <span className="logo-text">Skye</span>
              <span className="logo-dot"></span>
              <span className="logo-text green">Analytics</span>
            </div>
          </Link>
        </div>

        <nav className={`main-nav ${isMenuOpen ? 'active' : ''}`}>
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/cricket" className="nav-link active">Cricket</Link>
          <Link to="/stocks" className="nav-link">Stocks</Link>
          <Link to="/about" className="nav-link">About</Link>
          <Link to="/contact" className="nav-link">Contact</Link>
        </nav>

        <div className="mobile-menu-button" onClick={toggleMenu}>
          <div className={`menu-icon ${isMenuOpen ? 'active' : ''}`}>
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;