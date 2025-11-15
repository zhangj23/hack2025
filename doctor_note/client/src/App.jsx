import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PrescriptionDisplay from './components/PrescriptionDisplay';
import DrawingCanvas from './components/DrawingCanvas';
import ComparisonSection from './components/ComparisonSection';
import './App.css';

function App() {
  const [prescription, setPrescription] = useState(null);
  const [recognitionResult, setRecognitionResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchRandomPrescription();
  }, []);

  const fetchRandomPrescription = async () => {
    try {
      const response = await axios.get('/api/prescriptions/random');
      setPrescription(response.data);
    } catch (error) {
      console.error('Error fetching prescription:', error);
      // Fallback prescription
      setPrescription({
        id: 1,
        doctor: "Dr. Smith",
        facility: "Medical Center",
        medication: "DICLORAN",
        dosage: "500mg",
        instructions: "Take 2x daily",
        date: new Date().toLocaleDateString()
      });
    }
  };

  const handleRecognition = (result) => {
    setRecognitionResult(result);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <header className="bg-white shadow-md py-6">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl font-bold text-gray-800 text-center">
            🩺 Retro Prescription Digitizer
          </h1>
          <p className="text-center text-gray-600 mt-2">
            Modern AI solving a retro problem: Illegible doctor's handwriting
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Retro Prescription Section */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              📋 Retro Prescription
            </h2>
            {prescription && (
              <PrescriptionDisplay 
                prescription={prescription} 
                onRefresh={fetchRandomPrescription}
              />
            )}
          </div>

          {/* Modern AI Solution Section */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              ✨ Modern AI Solution
            </h2>
            <DrawingCanvas 
              onRecognize={handleRecognition}
              loading={loading}
              setLoading={setLoading}
            />
            {recognitionResult && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-semibold text-gray-800 mb-2">AI Recognition Result:</h3>
                <p className="text-2xl font-bold text-blue-600">{recognitionResult.text}</p>
                {recognitionResult.confidence && (
                  <div className="mt-2">
                    <p className="text-sm text-gray-600">Confidence: {Math.round(recognitionResult.confidence * 100)}%</p>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${recognitionResult.confidence * 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Comparison Section */}
        <ComparisonSection />
      </main>

      <footer className="bg-gray-800 text-white text-center py-4 mt-8">
        <p className="text-sm">
          Built for Hack 2025 | Preventing prescription errors with modern AI
        </p>
      </footer>
    </div>
  );
}

export default App;

