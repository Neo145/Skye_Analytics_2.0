import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Header1.css';

const Header: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    setIsMobileMenuOpen(false);
  };

  return (
    <header className="cricket-header">
      <div className="header-container">
        {/* Logo Section */}
        <div className="header-logo" onClick={() => handleNavigation('/')}>
          <span className="logo-blue">Skye</span>
          <span className="logo-green">Analytics</span>
        </div>

        {/* Desktop Navigation */}
        <nav className="desktop-nav">
          <ul>
            <li><Link to="/cricket">Cricket</Link></li>
            <li className="coming-soon">Stock Market</li>
            <li><Link to="/about">About</Link></li>
            <li><Link to="/contact">Contact</Link></li>
          </ul>
        </nav>

        {/* User Actions */}
        <div className="header-actions">
          <button 
            className="login-button"
            onClick={() => handleNavigation('/login')}
          >
            Login
          </button>
          <button 
            className="signup-button"
            onClick={() => handleNavigation('/signup')}
          >
            Sign Up
          </button>
        </div>

        {/* Mobile Menu Toggle */}
        <div 
          className={`mobile-menu-toggle ${isMobileMenuOpen ? 'open' : ''}`}
          onClick={toggleMobileMenu}
        >
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      <div className={`mobile-nav ${isMobileMenuOpen ? 'open' : ''}`}>
        <ul>
          <li onClick={() => handleNavigation('/cricket')}>Cricket Analytics</li>
          <li className="coming-soon" onClick={() => {}}>Stock Market Analytics</li>
          <li onClick={() => handleNavigation('/about')}>About Us</li>
          <li onClick={() => handleNavigation('/contact')}>Contact</li>
          <li className="mobile-auth">
            <button onClick={() => handleNavigation('/login')}>Login</button>
            <button onClick={() => handleNavigation('/signup')}>Sign Up</button>
          </li>
        </ul>
      </div>
    </header>
  );
};

export default Header;