import React, { useState } from "react";
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

const ColorDetector = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<"image" | "video" | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [imageId, setImageId] = useState<string | null>(null);
  const [colorData, setColorData] = useState<any>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setSelectedFile(file || null);
    setColorData(null);
    setImageId(null);

    if (file) {
      const isVideo = file.type.startsWith("video/");
      setFileType(isVideo ? "video" : "image");

      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadFile = async () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append("media", selectedFile);

    try {
      const response = await axios.post<{ image_id: string }>(
        "http://localhost:5001/upload",
        formData
      );
      setImageId(response.data.image_id);
      alert("Upload successful! Now click to detect color.");
    } catch (error) {
      console.error("Upload failed:", error);
    }
  };

  const handleMediaClick = async (
    e: React.MouseEvent<HTMLImageElement | HTMLVideoElement>
  ) => {
    if (!preview) return;

    const element = e.currentTarget;

    // If video, capture current frame and send as image
    if (element instanceof HTMLVideoElement) {
      const canvas = document.createElement("canvas");
      canvas.width = element.videoWidth;
      canvas.height = element.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.drawImage(element, 0, 0, canvas.width, canvas.height);

      canvas.toBlob(async (blob) => {
        if (!blob) return;

        const formData = new FormData();
        formData.append(
          "media",
          new File([blob], "frame.jpg", { type: "image/jpeg" })
        );

        try {
          const uploadRes = await axios.post<{ image_id: string }>(
            "http://localhost:5001/upload",
            formData
          );
          const newImageId = uploadRes.data.image_id;
          setImageId(newImageId);

          // Get click position on the element
          const rect = element.getBoundingClientRect();
          const clickX = e.clientX - rect.left;
          const clickY = e.clientY - rect.top;
          const scaleX = element.videoWidth / element.clientWidth;
          const scaleY = element.videoHeight / element.clientHeight;

          const actualX = Math.round(clickX * scaleX);
          const actualY = Math.round(clickY * scaleY);

          // Send to detect
          const detectRes = await axios.get<{
            color_name: string;
            r: number;
            g: number;
            b: number;
            hex: string;
          }>(
            `http://localhost:5001/detect/${newImageId}/${actualX}/${actualY}`
          );

          setColorData(detectRes.data);

          const { color_name, r, g, b } = detectRes.data;
          const speech = `The color is ${color_name}. RGB values are ${r}, ${g}, ${b}.`;
          speakColorName(speech);
        } catch (err) {
          console.error("Frame upload/detect failed:", err);
        }
      }, "image/jpeg");

      return;
    }

    // For image file
    if (!imageId) return;

    const rect = element.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    const scaleX = element.naturalWidth / element.clientWidth;
    const scaleY = element.naturalHeight / element.clientHeight;
    const actualX = Math.round(clickX * scaleX);
    const actualY = Math.round(clickY * scaleY);

    try {
      const response = await axios.get<{
        color_name: string;
        r: number;
        g: number;
        b: number;
        hex: string;
      }>(`http://localhost:5001/detect/${imageId}/${actualX}/${actualY}`);
      setColorData(response.data);
      const { color_name, r, g, b } = response.data;
      const speech = `The color is ${color_name}. RGB values ${r},${g},${b}.`;
      speakColorName(speech);
    } catch (error) {
      console.error("Detection failed:", error);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-white text-3xl font-bold mb-2">Color Detector</h2>
      <input
        type="file"
        onChange={handleFileChange}
        accept="image/*,video/*"
        className="mb-2"
      />
      <button
        onClick={uploadFile}
        className="bg-gradient-to-r from-blue-500 to-indigo-600 text-bold text-white px-5 py-2 rounded mb-4"
      >
        Upload File
      </button>

      {preview && fileType === "image" && (
        <img
          src={preview}
          alt="Uploaded Preview"
          onClick={handleMediaClick}
          className="max-w-full border cursor-crosshair"
        />
      )}

      {preview && fileType === "video" && (
        <video
          src={preview}
          controls
          onClick={handleMediaClick}
          className="max-w-full border cursor-crosshair"
        />
      )}

      {colorData && (
        <div className="mt-4 p-4 border rounded shadow bg-white text-black">
          <p className="font-bold text-white text-xl">
            Color: {colorData.color_name}
          </p>
          <p className="font-bold text-white text-xl">
            RGB: ({colorData.r}, {colorData.g}, {colorData.b})
          </p>
          <p className="font-bold text-white text-xl">HEX: {colorData.hex}</p>
          <div
            className="w-16 h-16 mt-2 rounded"
            style={{ backgroundColor: colorData.hex }}
          ></div>
        </div>
      )}
    </div>
  );
};

export default ColorDetector;
