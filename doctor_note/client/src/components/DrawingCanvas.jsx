import React, { useRef, useEffect, useState } from 'react';
import { createWorker } from 'tesseract.js';

const DrawingCanvas = ({ onRecognize, loading, setLoading }) => {
  const canvasRef = useRef(null);
  const workerRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [worker, setWorker] = useState(null);
  const [modelLoading, setModelLoading] = useState(true);

  useEffect(() => {
    loadOCRWorker();
    return () => {
      // Cleanup worker on unmount
      if (workerRef.current) {
        workerRef.current.terminate();
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadOCRWorker = async () => {
    try {
      setModelLoading(true);
      console.log('Loading Tesseract.js OCR engine...');
      
      // Create Tesseract worker
      const ocrWorker = await createWorker('eng', 1, {
        logger: (m) => {
          if (m.status === 'recognizing text') {
            console.log(`OCR Progress: ${Math.round(m.progress * 100)}%`);
          }
        }
      });
      
      // Configure for better handwriting recognition
      await ocrWorker.setParameters({
        tessedit_char_whitelist: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789mgx/.,- ',
        tessedit_pageseg_mode: '6', // Assume uniform block of text
      });
      
      setWorker(ocrWorker);
      workerRef.current = ocrWorker;
      setModelLoading(false);
      console.log('Tesseract.js OCR engine loaded successfully');
    } catch (error) {
      console.error('Error loading OCR worker:', error);
      setModelLoading(false);
      alert('Failed to load OCR engine. Please refresh the page.');
    }
  };

  // HELPER: Gets coordinates for both Mouse and Touch events
  const getEventCoordinates = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();

    if (e.touches && e.touches.length > 0) {
      // Touch event
      return {
        x: e.touches[0].clientX - rect.left,
        y: e.touches[0].clientY - rect.top,
      };
    }
    // Mouse event
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  };

  const startDrawing = (e) => {
    e.preventDefault(); // Prevents screen scrolling on touch
    setIsDrawing(true);
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const { x, y } = getEventCoordinates(e); // <-- Use helper
    
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    e.preventDefault(); // Prevents screen scrolling on touch

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const { x, y } = getEventCoordinates(e); // <-- Use helper
    
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#1F2937';
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const stopDrawing = () => {
    setIsDrawing(false);
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.beginPath();
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    onRecognize(null);
  };

  const enhanceTextWithGemini = async (ocrText) => {
    const apiKey = import.meta.env.VITE_GEMINI_API_KEY;
    
    if (!apiKey) {
      console.warn('Gemini API key not found. Using raw OCR text.');
      console.warn('Make sure VITE_GEMINI_API_KEY is set in your .env file and the dev server has been restarted.');
      return ocrText;
    }
    
    // Validate API key format (should not be empty or just whitespace)
    if (!apiKey.trim()) {
      console.warn('Gemini API key appears to be empty. Using raw OCR text.');
      return ocrText;
    }
    
    console.log('Gemini API key found, length:', apiKey.length);

    // Helper function to list available models and return usable model names
    const listAvailableModels = async () => {
      try {
        const listUrl = `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`;
        const response = await fetch(listUrl);
        const data = await response.json();
        if (data.models && data.models.length > 0) {
          // Filter models that support generateContent and extract their names
          const availableModels = data.models
            .filter(m => m.supportedGenerationMethods?.includes('generateContent'))
            .map(m => {
              // Extract model name (remove 'models/' prefix if present)
              const name = m.name.replace('models/', '');
              return name;
            });
          console.log('Available Gemini models:', availableModels.join(', '));
          return availableModels;
        } else {
          console.warn('No models found in API response:', data);
        }
      } catch (e) {
        console.warn('Could not list available models:', e);
      }
      return [];
    };

    try {
      const requestBody = {
        contents: [{
          parts: [{
            text: `You are a medical transcription assistant. The following text was extracted from a handwritten medical prescription using OCR. It may contain OCR errors, misspellings, or unclear characters.

Your task:
1. Clean up the text and fix obvious OCR errors
2. Correct spelling of medical terms (e.g., "DICLORAN", "AMOXICILLIN", "500mg", "2x daily")
3. Make it human-readable while preserving all medical information
4. Keep dosages, medication names, and instructions intact
5. Return ONLY the cleaned text, no explanations or additional text

OCR Text: "${ocrText}"

Cleaned prescription text:`
          }]
        }]
      };

      // First, try to get available models from the API
      const availableModels = await listAvailableModels();
      
      // Build endpoints list - use available models if found, otherwise use defaults
      let endpoints = [];
      
      if (availableModels.length > 0) {
        // Use available models from the API
        console.log('Using available models from API:', availableModels);
        for (const modelName of availableModels) {
          // Try both v1beta and v1 APIs
          endpoints.push(`https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${apiKey}`);
          endpoints.push(`https://generativelanguage.googleapis.com/v1/models/${modelName}:generateContent?key=${apiKey}`);
        }
      } else {
        // Fallback to default models if listing failed
        console.log('Using default model list (model listing may have failed)');
        endpoints = [
          // Try gemini-pro first (most widely available, works with most API keys)
          `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${apiKey}`,
          // Try v1 API with gemini-pro
          `https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=${apiKey}`,
          // Try gemini-1.5-flash (newer, faster, but may require updated API key)
          `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`,
          `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${apiKey}`,
          // Try v1 API with flash
          `https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=${apiKey}`,
          `https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key=${apiKey}`,
        ];
      }

      let lastError = null;
      
      for (const url of endpoints) {
        try {
          console.log('Calling Gemini API at:', url.split('?')[0]);
          const response = await fetch(url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
          });

          // Try to parse JSON, but handle errors gracefully
          let responseData;
          const responseText = await response.text();
          
          try {
            responseData = JSON.parse(responseText);
          } catch (parseError) {
            console.error('Failed to parse JSON response:', responseText);
            lastError = new Error(`Invalid JSON response from Gemini API: ${response.status} ${response.statusText}`);
            continue;
          }

          if (!response.ok) {
            // Log detailed error information
            console.error('Gemini API error response:', {
              status: response.status,
              statusText: response.statusText,
              error: responseData,
              rawResponse: responseText.substring(0, 500), // First 500 chars
              url: url.split('?')[0]
            });
            
            const errorMessage = responseData?.error?.message || 
                                 responseData?.message || 
                                 responseData?.error?.details?.[0]?.message ||
                                 response.statusText || 
                                 'Unknown error';
            lastError = new Error(`Gemini API error (${response.status}): ${errorMessage}`);
            continue; // Try next endpoint
          }

          // Parse response
          if (responseData.candidates && responseData.candidates[0] && responseData.candidates[0].content) {
            const enhancedText = responseData.candidates[0].content.parts[0].text.trim();
            console.log('Gemini enhancement successful');
            return enhancedText || ocrText; // Fallback to OCR text if Gemini returns empty
          }
          
          console.warn('Unexpected Gemini API response format:', responseData);
          lastError = new Error('Unexpected response format from Gemini API');
        } catch (fetchError) {
          console.error('Fetch error for endpoint:', url.split('?')[0], fetchError);
          console.error('Error details:', {
            message: fetchError.message,
            stack: fetchError.stack,
            name: fetchError.name
          });
          lastError = fetchError;
          continue; // Try next endpoint
        }
      }
      
      // If all endpoints failed, throw the last error
      if (lastError) {
        console.error('All model endpoints failed. Available models were already checked.');
        throw lastError;
      }
      
      return ocrText; // Fallback to original OCR text
    } catch (error) {
      console.error('Gemini API error (all endpoints failed):', error);
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        name: error.name,
        cause: error.cause
      });
      
      // Show user-friendly error message based on error type
      if (error.message && error.message.includes('401')) {
        console.error('❌ Authentication error: Check if your API key is valid and has proper permissions.');
      } else if (error.message && error.message.includes('403')) {
        console.error('❌ Forbidden: Your API key may not have access to this model or endpoint.');
      } else if (error.message && error.message.includes('400')) {
        console.error('❌ Bad request: Check the request format and parameters.');
      } else if (error.message && error.message.includes('429')) {
        console.error('❌ Rate limit exceeded: Too many requests. Please wait and try again.');
      } else {
        console.error('❌ Unknown error. Check console for details.');
      }
      
      // Return original OCR text if Gemini fails
      return ocrText;
    }
  };

  const preprocessCanvas = (canvas) => {
    // Create a processed canvas with better contrast for OCR
    const processedCanvas = document.createElement('canvas');
    const ctx = processedCanvas.getContext('2d');
    
    // Scale up for better recognition (OCR works better with higher resolution)
    const scale = 2;
    processedCanvas.width = canvas.width * scale;
    processedCanvas.height = canvas.height * scale;
    
    // Fill with white background
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, processedCanvas.width, processedCanvas.height);
    
    // Draw original canvas scaled up
    ctx.drawImage(canvas, 0, 0, processedCanvas.width, processedCanvas.height);
    
    // Apply image processing for better OCR
    const imageData = ctx.getImageData(0, 0, processedCanvas.width, processedCanvas.height);
    const data = imageData.data;
    
    // Enhance contrast - make dark pixels darker and light pixels lighter
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      
      // Convert to grayscale
      const gray = 0.299 * r + 0.587 * g + 0.114 * b;
      
      // Enhance contrast
      let contrast = gray;
      if (gray < 200) {
        // If it's not white (drawing), make it darker
        contrast = Math.max(0, gray - 40);
      } else {
        // Keep white background
        contrast = 255;
      }
      
      data[i] = contrast;     // R
      data[i + 1] = contrast; // G
      data[i + 2] = contrast; // B
      // Keep alpha channel
    }
    
    ctx.putImageData(imageData, 0, 0);
    
    return processedCanvas;
  };

  const recognizeHandwriting = async () => {
    if (!worker || modelLoading) {
      alert('OCR engine is still loading. Please wait...');
      return;
    }

    setLoading(true);
    const canvas = canvasRef.current;
    
    try {
      // Check if there's any drawing on the canvas
      const ctx = canvas.getContext('2d');
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const pixels = imageData.data;
      let hasDrawing = false;
      
      for (let i = 0; i < pixels.length; i += 4) {
        const r = pixels[i];
        const g = pixels[i + 1];
        const b = pixels[i + 2];
        // Check if pixel is not white
        if (r < 250 || g < 250 || b < 250) {
          hasDrawing = true;
          break;
        }
      }
      
      if (!hasDrawing) {
        onRecognize({
          text: 'No text detected. Please draw or upload an image.',
          confidence: 0
        });
        setLoading(false);
        return;
      }
      
      // Preprocess canvas for better OCR results
      const processedCanvas = preprocessCanvas(canvas);
      
      // Perform OCR recognition
      const { data: { text, confidence } } = await worker.recognize(processedCanvas);
      
      // Clean up processed canvas
      processedCanvas.remove();
      
      // Clean and format the recognized text
      let cleanedText = text.trim().replace(/\s+/g, ' ');
      const originalOcrText = cleanedText;
      
      // Enhance text with Gemini API if available
      if (cleanedText && cleanedText !== 'No text recognized' && import.meta.env.VITE_GEMINI_API_KEY) {
        try {
          console.log('Enhancing OCR text with Gemini API...');
          const enhancedText = await enhanceTextWithGemini(cleanedText);
          cleanedText = enhancedText;
          if (cleanedText !== originalOcrText) {
            console.log('Text enhanced:', { original: originalOcrText, enhanced: cleanedText });
          }
        } catch (error) {
          console.error('Error enhancing text with Gemini:', error);
          // Continue with OCR text if Gemini fails
        }
      }
      
      onRecognize({
        text: cleanedText || 'No text recognized',
        confidence: confidence ? Math.min(1, confidence / 100) : 0.5
      });
    } catch (error) {
      console.error('Recognition error:', error);
      alert('Error recognizing handwriting. Please try again. Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Scale image to fit canvas
        const scale = Math.min(canvas.width / img.width, canvas.height / img.height);
        const x = (canvas.width - img.width * scale) / 2;
        const y = (canvas.height - img.height * scale) / 2;
        
        ctx.drawImage(img, x, y, img.width * scale, img.height * scale);
      };
      img.src = event.target.result;
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="space-y-4">
      <div className="border-2 border-gray-300 rounded-lg p-2 bg-white">
        <canvas
          ref={canvasRef}
          width={600}
          height={300}
          className="w-full border border-gray-200 rounded cursor-crosshair"
          // Mouse Events
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          // Touch Events
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
        />
      </div>
      
      <div className="flex flex-wrap gap-2">
        <button
          onClick={clearCanvas}
          disabled={loading || modelLoading}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Clear
        </button>
        <button
          onClick={recognizeHandwriting}
          disabled={loading || modelLoading}
          className="px-4 py-2 bg-modern-blue text-white rounded hover:bg-modern-blue/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold"
        >
          {loading ? 'Recognizing...' : modelLoading ? 'Loading Model...' : '🤖 Recognize'}
        </button>
        <label className="px-4 py-2 bg-modern-teal text-white rounded hover:bg-modern-teal/80 cursor-pointer transition-colors font-semibold">
          📤 Upload Image
          <input
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />
        </label>
      </div>
      
      <div className="text-sm text-gray-600">
        {modelLoading ? (
          <div className="space-y-2">
            <p>Loading OCR engine...</p>
            <p className="text-xs text-gray-500">This may take a moment on first load.</p>
          </div>
        ) : (
          <p>Draw a prescription or upload an image to see AI recognition</p>
        )}
      </div>
    </div>
  );
};

export default DrawingCanvas;