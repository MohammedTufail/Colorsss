import React, { useEffect, useRef, useState } from "react";
import axios from "axios";

interface ColorData {
  name: string;
  hex: string;
  rgb: {
    r: number;
    g: number;
    b: number;
  };
  timestamp: string;
}

const API_BASE_URL = "http://127.0.0.1:5000";

const LiveDetection: React.FC = () => {
  const videoRef = useRef<HTMLImageElement>(null);
  const [colorData, setColorData] = useState<ColorData | null>(null);
  const [isDetecting, setIsDetecting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [videoKey, setVideoKey] = useState<number>(0); // Used to force reload the video

  // Check if the API is available
  useEffect(() => {
    const checkApiAvailability = async () => {
      try {
        await axios.get(`${API_BASE_URL}/health`);
        setError(null);
      } catch (err) {
        setError(
          "API server is not available. Please make sure the Flask server is running on port 5000."
        );
        console.error("API server not available", err);
      }
    };

    checkApiAvailability();

    // Cleanup on unmount
    return () => {
      if (isDetecting) {
        stopDetection();
      }
    };
  }, []);

  const startDetection = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:5000/setup");
      console.log(response.data);
    } catch (error) {
      console.error("Error starting detection:", error);
    }
  };

  const stopDetection = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/teardown`);
      setIsDetecting(false);
      setColorData(null);
    } catch (err) {
      console.error("Failed to stop detection", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleDetection = () => {
    if (isDetecting) {
      stopDetection();
    } else {
      startDetection();
    }
  };

  const handleClick = async (e: React.MouseEvent<HTMLImageElement>) => {
    if (!videoRef.current || !isDetecting) return;

    const bounds = videoRef.current.getBoundingClientRect();
    const x = Math.floor(e.clientX - bounds.left);
    const y = Math.floor(e.clientY - bounds.top);

    try {
      const res = await axios.post(`${API_BASE_URL}/live_color_data`, {
        x,
        y,
      });
      setColorData(res.data as ColorData);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch color info", err);
      setError(
        "Failed to detect color. Please try clicking again or restart detection."
      );
    }
  };

  // Alternative method using canvas to extract colors directly from the video stream
  const useCanvasMethod = false; // Set to true to enable this alternative method

  const canvasRef = useRef<HTMLCanvasElement>(null);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Get pixel data
    const pixel = ctx.getImageData(x, y, 1, 1).data;
    const [r, g, b] = [pixel[0], pixel[1], pixel[2]];

    // Create hex color
    const hex =
      "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);

    // Set color data
    setColorData({
      name: `RGB(${r},${g},${b})`, // We don't have color names client-side
      hex: hex,
      rgb: { r, g, b },
      timestamp: new Date().toISOString(),
    });
  };

  return (
    <div className="text-center p-4">
      <h2 className="text-xl font-bold mb-4">Live Color Detection</h2>

      <button
        onClick={toggleDetection}
        disabled={loading}
        className={`mb-4 px-4 py-2 rounded-md ${
          loading
            ? "bg-gray-400"
            : isDetecting
            ? "bg-red-500 hover:bg-red-600"
            : "bg-green-500 hover:bg-green-600"
        } text-white`}
      >
        {loading
          ? "Processing..."
          : isDetecting
          ? "Stop Detection"
          : "Start Detection"}
      </button>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded border border-red-300">
          {error}
        </div>
      )}

      {isDetecting && !useCanvasMethod && (
        <div className="mb-4">
          <p className="mb-2 text-gray-600">
            Click on the video to detect colors
          </p>
          <img
            key={videoKey}
            src={`${API_BASE_URL}/video_feed?t=${Date.now()}`} // Add timestamp to prevent caching
            alt="Live Camera Feed"
            ref={videoRef}
            onClick={handleClick}
            className="mx-auto border-4 border-gray-300 rounded-xl cursor-crosshair"
            style={{ maxWidth: "100%", height: "auto" }}
          />
        </div>
      )}

      {isDetecting && useCanvasMethod && (
        <div className="mb-4">
          <p className="mb-2 text-gray-600">
            Click on the canvas to detect colors
          </p>
          <canvas
            ref={canvasRef}
            onClick={handleCanvasClick}
            width="640"
            height="480"
            className="mx-auto border-4 border-gray-300 rounded-xl cursor-crosshair"
          />
        </div>
      )}

      {colorData && (
        <div className="mt-4 p-4 bg-gray-100 rounded shadow">
          <p>
            <strong>Color Name:</strong> {colorData.name}
          </p>
          <p>
            <strong>HEX:</strong> {colorData.hex}
          </p>
          <p>
            <strong>RGB:</strong> ({colorData.rgb.r}, {colorData.rgb.g},{" "}
            {colorData.rgb.b})
          </p>
          <div
            className="mt-2 w-24 h-10 mx-auto border"
            style={{ backgroundColor: colorData.hex }}
          />
        </div>
      )}
    </div>
  );
};

export default LiveDetection;
