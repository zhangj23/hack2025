import React, { useState, useEffect, useRef } from "react";
import { ArbitraryStyleTransferNetwork } from "@magenta/image";
import * as tf from "@tensorflow/tfjs";
import axios from "axios";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

function App() {
  const [contentImage, setContentImage] = useState(null);
  const [contentImageUrl, setContentImageUrl] = useState(null);
  const [styleImage, setStyleImage] = useState(null);
  const [stylizedImage, setStylizedImage] = useState(null);
  const [styles, setStyles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [error, setError] = useState(null);
  const [styleStrength, setStyleStrength] = useState(0.5); // Default to 0.5 for balanced style

  const modelRef = useRef(null);
  const contentCanvasRef = useRef(null);
  const styleCanvasRef = useRef(null);
  const outputCanvasRef = useRef(null);

  // Load the style transfer model
  useEffect(() => {
    const loadModel = async () => {
      try {
        setLoading(true);
        const model = new ArbitraryStyleTransferNetwork();
        await model.initialize();
        modelRef.current = model;
        setModelLoaded(true);
        setLoading(false);
      } catch (err) {
        console.error("Error loading model:", err);
        setError("Failed to load AI model. Please refresh the page.");
        setLoading(false);
      }
    };
    loadModel();
  }, []);

  // Load style gallery
  useEffect(() => {
    const fetchStyles = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/styles`);
        setStyles(response.data);
      } catch (err) {
        console.error("Error loading styles:", err);
      }
    };
    fetchStyles();
  }, []);

  const handleContentUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("content", file);

    try {
      const response = await axios.post(
        `${API_URL}/api/upload-content`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      const imageUrl = `${API_URL}${response.data.url}`;
      setContentImageUrl(imageUrl);

      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        setContentImage(img);
        drawImageToCanvas(img, contentCanvasRef.current);
      };
      img.src = imageUrl;
    } catch (err) {
      console.error("Error uploading content:", err);
      setError("Failed to upload content image");
    }
  };

  const handleStyleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("style", file);

    try {
      const response = await axios.post(
        `${API_URL}/api/upload-style`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        setStyleImage(img);
        applyStyleTransfer(img);
      };
      img.src = `${API_URL}${response.data.url}`;
    } catch (err) {
      console.error("Error uploading style:", err);
      setError("Failed to upload style image");
    }
  };

  const handleStyleSelect = async (styleUrl) => {
    if (!contentImage) {
      setError("Please upload a content image first");
      return;
    }

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      setStyleImage(img);
      applyStyleTransfer(img);
    };
    img.src = `${API_URL}${styleUrl}`;
  };

  const drawImageToCanvas = (img, canvas) => {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    canvas.width = img.width;
    canvas.height = img.height;
    ctx.drawImage(img, 0, 0);
  };

  const applyStyleTransfer = async (styleImg) => {
    if (!contentImage || !modelRef.current || !modelLoaded) {
      setError("Model not loaded or content image missing");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const outputCanvas = outputCanvasRef.current;
      if (!outputCanvas) return;

      // Resize images if needed (model works best with certain sizes)
      const maxSize = 512;
      const contentCanvas = document.createElement("canvas");
      const styleCanvas = document.createElement("canvas");

      const contentCtx = contentCanvas.getContext("2d");
      const styleCtx = styleCanvas.getContext("2d");

      // Resize content image
      const contentScale = Math.min(
        maxSize / contentImage.width,
        maxSize / contentImage.height,
        1
      );
      contentCanvas.width = contentImage.width * contentScale;
      contentCanvas.height = contentImage.height * contentScale;
      contentCtx.drawImage(
        contentImage,
        0,
        0,
        contentCanvas.width,
        contentCanvas.height
      );

      // Resize style image
      const styleScale = Math.min(
        maxSize / styleImg.width,
        maxSize / styleImg.height,
        1
      );
      styleCanvas.width = styleImg.width * styleScale;
      styleCanvas.height = styleImg.height * styleScale;
      styleCtx.drawImage(styleImg, 0, 0, styleCanvas.width, styleCanvas.height);

      // Set up output canvas (draw directly to the ref canvas)
      if (!outputCanvas) {
        throw new Error("Output canvas not available");
      }

      outputCanvas.width = contentCanvas.width;
      outputCanvas.height = contentCanvas.height;
      const outputCtx = outputCanvas.getContext("2d");

      // Perform style transfer
      console.log("Starting style transfer with strength:", styleStrength);
      const stylizedResult = await modelRef.current.stylize(
        contentCanvas,
        styleCanvas
      );

      console.log(
        "Style transfer complete, result type:",
        typeof stylizedResult,
        stylizedResult
      );

      // Create a temporary canvas for the stylized result
      const tempCanvas = document.createElement("canvas");
      tempCanvas.width = outputCanvas.width;
      tempCanvas.height = outputCanvas.height;
      const tempCtx = tempCanvas.getContext("2d");

      // Handle different return types and draw to temp canvas first
      // Check if it's ImageData first (most common for Magenta.js)
      if (stylizedResult instanceof ImageData) {
        console.log("Result is ImageData, putting on temp canvas");
        tempCanvas.width = stylizedResult.width;
        tempCanvas.height = stylizedResult.height;
        tempCtx.putImageData(stylizedResult, 0, 0);
        console.log("ImageData drawn to temp canvas successfully");
      }
      // Check if it's a tensor (TensorFlow.js 0.14.2)
      else if (
        stylizedResult &&
        (stylizedResult.constructor === tf.Tensor ||
          stylizedResult.constructor.name === "Tensor" ||
          (stylizedResult.shape && Array.isArray(stylizedResult.shape)))
      ) {
        // It's a tensor - convert to image data
        console.log("Result is a tensor, shape:", stylizedResult.shape);
        const shape = stylizedResult.shape;
        const height = shape[0];
        const width = shape[1];

        console.log("Converting tensor to pixels...");
        const imageData = await tf.toPixels(stylizedResult);
        console.log("Got image data, length:", imageData.length);

        // Create ImageData and put it on temp canvas
        const imgData = new ImageData(
          new Uint8ClampedArray(imageData),
          width,
          height
        );
        tempCanvas.width = width;
        tempCanvas.height = height;
        tempCtx.putImageData(imgData, 0, 0);
        console.log("Image data drawn to temp canvas");

        // Clean up tensor
        stylizedResult.dispose();
      } else if (
        stylizedResult instanceof HTMLImageElement ||
        stylizedResult instanceof HTMLCanvasElement
      ) {
        // It's already an image or canvas
        console.log("Result is an image/canvas, drawing to temp canvas...");
        tempCtx.drawImage(stylizedResult, 0, 0);
      } else {
        // Try to draw it anyway (might be ImageData or other drawable)
        console.log("Unknown result type, attempting to draw...");
        console.log("Result:", stylizedResult);
        console.log("Result type:", typeof stylizedResult);
        console.log("Result constructor:", stylizedResult?.constructor);

        try {
          outputCtx.drawImage(stylizedResult, 0, 0);
        } catch (e) {
          console.error(
            "Direct draw failed, checking for ImageData-like object...",
            e
          );
          // Fallback: try to treat as ImageData (has data, width, height properties)
          if (
            stylizedResult &&
            stylizedResult.data &&
            stylizedResult.width &&
            stylizedResult.height
          ) {
            console.log("Treating as ImageData-like object");
            tempCanvas.width = stylizedResult.width;
            tempCanvas.height = stylizedResult.height;
            tempCtx.putImageData(stylizedResult, 0, 0);
          }
          // Try tensor conversion
          else if (stylizedResult && stylizedResult.shape) {
            console.log("Treating as tensor");
            const [height, width] = stylizedResult.shape.slice(0, 2);
            const imageData = await tf.toPixels(stylizedResult);
            const imgData = new ImageData(
              new Uint8ClampedArray(imageData),
              width,
              height
            );
            tempCanvas.width = width;
            tempCanvas.height = height;
            tempCtx.putImageData(imgData, 0, 0);
            stylizedResult.dispose();
          } else {
            throw new Error(
              "Unable to draw stylized result. Type: " +
                typeof stylizedResult +
                ", Constructor: " +
                (stylizedResult?.constructor?.name || "unknown")
            );
          }
        }
      }

      // Update output canvas dimensions to match temp canvas
      outputCanvas.width = tempCanvas.width;
      outputCanvas.height = tempCanvas.height;

      // Apply style strength by blending with original content
      // Lower strength = more original content preserved
      if (styleStrength < 1.0) {
        console.log(
          "Blending result with original content, strength:",
          styleStrength
        );

        // Draw original content first with reduced opacity
        outputCtx.globalAlpha = 1.0 - styleStrength; // More original when strength is low
        outputCtx.drawImage(
          contentCanvas,
          0,
          0,
          outputCanvas.width,
          outputCanvas.height
        );

        // Then draw stylized result on top with style strength opacity
        outputCtx.globalAlpha = styleStrength; // More style when strength is high
        outputCtx.drawImage(tempCanvas, 0, 0);

        outputCtx.globalAlpha = 1.0; // Reset
        console.log("Blending complete");
      } else {
        // Full strength - use stylized result directly
        outputCtx.drawImage(tempCanvas, 0, 0);
        console.log("Full strength style applied");
      }

      // Verify canvas has content
      const canvasData = outputCanvas.toDataURL();
      if (!canvasData || canvasData === "data:,") {
        throw new Error("Canvas is empty after style transfer");
      }

      console.log(
        "Canvas has content, dimensions:",
        outputCanvas.width,
        "x",
        outputCanvas.height
      );

      // Make canvas visible immediately
      if (outputCanvasRef.current) {
        outputCanvasRef.current.style.display = "block";
      }

      // Force React to re-render by setting a marker
      setStylizedImage(true); // Use true as a marker that we have content

      // Create an image from the canvas for download functionality
      const resultImage = new Image();
      resultImage.crossOrigin = "anonymous";
      resultImage.src = canvasData;

      await new Promise((resolve, reject) => {
        resultImage.onload = () => {
          console.log("Result image loaded successfully");
          resolve();
        };
        resultImage.onerror = (e) => {
          console.error("Failed to load result image:", e);
          reject(new Error("Failed to create result image"));
        };
        // Timeout after 5 seconds
        setTimeout(() => {
          reject(new Error("Image load timeout"));
        }, 5000);
      });

      console.log("Style transfer complete, image ready");
      setStylizedImage(resultImage); // Now set the actual image for download
      setLoading(false);
    } catch (err) {
      console.error("Error applying style transfer:", err);
      console.error("Error stack:", err.stack);
      setError(
        `Failed to apply style transfer: ${err.message}. Check console for details.`
      );
      setLoading(false);
      setStylizedImage(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-5xl font-bold text-white mb-2">
            <span className="text-retro">Retro</span> →{" "}
            <span className="text-modern">Modern</span>
          </h1>
          <p className="text-xl text-gray-300 mb-1">The AI Upcycler</p>
          <p className="text-sm text-gray-400">
            Your Personal Stylist - Transform vintage clothing with AI
          </p>
        </header>

        {error && (
          <div className="bg-red-500 text-white p-4 rounded-lg mb-4 text-center">
            {error}
          </div>
        )}

        {loading && !modelLoaded && (
          <div className="bg-blue-500 text-white p-4 rounded-lg mb-4 text-center">
            Loading AI model... This may take a moment.
          </div>
        )}

        {/* Three Panel Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Left Panel - Content Upload */}
          <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
            <h2 className="text-2xl font-semibold text-white mb-4 text-center">
              Upload Content
            </h2>
            <div className="mb-4">
              <label className="block w-full">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleContentUpload}
                  className="hidden"
                  id="content-upload"
                />
                <div className="cursor-pointer bg-modern hover:bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg text-center transition-colors">
                  Choose Clothing Photo
                </div>
              </label>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 min-h-[300px] flex items-center justify-center">
              {contentImageUrl ? (
                <img
                  src={contentImageUrl}
                  alt="Uploaded clothing"
                  className="max-w-full max-h-[400px] rounded-lg object-contain"
                />
              ) : (
                <p className="text-gray-400 text-center">
                  Upload a photo of your clothing item
                </p>
              )}
            </div>
          </div>

          {/* Middle Panel - Style Gallery */}
          <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
            <h2 className="text-2xl font-semibold text-white mb-4 text-center">
              Style Gallery
            </h2>
            <div className="mb-4">
              <label className="block w-full">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleStyleUpload}
                  className="hidden"
                  id="style-upload"
                />
                <div className="cursor-pointer bg-retro hover:bg-amber-600 text-white font-semibold py-3 px-6 rounded-lg text-center transition-colors">
                  Upload Custom Style
                </div>
              </label>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 max-h-[500px] overflow-y-auto">
              <div className="grid grid-cols-2 gap-3">
                {styles.map((style, index) => (
                  <div
                    key={index}
                    onClick={() => handleStyleSelect(style.url)}
                    className="cursor-pointer group relative overflow-hidden rounded-lg aspect-square bg-gray-600 hover:ring-2 hover:ring-modern transition-all"
                  >
                    <img
                      src={`${API_URL}${style.url}`}
                      alt={style.name}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                      onError={(e) => {
                        e.target.style.display = "none";
                      }}
                    />
                    <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white text-xs p-1 text-center">
                      {style.name}
                    </div>
                  </div>
                ))}
              </div>
              {styles.length === 0 && (
                <p className="text-gray-400 text-center py-8">
                  No styles available. Add style images to server/public/styles/
                </p>
              )}
            </div>
          </div>

          {/* Right Panel - Output */}
          <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
            <h2 className="text-2xl font-semibold text-white mb-4 text-center">
              Stylized Output
            </h2>
            {/* Style Strength Control */}
            <div className="mb-4">
              <label className="block text-white text-sm mb-2">
                Style Strength: {Math.round(styleStrength * 100)}%
              </label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={styleStrength}
                onChange={(e) => {
                  const newStrength = parseFloat(e.target.value);
                  setStyleStrength(newStrength);
                  // Re-apply style transfer if we have both images
                  if (contentImage && styleImage) {
                    applyStyleTransfer(styleImage);
                  }
                }}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-modern"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>Subtle (10%)</span>
                <span>Balanced (50%)</span>
                <span>Strong (100%)</span>
              </div>
            </div>
            {loading && modelLoaded && (
              <div className="bg-blue-500 text-white p-3 rounded-lg mb-4 text-center text-sm">
                Applying style transfer...
              </div>
            )}
            <div className="bg-gray-700 rounded-lg p-4 min-h-[300px] flex items-center justify-center relative">
              <canvas
                ref={outputCanvasRef}
                className="max-w-full max-h-[400px] rounded-lg"
                style={{ display: stylizedImage ? "block" : "none" }}
              />
              {!stylizedImage && (
                <p className="text-gray-400 text-center absolute">
                  {contentImage && styleImage && loading
                    ? "Processing..."
                    : contentImage && styleImage
                    ? "Processing..."
                    : "Upload content and select a style to see the transformation"}
                </p>
              )}
            </div>
            {stylizedImage && outputCanvasRef.current && (
              <div className="mt-4 text-center">
                <a
                  href={outputCanvasRef.current.toDataURL()}
                  download="stylized-clothing.png"
                  className="inline-block bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors"
                >
                  Download Result
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="text-center text-gray-400 text-sm mt-8">
          <p>
            Transform your retro clothing into modern designs with AI-powered
            style transfer
          </p>
          <p className="mt-2">Powered by Magenta.js Arbitrary Style Transfer</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
