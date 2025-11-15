import React from 'react';

const ComparisonSection = () => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mt-8">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">
        🔄 Retro vs Modern
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Retro Problem */}
        <div className="bg-red-50 border-4 border-red-300 rounded-lg p-6">
          <h3 className="text-2xl font-bold text-red-700 mb-4 flex items-center">
            ❌ Retro Problem
          </h3>
          <ul className="space-y-3">
            <li className="flex items-start">
              <span className="text-red-600 mr-2">•</span>
              <span className="text-gray-700">Illegible handwriting causing confusion</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-600 mr-2">•</span>
              <span className="text-gray-700">Manual data entry errors</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-600 mr-2">•</span>
              <span className="text-gray-700">Patient safety risks from misread prescriptions</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-600 mr-2">•</span>
              <span className="text-gray-700">Time-consuming verification processes</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-600 mr-2">•</span>
              <span className="text-gray-700">Costly medication errors</span>
            </li>
          </ul>
        </div>

        {/* Modern Solution */}
        <div className="bg-green-50 border-4 border-green-300 rounded-lg p-6">
          <h3 className="text-2xl font-bold text-green-700 mb-4 flex items-center">
            ✅ Modern Solution
          </h3>
          <ul className="space-y-3">
            <li className="flex items-start">
              <span className="text-green-600 mr-2">•</span>
              <span className="text-gray-700">Real-time OCR recognition with AI</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">•</span>
              <span className="text-gray-700">Automated validation and error checking</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">•</span>
              <span className="text-gray-700">Instant digitization prevents errors</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">•</span>
              <span className="text-gray-700">Browser-based, no installation needed</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">•</span>
              <span className="text-gray-700">Cost-effective error prevention</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded-lg border-2 border-blue-200">
        <p className="text-center text-gray-700">
          <strong className="text-blue-700">The Impact:</strong> This tool provides a tangible solution to a universal problem 
          that affects patient safety and healthcare costs worldwide. By digitizing prescriptions before they're filled, 
          we prevent costly and dangerous medication errors.
        </p>
      </div>
    </div>
  );
};

export default ComparisonSection;

