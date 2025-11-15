import React, { useState, useEffect, useRef } from "react";
import { ArbitraryStyleTransferNetwork } from "@magenta/image";
import * as tf from "@tensorflow/tfjs";
import axios from "axios";
import {
  generateClothingMask,
  loadSegmentationModel,
  generateMaskWithModel,
  applyMaskToImage,
  blendWithMask,
} from "./utils/segmentation";
import { MaskEditor } from "./components/MaskEditor";
import "./App.css";

// Mask Preview Component
function MaskPreview({ canvasRef, maskData }) {
  useEffect(() => {
    if (canvasRef.current && maskData) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      canvas.width = maskData.width;
      canvas.height = maskData.height;

      console.log("Drawing mask to preview canvas:", {
        width: maskData.width,
        height: maskData.height,
        dataLength: maskData.data.length,
      });

      ctx.putImageData(maskData, 0, 0);

      // Verify the mask was drawn correctly by checking the entire canvas
      const fullCheck = ctx.getImageData(0, 0, canvas.width, canvas.height);
      let totalWhitePixels = 0;
      for (let i = 0; i < fullCheck.data.length; i += 4) {
        if (fullCheck.data[i] > 128) totalWhitePixels++;
      }
      console.log(
        `Mask preview canvas: ${totalWhitePixels} white pixels total (should match mask data)`
      );

      // Also verify original mask data
      let originalWhiteCount = 0;
      for (let i = 0; i < maskData.data.length; i += 4) {
        if (maskData.data[i] > 128) originalWhiteCount++;
      }
      console.log(
        `Original mask data: ${originalWhiteCount} white pixels total`
      );

      if (totalWhitePixels === 0 && originalWhiteCount > 0) {
        console.error(
          "ERROR: Canvas has no white pixels but mask data does! Canvas may not be rendering correctly."
        );
      }
    }
  }, [canvasRef, maskData]);

  if (!maskData) {
    return null;
  }

  return (
    <div className="mt-4 bg-gray-700 rounded-lg p-4">
      <h3 className="text-white text-sm mb-2">Mask Preview</h3>
      <canvas
        ref={canvasRef}
        className="max-w-full rounded-lg border-2 border-modern"
        style={{ maxHeight: "200px", imageRendering: "auto" }}
      />
    </div>
  );
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

function App() {
  const [contentImage, setContentImage] = useState(null);
  const [contentImageUrl, setContentImageUrl] = useState(null);
  const [styleImage, setStyleImage] = useState(null);
  const [stylizedImage, setStylizedImage] = useState(null);
  const [maskData, setMaskData] = useState(null);
  const [styles, setStyles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [segmentationModel, setSegmentationModel] = useState(null);
  const [error, setError] = useState(null);
  const [styleStrength, setStyleStrength] = useState(0.5);
  const [useMasking, setUseMasking] = useState(true);
  const [showMaskEditor, setShowMaskEditor] = useState(false);

  const modelRef = useRef(null);
  const contentCanvasRef = useRef(null);
  const styleCanvasRef = useRef(null);
  const outputCanvasRef = useRef(null);
  const maskCanvasRef = useRef(null);

  // Load the style transfer model
  useEffect(() => {
    const loadModels = async () => {
      try {
        setLoading(true);

        // Load style transfer model
        const styleModel = new ArbitraryStyleTransferNetwork();
        await styleModel.initialize();
        modelRef.current = styleModel;
        setModelLoaded(true);

        // Try to load segmentation model
        try {
          const segModel = await loadSegmentationModel();
          setSegmentationModel(segModel);
        } catch (err) {
          console.warn("Segmentation model not available, using fallback");
        }

        setLoading(false);
      } catch (err) {
        console.error("Error loading models:", err);
        setError("Failed to load AI models. Please refresh the page.");
        setLoading(false);
      }
    };
    loadModels();
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

      // CRITICAL: Set onload handler BEFORE setting src
      // This ensures we wait for the image to fully load before processing
      img.onload = async () => {
        // Verify image is actually loaded with valid dimensions
        if (img.width === 0 || img.height === 0) {
          console.error("Image loaded but has zero dimensions! Waiting...");
          // Wait a bit and try again
          setTimeout(async () => {
            if (img.width > 0 && img.height > 0) {
              await processImage(img);
            } else {
              console.error("Image still has zero dimensions after wait");
              setError("Failed to load image properly");
            }
          }, 100);
          return;
        }

        console.log(`Image fully loaded: ${img.width}x${img.height}`);
        await processImage(img);
      };

      img.onerror = (err) => {
        console.error("Error loading image:", err);
        setError("Failed to load image");
      };

      // Set src AFTER onload handler to trigger the load
      img.src = imageUrl;

      // Helper function to process the loaded image
      async function processImage(imageElement) {
        setContentImage(imageElement);

        // Generate mask automatically
        if (useMasking) {
          console.log("Generating mask for uploaded image...");
          console.log(
            `Image dimensions: ${imageElement.width}x${imageElement.height}`
          );

          // Double-check image is ready
          if (imageElement.width === 0 || imageElement.height === 0) {
            console.error(
              "ERROR: Image has zero dimensions when generating mask!"
            );
            return;
          }

          try {
            const mask = segmentationModel
              ? await generateMaskWithModel(imageElement, segmentationModel)
              : await generateClothingMask(imageElement);

            console.log("Mask generated:", {
              mask: mask ? "exists" : "null",
              width: mask?.width,
              height: mask?.height,
            });

            if (mask) {
              // Verify mask has content
              let whitePixels = 0;
              for (let i = 0; i < mask.data.length; i += 4) {
                if (mask.data[i] > 128) whitePixels++;
              }
              console.log(`Mask has ${whitePixels} white pixels`);

              if (whitePixels === 0) {
                console.warn(
                  "WARNING: Generated mask has 0 white pixels! BodyPix may not have detected a person."
                );
              }

              setMaskData(mask);
            } else {
              console.error("Mask generation returned null");
            }
          } catch (err) {
            console.error("Error generating mask:", err);
            setError(`Failed to generate mask: ${err.message}`);
          }
        }
      }
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
        if (contentImage) {
          applyStyleTransfer(img);
        }
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

      // Perform style transfer
      console.log("Starting style transfer with strength:", styleStrength);
      const stylizedResult = await modelRef.current.stylize(
        contentCanvas,
        styleCanvas
      );

      // Create temp canvas for stylized result
      const tempCanvas = document.createElement("canvas");
      tempCanvas.width = contentCanvas.width;
      tempCanvas.height = contentCanvas.height;
      const tempCtx = tempCanvas.getContext("2d");

      // Handle ImageData result
      if (stylizedResult instanceof ImageData) {
        tempCanvas.width = stylizedResult.width;
        tempCanvas.height = stylizedResult.height;
        tempCtx.putImageData(stylizedResult, 0, 0);
      } else {
        tempCtx.drawImage(stylizedResult, 0, 0);
      }

      // Apply masking if enabled
      if (useMasking && maskData) {
        console.log("Applying mask to style transfer", {
          maskSize: `${maskData.width}x${maskData.height}`,
          contentSize: `${contentCanvas.width}x${contentCanvas.height}`,
          styleStrength,
        });

        // Resize mask to match content canvas dimensions
        const maskCanvas = document.createElement("canvas");
        maskCanvas.width = contentCanvas.width;
        maskCanvas.height = contentCanvas.height;
        const maskCtx = maskCanvas.getContext("2d");

        // Create a temporary canvas to draw the original mask
        const originalMaskCanvas = document.createElement("canvas");
        originalMaskCanvas.width = maskData.width;
        originalMaskCanvas.height = maskData.height;
        const originalMaskCtx = originalMaskCanvas.getContext("2d");
        originalMaskCtx.putImageData(maskData, 0, 0);

        // Scale the mask to match content canvas size
        maskCtx.drawImage(
          originalMaskCanvas,
          0,
          0,
          maskCanvas.width,
          maskCanvas.height
        );

        // Convert mask to grayscale alpha mask for proper compositing
        // The mask should be white (255) where we want style, black (0) elsewhere
        const maskImgData = maskCtx.getImageData(
          0,
          0,
          maskCanvas.width,
          maskCanvas.height
        );
        for (let i = 0; i < maskImgData.data.length; i += 4) {
          // Use the red channel as alpha (since mask is grayscale)
          const alpha = maskImgData.data[i] / 255;
          maskImgData.data[i] = 255; // R
          maskImgData.data[i + 1] = 255; // G
          maskImgData.data[i + 2] = 255; // B
          maskImgData.data[i + 3] = Math.round(alpha * 255); // A - use mask brightness as alpha
        }
        maskCtx.putImageData(maskImgData, 0, 0);

        // Set up output canvas
        outputCanvas.width = contentCanvas.width;
        outputCanvas.height = contentCanvas.height;
        const outputCtx = outputCanvas.getContext("2d");

        // Step 1: Draw the original content as the base
        outputCtx.drawImage(contentCanvas, 0, 0);

        // Step 2: Create masked stylized version
        const maskedStylizedCanvas = document.createElement("canvas");
        maskedStylizedCanvas.width = contentCanvas.width;
        maskedStylizedCanvas.height = contentCanvas.height;
        const maskedCtx = maskedStylizedCanvas.getContext("2d");

        // Draw the full stylized image
        maskedCtx.drawImage(tempCanvas, 0, 0);

        // Apply mask using globalCompositeOperation: only keep pixels where mask has alpha
        maskedCtx.globalCompositeOperation = "destination-in";
        maskedCtx.drawImage(maskCanvas, 0, 0);
        maskedCtx.globalCompositeOperation = "source-over";

        console.log("Masked stylized canvas created");

        // Step 3: Composite the masked stylized result onto the original
        // The maskedStylizedCanvas already has only the masked region (white areas)
        // So we can just draw it directly on top of the original

        // Verify mask has content
        const maskCheckData = maskCtx.getImageData(
          0,
          0,
          Math.min(100, maskCanvas.width),
          Math.min(100, maskCanvas.height)
        );
        let whitePixelCount = 0;
        for (let i = 0; i < maskCheckData.data.length; i += 4) {
          if (maskCheckData.data[i + 3] > 128) whitePixelCount++;
        }
        console.log(`Mask check: ${whitePixelCount} white pixels in sample`);

        // Simple approach: draw masked stylized on top of original
        // The maskedStylizedCanvas only has pixels in the white mask areas
        if (styleStrength < 1.0) {
          // For blending, we need to blend the masked areas
          // Draw original masked area first
          const originalMaskedCanvas = document.createElement("canvas");
          originalMaskedCanvas.width = contentCanvas.width;
          originalMaskedCanvas.height = contentCanvas.height;
          const originalMaskedCtx = originalMaskedCanvas.getContext("2d");
          originalMaskedCtx.drawImage(contentCanvas, 0, 0);
          originalMaskedCtx.globalCompositeOperation = "destination-in";
          originalMaskedCtx.drawImage(maskCanvas, 0, 0);
          originalMaskedCtx.globalCompositeOperation = "source-over";

          // Blend: original (masked) at (1-strength) + stylized (masked) at strength
          outputCtx.globalAlpha = 1.0 - styleStrength;
          outputCtx.drawImage(originalMaskedCanvas, 0, 0);
          outputCtx.globalAlpha = styleStrength;
          outputCtx.drawImage(maskedStylizedCanvas, 0, 0);
          outputCtx.globalAlpha = 1.0;
        } else {
          // Full strength: just draw the masked stylized version (it only has pixels in mask area)
          outputCtx.drawImage(maskedStylizedCanvas, 0, 0);
        }

        console.log("Mask applied successfully");
      } else {
        // No masking - blend with style strength
        outputCanvas.width = tempCanvas.width;
        outputCanvas.height = tempCanvas.height;
        const outputCtx = outputCanvas.getContext("2d");

        if (styleStrength < 1.0) {
          outputCtx.globalAlpha = 1.0 - styleStrength;
          outputCtx.drawImage(
            contentCanvas,
            0,
            0,
            outputCanvas.width,
            outputCanvas.height
          );
          outputCtx.globalAlpha = styleStrength;
          outputCtx.drawImage(tempCanvas, 0, 0);
          outputCtx.globalAlpha = 1.0;
        } else {
          outputCtx.drawImage(tempCanvas, 0, 0);
        }
      }

      // Create result image
      const resultImage = new Image();
      resultImage.src = outputCanvas.toDataURL();
      await new Promise((resolve, reject) => {
        resultImage.onload = resolve;
        resultImage.onerror = reject;
      });

      setStylizedImage(resultImage);
      setLoading(false);
    } catch (err) {
      console.error("Error applying style transfer:", err);
      setError(`Failed to apply style transfer: ${err.message}`);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto px-4 py-8">
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
            Loading AI models... This may take a moment.
          </div>
        )}

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

            <div className="mb-4">
              <label className="flex items-center gap-2 text-white text-sm">
                <input
                  type="checkbox"
                  checked={useMasking}
                  onChange={(e) => {
                    setUseMasking(e.target.checked);
                    if (e.target.checked && contentImage) {
                      // Regenerate mask
                      const generateMask = async () => {
                        const mask = segmentationModel
                          ? await generateMaskWithModel(
                              contentImage,
                              segmentationModel
                            )
                          : await generateClothingMask(contentImage);
                        setMaskData(mask);
                      };
                      generateMask();
                    }
                  }}
                />
                <span>Use Smart Masking (isolate clothing)</span>
              </label>
            </div>

            {maskData && useMasking && (
              <div className="mb-4">
                <button
                  onClick={() => setShowMaskEditor(!showMaskEditor)}
                  className="w-full bg-retro hover:bg-amber-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors text-sm"
                >
                  {showMaskEditor ? "Hide" : "Edit"} Mask
                </button>
              </div>
            )}

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

            {/* Mask Preview */}
            {maskData && useMasking && (
              <MaskPreview canvasRef={maskCanvasRef} maskData={maskData} />
            )}
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

        {/* Mask Editor Modal */}
        {showMaskEditor && maskData && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-semibold text-white">Edit Mask</h2>
                <button
                  onClick={() => setShowMaskEditor(false)}
                  className="text-white hover:text-gray-300 text-2xl"
                >
                  ×
                </button>
              </div>
              <MaskEditor
                maskData={maskData}
                onMaskChange={(newMask) => {
                  setMaskData(newMask);
                  // Re-apply style transfer with new mask
                  if (styleImage) {
                    applyStyleTransfer(styleImage);
                  }
                }}
                width={contentImage?.width || 512}
                height={contentImage?.height || 512}
              />
            </div>
          </div>
        )}

        <footer className="text-center text-gray-400 text-sm mt-8">
          <p>
            Transform your retro clothing into modern designs with AI-powered
            style transfer
          </p>
          <p className="mt-2">Powered by Magenta.js & TensorFlow.js</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
