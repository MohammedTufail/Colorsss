import React, { useState, useRef, useEffect } from "react";

function ColorBlindnessSimulator() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageLoadAttempts, setImageLoadAttempts] = useState<
    Record<string, number>
  >({});

  interface SimulationResult {
    originalImage: string;
    simulations: Record<string, string>;
    dominantColors: string[];
    suggestedColors: Record<string, string>;
  }

  const [result, setResult] = useState<SimulationResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Server base URL - adjust this based on your Flask server's address
  // Use an environment variable or configure this dynamically
  const SERVER_BASE_URL = "http://localhost:5000";

  // Colorblind type descriptions
  const colorblindTypes = {
    deuteranopia: "Deuteranopia (Red-Green - Most Common)",
    protanopia: "Protanopia (Red-Green)",
    tritanopia: "Tritanopia (Blue-Yellow)",
  };

  // Clear console on mount to reduce clutter
  useEffect(() => {
    console.clear();
    console.log("Component mounted - ColorBlindnessSimulator");
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const objectUrl = URL.createObjectURL(file);
      setPreviewUrl(objectUrl);
      setResult(null);
      setError(null);
      setImageLoadAttempts({});
    }
  };

  // Removed unused handleImageError function

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsLoading(true);
    setError(null);
    setImageLoadAttempts({});

    const formData = new FormData();
    formData.append("image", selectedFile);

    try {
      const response = await fetch(`${SERVER_BASE_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ error: "Unknown error" }));
        throw new Error(errorData.error || "Server responded with an error");
      }

      const data = await response.json();
      console.log("Server response:", data);
      setResult(data);
    } catch (error) {
      console.error("Error uploading file:", error);
      setError(
        error instanceof Error ? error.message : "Failed to process image"
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Function to generate complete image URL
  const getImageUrl = (path: string) => {
    if (!path) return "";

    // If path already starts with http or https, use it as is
    if (path.startsWith("http")) return path;

    // Otherwise prepend the server base URL
    return `${SERVER_BASE_URL}${path}`;
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-white text-2xl font-bold text-center mb-6">
        ColorBlind Simulation Tool
      </h1>

      <form onSubmit={handleSubmit} className="mb-6">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center mb-4">
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
            ref={fileInputRef}
          />

          {!previewUrl ? (
            <div>
              <div className="flex justify-center mb-4">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
              </div>
              <p className="mb-4 text-sm text-gray-200">
                Upload an image to see how it appears to colorblind users
              </p>
              <label
                htmlFor="file-upload"
                className="cursor-pointer inline-flex items-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              >
                Select Image
              </label>
            </div>
          ) : (
            <div>
              <img
                src={previewUrl}
                alt="Preview"
                className="max-h-64 mx-auto mb-4"
              />
              <div>
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer inline-flex items-center px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 mr-2"
                >
                  Change Image
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null);
                    setPreviewUrl(null);
                    setResult(null);
                    setError(null);
                    setImageLoadAttempts({});
                    if (fileInputRef.current) fileInputRef.current.value = "";
                  }}
                  className="inline-flex items-center px-3 py-1 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200"
                >
                  Remove
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="text-center">
          <button
            type="submit"
            disabled={!selectedFile || isLoading}
            className={`px-4 py-2 ${
              !selectedFile || isLoading
                ? "bg-gray-400"
                : "bg-blue-500 hover:bg-blue-600"
            } text-white rounded-md`}
          >
            {isLoading ? "Processing..." : "Generate Colorblind Simulations"}
          </button>
        </div>
      </form>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          <p className="font-medium">Error: {error}</p>
          <p className="text-sm mt-1">
            Please check the server connection and try again.
          </p>
        </div>
      )}

      {result && (
        <div className="mt-8">
          <h2 className="text-white text-xl font-semibold mb-4">
            Simulation Results
          </h2>
          <p className="text-white text-sm text-gray-500 mb-4">
            These simulations show how your image would appear to users with
            different types of color blindness.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <div className="border rounded-md p-4">
              <h3 className="text-white text-center mb-2 font-medium">Original Image</h3>
              {result.originalImage && (
                <div className="relative min-h-[150px] flex items-center justify-center">
                  <img
                    src={getImageUrl(result.originalImage)}
                    alt="Original"
                    className="max-h-64 mx-auto"
                    onError={(e) => {
                      console.error("Failed to load original image:", e);
                      const imgElement = e.currentTarget;
                      const attempts = imageLoadAttempts["original"] || 0;
                      if (attempts < 3) {
                        // Add cache-busting parameter and retry
                        imgElement.src = `${getImageUrl(
                          result.originalImage
                        )}?retry=${Date.now()}`;
                      } else {
                        imgElement.src = "/placeholder-image.png";
                        imgElement.alt = "Image failed to load";
                      }
                    }}
                  />
                </div>
              )}
            </div>

            {Object.entries(result.simulations).map(([type, imagePath]) => {
              const colorblindType = type as keyof typeof colorblindTypes;
              return (
                <div key={type} className="border rounded-md p-4">
                  <h3 className="text-white text-center mb-2 font-medium">
                    {colorblindTypes[colorblindType]}
                  </h3>
                  <div className="relative min-h-[150px] flex items-center justify-center">
                    <img
                      src={getImageUrl(imagePath)}
                      alt={`${type} simulation`}
                      className="max-h-64 mx-auto"
                      onError={(e) => {
                        const imgElement = e.currentTarget;
                        const attempts = imageLoadAttempts[type] || 0;
                        if (attempts < 3) {
                          // Add cache-busting parameter and retry
                          imgElement.src = `${getImageUrl(
                            imagePath
                          )}?retry=${Date.now()}`;
                          setImageLoadAttempts((prev) => ({
                            ...prev,
                            [type]: (prev[type] || 0) + 1,
                          }));
                        } else {
                          imgElement.src = "/placeholder-image.png";
                          imgElement.alt = "Image failed to load";
                        }
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="bg-blue-50 p-4 rounded-lg mb-6">
            <h3 className="text-lg font-medium mb-2">Color Analysis</h3>
            <p className="mb-4">
              We detected these dominant colors in your image:
            </p>

            <div className="flex flex-wrap gap-2 mb-4">
              {result.dominantColors.map((color, i) => (
                <div key={i} className="flex flex-col items-center">
                  <div
                    style={{ backgroundColor: color }}
                    className="w-12 h-12 rounded-md shadow-sm border border-gray-200"
                  ></div>
                  <span className="text-xs mt-1">{color}</span>
                </div>
              ))}
            </div>

            <h3 className="text-lg font-medium mb-2">
              Suggested Color Alternatives
            </h3>
            <p className="mb-4">
              Consider these alternative colors for better visibility by
              colorblind users:
            </p>

            <div className="flex flex-wrap gap-4">
              {Object.entries(result.suggestedColors).map(
                ([original, suggested], i) => (
                  <div
                    key={i}
                    className="flex items-center bg-white p-2 rounded-md shadow-sm"
                  >
                    <div className="flex flex-col items-center mr-2">
                      <div
                        style={{ backgroundColor: original }}
                        className="w-10 h-10 rounded-md border border-gray-200"
                      ></div>
                      <span className="text-xs mt-1">Original</span>
                    </div>

                    <span className="text-gray-400 mx-2">→</span>

                    <div className="flex flex-col items-center">
                      <div
                        style={{ backgroundColor: suggested }}
                        className="w-10 h-10 rounded-md border border-gray-200"
                      ></div>
                      <span className="text-xs mt-1">Suggested</span>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium mb-2">Tips for Developers</h3>
            <ul className="list-disc pl-5 space-y-2">
              <li>
                Avoid using red and green together as they are difficult to
                distinguish for most colorblind users
              </li>
              <li>Use high contrast between text and background colors</li>
              <li>
                Don't rely on color alone to convey information - add text
                labels, patterns, or icons
              </li>
              <li>
                Consider using tools like this one to test your UI before
                finalizing
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default ColorBlindnessSimulator;
