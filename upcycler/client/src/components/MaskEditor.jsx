import React, { useRef, useEffect, useState } from "react";

export function MaskEditor({ maskData, onMaskChange, width, height }) {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [brushSize, setBrushSize] = useState(20);
  const [mode, setMode] = useState("add"); // 'add' or 'erase'

  useEffect(() => {
    if (!maskData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    canvas.width = width;
    canvas.height = height;

    ctx.putImageData(maskData, 0, 0);
  }, [maskData, width, height]);

  const draw = (e) => {
    if (!isDrawing) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    ctx.globalCompositeOperation =
      mode === "add" ? "source-over" : "destination-out";
    ctx.fillStyle = mode === "add" ? "white" : "black";
    ctx.beginPath();
    ctx.arc(x, y, brushSize, 0, Math.PI * 2);
    ctx.fill();

    // Update mask data
    const newMaskData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    onMaskChange(newMaskData);
  };

  const handleMouseDown = (e) => {
    setIsDrawing(true);
    draw(e);
  };

  const handleMouseMove = (e) => {
    if (isDrawing) {
      draw(e);
    }
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-4 items-center">
        <label className="text-white text-sm">Brush Size:</label>
        <input
          type="range"
          min="5"
          max="50"
          value={brushSize}
          onChange={(e) => setBrushSize(parseInt(e.target.value))}
          className="flex-1"
        />
        <span className="text-white text-sm w-12">{brushSize}px</span>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => setMode("add")}
          className={`px-4 py-2 rounded ${
            mode === "add"
              ? "bg-modern text-white"
              : "bg-gray-600 text-gray-300"
          }`}
        >
          Add
        </button>
        <button
          onClick={() => setMode("erase")}
          className={`px-4 py-2 rounded ${
            mode === "erase"
              ? "bg-red-600 text-white"
              : "bg-gray-600 text-gray-300"
          }`}
        >
          Erase
        </button>
      </div>

      <div className="border-2 border-gray-600 rounded overflow-hidden">
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className="cursor-crosshair max-w-full"
          style={{ imageRendering: "pixelated" }}
        />
      </div>

      <p className="text-gray-400 text-xs">
        Click and drag to edit the mask. White areas will receive the style.
      </p>
    </div>
  );
}
