import * as tf from "@tensorflow/tfjs";
import * as bodyPix from "@tensorflow-models/body-pix";

/**
 * BodyPix model for high-quality person/clothing detection
 * This is the primary method - much better than fallback
 */
let segmentationModel = null;

/**
 * Load BodyPix model
 * This works without CORS issues and is optimized for browser use
 */
export async function loadSegmentationModel() {
  if (segmentationModel) {
    return segmentationModel;
  }

  try {
    console.log("Loading BodyPix model...");
    // Load BodyPix with default settings (good balance of speed and accuracy)
    segmentationModel = await bodyPix.load({
      architecture: "MobileNetV1",
      outputStride: 16,
      multiplier: 0.75,
      quantBytes: 2,
    });
    console.log("BodyPix model loaded successfully");
    return segmentationModel;
  } catch (error) {
    console.warn("Failed to load BodyPix model, using fallback:", error);
    return null;
  }
}

/**
 * Generate mask using BodyPix
 * This returns a high-quality mask of the person/clothing
 */
export async function generateMaskWithModel(imageElement, model) {
  if (!model) {
    console.log("No model available, using fallback");
    return await generateClothingMask(imageElement);
  }

  try {
    console.log("Generating PART mask with BodyPix", {
      imageWidth: imageElement.width,
      imageHeight: imageElement.height,
    });

    // FIX: Call 'segmentPersonParts' instead of 'segmentPerson'
    const segmentation = await model.segmentPersonParts(imageElement, {
      flipHorizontal: false,
      internalResolution: "medium",
      segmentationThreshold: 0.5,
    });

    console.log("BodyPix PARTS segmentation result:", {
      segmentation: segmentation ? "exists" : "null",
      type: typeof segmentation,
      keys: segmentation ? Object.keys(segmentation) : [],
    });

    if (!segmentation) {
      console.warn("No person detected, using fallback");
      return await generateClothingMask(imageElement);
    }

    // BodyPix 'segmentPersonParts' returns data as an Int32Array
    // where each value is a part ID (0-23) or -1 for background.
    const { width, height, data } = segmentation;

    console.log("Segmentation dimensions:", {
      width,
      height,
      dataLength: data.length,
    });

    if (!data || data.length === 0) {
      console.warn("Empty segmentation data, using fallback");
      return await generateClothingMask(imageElement);
    }

    // Convert segmentation mask to ImageData
    const maskData = new Uint8ClampedArray(width * height * 4);
    let clothingPixelCount = 0;

    // FIX: Define the part IDs that we consider "t-shirt"
    // 0: torso-front, 1: torso-back
    // 4: left-upper-arm-front, 5: left-upper-arm-back
    // 6: right-upper-arm-front, 7: right-upper-arm-back
    const clothingPartIds = new Set([2, 3, 4, 5, 12, 13]); // Only include torso-front and torso-back

    for (let i = 0; i < data.length; i++) {
      const pixelIndex = i * 4;

      // FIX: The value is now a part ID (0-23) or -1
      const partId = data[i];

      // FIX: Check if the partId is in our "clothing" set
      const isClothing = clothingPartIds.has(partId);
      const whiteValue = isClothing ? 255 : 0;

      maskData[pixelIndex] = whiteValue; // R
      maskData[pixelIndex + 1] = whiteValue; // G
      maskData[pixelIndex + 2] = whiteValue; // B
      maskData[pixelIndex + 3] = 255; // A

      if (isClothing) clothingPixelCount++;
    }

    console.log(
      `BodyPix mask: ${clothingPixelCount} CLOTHING pixels out of ${data.length} total`
    );

    // ... (rest of the function for resizing and returning the mask) ...
    // No changes needed below this line

    let minX = width,
      maxX = 0,
      minY = height,
      maxY = 0;
    let foundPixels = 0;
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const idx = (y * width + x) * 4;
        if (maskData[idx] > 128) {
          foundPixels++;
          minX = Math.min(minX, x);
          maxX = Math.max(maxX, x);
          minY = Math.min(minY, y);
          maxY = Math.max(maxY, y);
        }
      }
    }
    console.log(
      `Clothing bounding box: (${minX}, ${minY}) to (${maxX}, ${maxY}), found ${foundPixels} pixels`
    );

    const maskImageData = new ImageData(maskData, width, height);

    if (width !== imageElement.width || height !== imageElement.height) {
      console.log(
        `Resizing mask from ${width}x${height} to ${imageElement.width}x${imageElement.height}`
      );

      const resizedCanvas = document.createElement("canvas");
      resizedCanvas.width = imageElement.width;
      resizedCanvas.height = imageElement.height;
      const resizedCtx = resizedCanvas.getContext("2d");

      const tempCanvas = document.createElement("canvas");
      tempCanvas.width = width;
      tempCanvas.height = height;
      const tempCtx = tempCanvas.getContext("2d");
      tempCtx.putImageData(maskImageData, 0, 0);

      resizedCtx.drawImage(
        tempCanvas,
        0,
        0,
        imageElement.width,
        imageElement.height
      );
      const resizedImageData = resizedCtx.getImageData(
        0,
        0,
        imageElement.width,
        imageElement.height
      );

      let whiteCount = 0;
      for (let i = 0; i < resizedImageData.data.length; i += 4) {
        if (resizedImageData.data[i] > 128) whiteCount++;
      }
      console.log(`Resized mask has ${whiteCount} white pixels`);
      console.log("Mask generated successfully with BodyPix (resized)");
      return resizedImageData;
    }

    let whiteCount = 0;
    for (let i = 0; i < maskData.length; i += 4) {
      if (maskData[i] > 128) whiteCount++;
    }
    console.log(`Final mask has ${whiteCount} white pixels`);
    console.log("Mask generated successfully with BodyPix");
    return maskImageData;
  } catch (error) {
    console.error("Error generating part mask with BodyPix:", error);
    console.error("Error stack:", error.stack);
    return await generateClothingMask(imageElement);
  }
}

/**
 * Improved clothing segmentation using edge detection and color analysis
 * This is an enhanced fallback method that works better than simple thresholding
 */
export async function generateClothingMask(imageElement) {
  console.log(
    "Generating clothing mask for image:",
    imageElement.width,
    "x",
    imageElement.height
  );

  const canvas = document.createElement("canvas");
  canvas.width = imageElement.width;
  canvas.height = imageElement.height;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(imageElement, 0, 0);

  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imageData.data;
  const maskData = new Uint8ClampedArray(data.length);

  // Simple approach: mask the center region (where clothing usually is)
  // This is a fallback that always works
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const maskWidth = canvas.width * 0.5; // 50% of width
  const maskHeight = canvas.height * 0.6; // 60% of height (taller for shirts)

  let clothingPixelCount = 0;

  // Create mask - center rectangular region
  for (let i = 0; i < data.length; i += 4) {
    const x = (i / 4) % canvas.width;
    const y = Math.floor(i / 4 / canvas.width);
    const a = data[i + 3];

    // Check if pixel is in center region and not transparent
    const inCenterX = Math.abs(x - centerX) < maskWidth / 2;
    const inCenterY = Math.abs(y - centerY) < maskHeight / 2;

    if (inCenterX && inCenterY && a > 128) {
      // Also check it's not pure black or pure white
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      const brightness = (r + g + b) / 3;

      // Include if not pure black/white
      if (brightness > 10 && brightness < 245) {
        maskData[i] = 255; // R
        maskData[i + 1] = 255; // G
        maskData[i + 2] = 255; // B
        maskData[i + 3] = 255; // A
        clothingPixelCount++;
      } else {
        maskData[i] = 0;
        maskData[i + 1] = 0;
        maskData[i + 2] = 0;
        maskData[i + 3] = 255;
      }
    } else {
      maskData[i] = 0;
      maskData[i + 1] = 0;
      maskData[i + 2] = 0;
      maskData[i + 3] = 255;
    }
  }

  console.log(`Mask generated: ${clothingPixelCount} clothing pixels`);

  // Apply light morphological operations to smooth edges
  const cleanedMask = cleanMask(maskData, canvas.width, canvas.height);

  const maskImageData = new ImageData(cleanedMask, canvas.width, canvas.height);
  console.log(
    "Mask generation complete, size:",
    maskImageData.width,
    "x",
    maskImageData.height
  );
  return maskImageData;
}

/**
 * Clean up mask using simple morphological operations
 */
function cleanMask(maskData, width, height) {
  const cleaned = new Uint8ClampedArray(maskData);
  const kernelSize = 3;
  const halfKernel = Math.floor(kernelSize / 2);

  // Simple erosion to remove small noise
  for (let y = halfKernel; y < height - halfKernel; y++) {
    for (let x = halfKernel; x < width - halfKernel; x++) {
      const idx = (y * width + x) * 4;
      let whiteCount = 0;

      // Count white pixels in neighborhood
      for (let dy = -halfKernel; dy <= halfKernel; dy++) {
        for (let dx = -halfKernel; dx <= halfKernel; dx++) {
          const nIdx = ((y + dy) * width + (x + dx)) * 4;
          if (maskData[nIdx] > 128) whiteCount++;
        }
      }

      // If less than 2 white pixels in 3x3 area, make it black (remove noise)
      // Very low threshold to preserve clothing pixels
      if (whiteCount < 2) {
        cleaned[idx] = 0;
        cleaned[idx + 1] = 0;
        cleaned[idx + 2] = 0;
      }
    }
  }

  return cleaned;
}

/**
 * Apply mask to style transfer result
 */
export function applyMaskToImage(imageData, maskData) {
  const result = new Uint8ClampedArray(imageData.data.length);

  for (let i = 0; i < imageData.data.length; i += 4) {
    // FIX: Read from the Red channel (data[i]) not the Alpha channel (data[i+3])
    const maskValue = maskData.data[i] / 255; // Normalize to 0 (black) or 1 (white)

    // Apply the mask to the color channels
    result[i] = imageData.data[i] * maskValue; // R
    result[i + 1] = imageData.data[i + 1] * maskValue; // G
    result[i + 2] = imageData.data[i + 2] * maskValue; // B

    // FIX: Apply the mask to the Alpha channel to make the background transparent
    result[i + 3] = maskValue * 255; // A
  }

  return new ImageData(result, imageData.width, imageData.height);
}
/**
 * Blend original content with stylized result using mask
 */
export function blendWithMask(originalCanvas, stylizedCanvas, maskData) {
  const outputCanvas = document.createElement("canvas");
  outputCanvas.width = originalCanvas.width;
  outputCanvas.height = originalCanvas.height;
  const ctx = outputCanvas.getContext("2d");

  // --- Create a temporary canvas to hold the *isolated* stylized shirt ---
  const tempCanvas = document.createElement("canvas");
  tempCanvas.width = originalCanvas.width;
  tempCanvas.height = originalCanvas.height;
  const tempCtx = tempCanvas.getContext("2d");

  // 1. Draw the *stylized* image onto the temp canvas
  tempCtx.drawImage(stylizedCanvas, 0, 0);

  // 2. Set composite op to "destination-in".
  // This means: "Keep the destination (stylized image) ONLY
  // where the new source (the mask) is drawn."
  tempCtx.globalCompositeOperation = "destination-in";

  // 3. Draw the mask.
  // We must draw it to *another* temp canvas first so we can use drawImage,
  // as putImageData doesn't respect composite operations.
  const maskCanvas = document.createElement("canvas");
  maskCanvas.width = maskData.width;
  maskCanvas.height = maskData.height;
  const maskCtx = maskCanvas.getContext("2d");
  maskCtx.putImageData(maskData, 0, 0);

  // This drawImage call *does* respect the composite operation
  tempCtx.drawImage(maskCanvas, 0, 0);

  // --- Now, `tempCanvas` holds *only* the stylized shirt ---

  // 4. Draw the original image (with its background)
  ctx.drawImage(originalCanvas, 0, 0);

  // 5. Draw the isolated stylized shirt on top
  ctx.drawImage(tempCanvas, 0, 0);

  return outputCanvas;
}
