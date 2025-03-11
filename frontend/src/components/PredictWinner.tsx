import React, { useState } from 'react';

const PredictWinner: React.FC = () => {
  const [teamA, setTeamA] = useState('');
  const [teamB, setTeamB] = useState('');
  const [prediction, setPrediction] = useState<string | null>(null);

  const handlePredict = () => {
    // Placeholder prediction logic
    if (teamA && teamB) {
      setPrediction(`Predicted Winner: ${Math.random() > 0.5 ? teamA : teamB}`);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6 text-blue-700">Match Winner Prediction</h1>
      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="mb-4">
          <label className="block text-gray-700 mb-2">Team A</label>
          <input 
            type="text" 
            value={teamA}
            onChange={(e) => setTeamA(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="Enter Team A"
          />
        </div>
        <div className="mb-4">
          <label className="block text-gray-700 mb-2">Team B</label>
          <input 
            type="text" 
            value={teamB}
            onChange={(e) => setTeamB(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="Enter Team B"
          />
        </div>
        <button 
          onClick={handlePredict}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Predict Winner
        </button>
        {prediction && (
          <div className="mt-4 p-4 bg-blue-100 rounded">
            <p className="font-bold text-blue-800">{prediction}</p>
            <p className="text-sm text-gray-600">
              Note: This is a placeholder prediction and not a real machine learning model.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PredictWinner;