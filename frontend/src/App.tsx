import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './HomePage'; // Your existing HomePage
import CricketAnalytics from './CricketAnalytics'; // New Cricket page

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/cricket" element={<CricketAnalytics />} />
        {/* Add other routes as needed */}
      </Routes>
    </Router>
  );
};

export default App;