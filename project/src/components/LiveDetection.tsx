import React, { useEffect, useRef, useState } from "react";
import axios from "axios";

const speakColorName = (speech: string) => {
  const msg = new SpeechSynthesisUtterance();
  msg.text = speech;
  msg.lang = "en-US";
  msg.pitch = 1;
  msg.rate = 1;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(msg);
};

const stopSpeech = () => {
  window.speechSynthesis.cancel();
};

interface ColorData {
  name: string;
  rgb: {
    r: number;
    g: number;
    b: number;
  };
  hex: string;
  timestamp: string;
}

const API_BASE_URL = "http://127.0.0.1:5000";

const LiveDetection: React.FC = () => {
  const videoRef = useRef<HTMLImageElement>(null);
  const [colorData, setColorData] = useState<ColorData | null>(null);
  const [isDetecting, setIsDetecting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [videoKey, setVideoKey] = useState<number>(0);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const useCanvasMethod = false;

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

    return () => {
      if (isDetecting) {
        stopDetection();
      }
    };
  }, []);

  useEffect(() => {
    if (colorData) {
      const speech = `The color is ${colorData.name}. RGB values are (${colorData.rgb.r}, ${colorData.rgb.g}, ${colorData.rgb.b}).`;
      speakColorName(speech);
 
    }
  }, [colorData]);
 
  
  const startDetection = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/setup`);
      const responseData = response.data as { status: string };
      if (responseData.status === "Camera initialized successfully") {
        setIsDetecting(true);
        setVideoKey((prev) => prev + 1);
      }
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
      stopSpeech();
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
      const res = await axios.post(`${API_BASE_URL}/live_color_data`, { x, y });
      setColorData(res.data as ColorData);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch color info", err);
      setError(
        "Failed to detect color. Please try clicking again or restart detection."
      );
    }
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const pixel = ctx.getImageData(x, y, 1, 1).data;
    const [r, g, b] = [pixel[0], pixel[1], pixel[2]];
    const hex =
      "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);

    setColorData({
      name: `RGB(${r},${g},${b})`,
      rgb: { r, g, b },
      hex,
      timestamp: new Date().toISOString(),
    });
  };

  return (
    <div className="text-center p-4">
      <h2 className="text-white text-2xl font-bold mb-4">
        Live Color Detection
      </h2>

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
            src={`${API_BASE_URL}/video_feed?t=${Date.now()}`}
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
      <button
        onClick={stopSpeech}
        className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded ml-2"
      >
        Stop Speech
      </button>
      {colorData && (
        <div className="mt-4 p-4 border rounded shadow bg-white w-[640px] mx-auto">
          <p className="font-bold flex text-white text-xl">
            <strong>COLOR NAME:-</strong> {colorData.name}
          </p>
          <p className="font-bold flex text-white text-xl">
            <strong>RGB:-</strong> ({colorData.rgb.r}, {colorData.rgb.g},{" "}
            {colorData.rgb.b})
          </p>
          <p className="font-bold flex text-white text-xl">
            <strong>HEX:-</strong> {colorData.hex}
          </p>

          <div
            className="mt-2 w-24 h-10 border flex"
            style={{ backgroundColor: colorData.hex }}
          />
        </div>
      )}
    </div>
  );
};

export default LiveDetection;
