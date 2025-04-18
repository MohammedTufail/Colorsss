import React, { useState } from "react";
import axios from "axios";

const ColorDetector = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imageId, setImageId] = useState<string | null>(null);
  const [colorData, setColorData] = useState<any>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    setSelectedFile(file);

    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadImage = async () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append("image", selectedFile);

    try {
      interface UploadResponse {
        image_id: string;
      }

      const response = await axios.post<UploadResponse>(
        "http://localhost:5000/upload",
        formData
      );
      console.log("The response is", response.data.image_id);

      setImageId(response.data.image_id);
      alert("Image uploaded! Now click on the image to detect a color.");
    } catch (error) {
      console.error("Upload failed:", error);
    }
  };
  const handleImageClick = async (e: React.MouseEvent<HTMLImageElement>) => {
    if (!imageId || !preview) return;

    const img = e.currentTarget;
    const rect = img.getBoundingClientRect();

    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const scaleX = img.naturalWidth / img.clientWidth;
    const scaleY = img.naturalHeight / img.clientHeight;

    const actualX = Math.round(clickX * scaleX);
    const actualY = Math.round(clickY * scaleY);

    try {
      const response = await axios.get(
        `http://localhost:5000/detect/${imageId}/${actualX}/${actualY}`
      );
      setColorData(response.data);
    } catch (error) {
      console.error("Detection failed:", error);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-2">Color Detector</h2>
      <input type="file" onChange={handleFileChange} className="mb-2" />
      <button
        onClick={uploadImage}
        className="bg-blue-500 text-white px-4 py-2 rounded mb-4"
      >
        Upload Image
      </button>
      {preview && (
        <img
          src={preview}
          alt="Uploaded preview"
          onClick={handleImageClick}
          className="max-w-full border cursor-crosshair"
        />
      )}
      <div className="space-y-20">
        {/* Hero Section with Enhanced Animation and Colors */}
        <div className="relative overflow-hidden bg-gradient-rainbow rainbow-animate rounded-[2.5rem] p-8 md:p-20">
          <div className="absolute inset-0 bg-black/30 pointer-events-none" />
          <div className="absolute inset-0 bg-grid-white/[0.2] bg-grid-16 pointer-events-none" />
          <div className="absolute inset-0 bg-gradient-radial from-white/20 via-transparent to-transparent pointer-events-none" />
          {colorData && (
            <div className="mt-4 p-4 border rounded shadow">
              <p>
                <strong>Color:</strong> {colorData.color_name}
              </p>
              <p>
                <strong>RGB:</strong> ({colorData.r}, {colorData.g},{" "}
                {colorData.b})
              </p>
              <p>
                <strong>HEX:</strong> {colorData.hex}
              </p>
              <div
                className="w-16 h-16 mt-2 rounded"
                style={{ backgroundColor: colorData.hex }}
              ></div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ColorDetector;
