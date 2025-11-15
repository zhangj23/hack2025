import React from 'react';

const PrescriptionDisplay = ({ prescription, onRefresh }) => {
  return (
    <div className="prescription-card bg-retro-cream border-4 border-retro-brown rounded-lg p-6 shadow-inner">
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="font-bold text-lg text-retro-brown">{prescription.doctor}</p>
          <p className="text-sm text-gray-700">{prescription.facility}</p>
        </div>
        <div className="text-sm text-gray-600">
          Date: {prescription.date}
        </div>
      </div>
      
      <div className="prescription-body bg-white rounded p-4 mb-4 border-2 border-dashed border-retro-brown">
        <div className="handwritten-text font-handwriting text-3xl text-gray-800 mb-2">
          {prescription.medication}
        </div>
        <div className="handwritten-text font-handwriting text-2xl text-gray-700 mb-2">
          {prescription.dosage}
        </div>
        <div className="handwritten-text font-handwriting text-xl text-gray-600">
          {prescription.instructions}
        </div>
      </div>
      
      <div className="flex justify-between items-center">
        <p className="text-sm italic text-gray-600">Can you read this? 🤔</p>
        <button
          onClick={onRefresh}
          className="px-4 py-2 bg-retro-brown text-white rounded hover:bg-retro-brown/80 transition-colors text-sm"
        >
          🔄 New Prescription
        </button>
      </div>
    </div>
  );
};

export default PrescriptionDisplay;

