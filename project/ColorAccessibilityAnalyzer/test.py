from PIL import Image
import numpy as np
import cv2
import os
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

# ------------ Configuration ------------
INPUT_IMAGE_PATH = "colorpic.jpg"  # <- replace with your image path
OUTPUT_DIR = "output"
DELTA_THRESHOLD = 10
# ---------------------------------------

# Colorblind simulation matrices
COLORBLIND_MATRICES = {
    "deuteranopia": np.array([[0.625, 0.70, 0], [0.70, 0.625, 0], [0, 0, 1]]),
    "protanopia": np.array([[0.567, 0.433, 0], [0.558, 0.442, 0], [0, 0.242, 0.758]]),
    "tritanopia": np.array([[0.95, 0.05, 0], [0, 0.433, 0.567], [0, 0.475, 0.525]]),
}

# Helper: simulate colorblindness
def simulate_colorblind(image_np, matrix):
    flat_img = image_np.reshape(-1, 3) / 255.0
    simulated = np.dot(flat_img, matrix.T)
    simulated = np.clip(simulated * 255, 0, 255).astype(np.uint8)
    return simulated.reshape(image_np.shape)

# Helper: analyze indistinguishable colors
def analyze_colors(image_np):
    height, width, _ = image_np.shape
    color_set = {}
    indistinguishable_pairs = []

    for y in range(0, height, 10):  # Step size of 10 pixels
        for x in range(0, width, 10):
            r, g, b = image_np[y, x]
            srgb = sRGBColor(r / 255, g / 255, b / 255)
            lab = convert_color(srgb, LabColor)
            hex_code = '#{:02x}{:02x}{:02x}'.format(r, g, b)

            for existing_hex, existing_lab in color_set.items():
                delta = delta_e_cie2000(lab, existing_lab)
                if delta < DELTA_THRESHOLD:
                    indistinguishable_pairs.append((existing_hex, hex_code))
                    break
            else:
                color_set[hex_code] = lab

    return indistinguishable_pairs

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load image
    try:
        image = Image.open(INPUT_IMAGE_PATH).convert("RGB")
        image_np = np.array(image)
    except Exception as e:
        print(" Error loading image:", e)
        return

    # Analyze indistinguishable colors
    print("Analyzing color differences...")
    pairs = analyze_colors(image_np)
    print(f"Found {len(pairs)} indistinguishable color pairs (ΔE < {DELTA_THRESHOLD}):")
    for p1, p2 in pairs:
        print(f" - {p1} ≈ {p2}")

    # Simulate and save images
    print("\n Generating simulated views for colorblindness...")
    for mode, matrix in COLORBLIND_MATRICES.items():
        simulated = simulate_colorblind(image_np, matrix)
        # Convert simulated image from RGB to BGR before saving
        save_path = os.path.join(OUTPUT_DIR, f"{mode}.png")
        cv2.imwrite(save_path, cv2.cvtColor(simulated, cv2.COLOR_RGB2BGR))
        print(f"Saved {mode} simulation to {save_path}")

if __name__ == "__main__":
    main()
    '''
    comment
 import { useState, useEffect, useRef } from "react";
 import {
  Upload,
  ArrowRight,
  RefreshCw,
  Search,
  Download,
  EyeOff,
  Palette,
} from "lucide-react";

export default function ColorBlindnessSimulator() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [colorblindType, setColorblindType] = useState("deuteranopia");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState("simulator");
  const [colorToTest, setColorToTest] = useState("#3498db");
  const [colorSimulation, setColorSimulation] = useState(null);
  const fileInputRef = useRef(null);

  const colorblindTypes = {
    deuteranopia: "Deuteranopia (Red-Green - Most Common)",
    protanopia: "Protanopia (Red-Green)",
    tritanopia: "Tritanopia (Blue-Yellow)",
  };

  const descriptions = {
    deuteranopia:
      "People with deuteranopia have difficulty distinguishing between red and green colors. This is the most common type of color blindness, affecting approximately 6% of males.",
    protanopia:
      "People with protanopia cannot perceive red light. They also have difficulty distinguishing between red and green colors, often seeing reds as brownish-yellow.",
    tritanopia:
      "People with tritanopia have difficulty distinguishing between blue and yellow colors. This is the rarest form of color blindness, affecting less than 0.01% of people.",
  };

  useEffect(() => {
    // Clean up preview URL when component unmounts
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      const objectUrl = URL.createObjectURL(file);
      setPreviewUrl(objectUrl);
      setResult(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsLoading(true);
    const formData = new FormData();
    formData.append("image", selectedFile);
    formData.append("colorblindType", colorblindType);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Server responded with an error");
      }

      const data = await response.json();
      setResult(data[colorblindType]);
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Failed to process image. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const simulateColorTest = async () => {
    try {
      const response = await fetch("/api/simulate-color", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          color: colorToTest,
          colorblindType,
        }),
      });

      if (!response.ok) {
        throw new Error("Server responded with an error");
      }

      const data = await response.json();
      setColorSimulation(data);
    } catch (error) {
      console.error("Error simulating color:", error);
      alert("Failed to simulate color. Please try again.");
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setPreviewUrl("");
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const downloadReport = () => {
    if (!result || !result.colorAnalysis) return;

    const { colorAnalysis } = result;
    const reportContent = `
# Colorblindness Simulation Report for ${colorblindType}

## Problematic Colors
${colorAnalysis.problematic_colors.map((color) => `- ${color}`).join("\n")}

## Suggested Alternatives
${Object.entries(colorAnalysis.suggested_alternatives)
  .map(
    ([original, suggested]) =>
      `- Original: ${original} → Suggested: ${suggested}`
  )
  .join("\n")}

## All Dominant Colors
${colorAnalysis.dominant_colors
  .map(
    (color) =>
      `- ${color} → appears as ${colorAnalysis.colorblind_versions[color]} to people with ${colorblindType}`
  )
  .join("\n")}
`;

    const blob = new Blob([reportContent], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `colorblind-report-${colorblindType}-${new Date()
      .toISOString()
      .slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <header className="bg-indigo-700 text-white shadow-md">
        <div className="container mx-auto py-4 px-6">
          <h1 className="text-2xl font-bold">ColorBlind Insight Tool</h1>
          <p className="text-indigo-200">
            Improve your website's accessibility for colorblind users
          </p>
        </div>
      </header>

      <div className="container mx-auto p-6 flex-grow">
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex mb-6 border-b">
            <button
              className={`px-4 py-2 mr-4 focus:outline-none ${
                activeTab === "simulator"
                  ? "text-indigo-600 border-b-2 border-indigo-600 font-medium"
                  : "text-gray-500"
              }`}
              onClick={() => setActiveTab("simulator")}
            >
              Image Simulator
            </button>
            <button
              className={`px-4 py-2 mr-4 focus:outline-none ${
                activeTab === "colortest"
                  ? "text-indigo-600 border-b-2 border-indigo-600 font-medium"
                  : "text-gray-500"
              }`}
              onClick={() => setActiveTab("colortest")}
            >
              Color Tester
            </button>
            <button
              className={`px-4 py-2 focus:outline-none ${
                activeTab === "info"
                  ? "text-indigo-600 border-b-2 border-indigo-600 font-medium"
                  : "text-gray-500"
              }`}
              onClick={() => setActiveTab("info")}
            >
              About Colorblindness
            </button>
          </div>

          {activeTab === "simulator" && (
            <div>
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-2">
                  Simulate Colorblindness
                </h2>
                <p className="text-gray-600 mb-4">
                  {descriptions[colorblindType]}
                </p>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Select Colorblindness Type:
                  </label>
                  <select
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    value={colorblindType}
                    onChange={(e) => setColorblindType(e.target.value)}
                  >
                    {Object.entries(colorblindTypes).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-md p-6 text-center">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFileChange}
                      className="hidden"
                      id="file-upload"
                      ref={fileInputRef}
                    />
                    {!previewUrl ? (
                      <div className="space-y-2">
                        <Upload className="mx-auto h-12 w-12 text-gray-400" />
                        <label
                          htmlFor="file-upload"
                          className="cursor-pointer inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                          Select Image
                        </label>
                        <p className="text-sm text-gray-500">
                          PNG, JPG, GIF up to 10MB
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <img
                          src={previewUrl}
                          alt="Preview"
                          className="max-h-48 mx-auto"
                        />
                        <div className="flex justify-center space-x-4">
                          <label
                            htmlFor="file-upload"
                            className="cursor-pointer inline-flex items-center px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                          >
                            Change Image
                          </label>
                          <button
                            type="button"
                            onClick={resetForm}
                            className="inline-flex items-center px-3 py-1 bg-red-100 text-red-700 text-sm rounded-md hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex justify-center">
                    <button
                      type="submit"
                      disabled={!selectedFile || isLoading}
                      className={`flex items-center px-4 py-2 ${
                        !selectedFile || isLoading
                          ? "bg-gray-400"
                          : "bg-indigo-600 hover:bg-indigo-700"
                      } text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                    >
                      {isLoading ? (
                        <RefreshCw className="animate-spin mr-2 h-5 w-5" />
                      ) : (
                        <EyeOff className="mr-2 h-5 w-5" />
                      )}
                      {isLoading ? "Processing..." : "Simulate Colorblindness"}
                    </button>
                  </div>
                </form>
              </div>

              {result && (
                <div className="mt-8 border-t pt-6">
                  <h3 className="text-lg font-semibold mb-4">
                    Simulation Results for {colorblindType}
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div className="border rounded-md p-4">
                      <h4 className="text-center mb-2 font-medium">
                        Original Image
                      </h4>
                      <div className="flex justify-center">
                        <img
                          src={result.originalImage}
                          alt="Original"
                          className="max-h-64"
                        />
                      </div>
                    </div>
                    <div className="border rounded-md p-4">
                      <h4 className="text-center mb-2 font-medium">
                        How it appears with {colorblindType}
                      </h4>
                      <div className="flex justify-center">
                        <img
                          src={result.simulatedImage}
                          alt={`${colorblindType} simulation`}
                          className="max-h-64"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 p-6 rounded-lg mb-6">
                    <div className="flex justify-between items-center mb-4">
                      <h4 className="text-lg font-medium">
                        Color Analysis Report
                      </h4>
                      <button
                        onClick={downloadReport}
                        className="flex items-center text-sm px-3 py-1 bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200"
                      >
                        <Download className="h-4 w-4 mr-1" /> Download Report
                      </button>
                    </div>

                    {result.colorAnalysis.problematic_colors.length > 0 ? (
                      <div>
                        <h5 className="font-medium text-red-600 mb-2">
                          Problematic Colors
                        </h5>
                        <p className="text-sm text-gray-600 mb-3">
                          These colors may be difficult to distinguish for
                          people with {colorblindType}
                        </p>
                        <div className="flex flex-wrap gap-3 mb-6">
                          {result.colorAnalysis.problematic_colors.map(
                            (color, idx) => (
                              <div
                                key={idx}
                                className="flex flex-col items-center"
                              >
                                <div className="flex items-center mb-1">
                                  <div
                                    style={{ backgroundColor: color }}
                                    className="w-10 h-10 rounded border"
                                  ></div>
                                  <ArrowRight className="mx-2 h-4 w-4 text-gray-400" />
                                  <div
                                    style={{
                                      backgroundColor:
                                        result.colorAnalysis
                                          .colorblind_versions[color],
                                    }}
                                    className="w-10 h-10 rounded border"
                                  ></div>
                                </div>
                                <div className="text-xs text-center">
                                  <div>{color}</div>
                                  <div className="text-gray-500">
                                    {
                                      result.colorAnalysis.colorblind_versions[
                                        color
                                      ]
                                    }
                                  </div>
                                </div>
                              </div>
                            )
                          )}
                        </div>

                        <h5 className="font-medium text-green-600 mb-2">
                          Suggested Alternatives
                        </h5>
                        <p className="text-sm text-gray-600 mb-3">
                          Consider using these colors instead for better
                          accessibility
                        </p>
                        <div className="flex flex-wrap gap-3">
                          {Object.entries(
                            result.colorAnalysis.suggested_alternatives
                          ).map(([original, suggested], idx) => (
                            <div
                              key={idx}
                              className="flex flex-col items-center"
                            >
                              <div className="flex items-center mb-1">
                                <div
                                  style={{ backgroundColor: original }}
                                  className="w-10 h-10 rounded border"
                                ></div>
                                <ArrowRight className="mx-2 h-4 w-4 text-gray-400" />
                                <div
                                  style={{ backgroundColor: suggested }}
                                  className="w-10 h-10 rounded border"
                                ></div>
                              </div>
                              <div className="text-xs text-center">
                                <div>{original}</div>
                                <div className="text-green-600">
                                  {suggested}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="text-green-600">
                        No problematic colors detected. Your image should be
                        perceivable by people with {colorblindType}.
                      </div>
                    )}
                  </div>

                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h4 className="text-lg font-medium mb-4">
                      All Dominant Colors
                    </h4>
                    <div className="flex flex-wrap gap-3">
                      {result.colorAnalysis.dominant_colors.map(
                        (color, idx) => (
                          <div key={idx} className="flex flex-col items-center">
                            <div className="flex items-center mb-1">
                              <div
                                style={{ backgroundColor: color }}
                                className="w-8 h-8 rounded border"
                              ></div>
                              <ArrowRight className="mx-1 h-3 w-3 text-gray-400" />
                              <div
                                style={{
                                  backgroundColor:
                                    result.colorAnalysis.colorblind_versions[
                                      color
                                    ],
                                }}
                                className="w-8 h-8 rounded border"
                              ></div>
                            </div>
                            <div className="text-xs">{color}</div>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "colortest" && (
            <div>
              <h2 className="text-xl font-semibold mb-4">
                Test Individual Colors
              </h2>
              <p className="text-gray-600 mb-6">
                Enter a hex color to see how it appears to people with different
                types of colorblindness. This tool helps you test your color
                choices before implementing them in your design.
              </p>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Colorblindness Type:
                </label>
                <select
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  value={colorblindType}
                  onChange={(e) => setColorblindType(e.target.value)}
                >
                  {Object.entries(colorblindTypes).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Enter Hex Color:
                </label>
                <div className="flex">
                  <input
                    type="text"
                    value={colorToTest}
                    onChange={(e) => setColorToTest(e.target.value)}
                    placeholder="#RRGGBB"
                    pattern="^#([A-Fa-f0-9]{6})$"
                    className="flex-grow p-2 border border-gray-300 rounded-l-md focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <input
                    type="color"
                    value={colorToTest}
                    onChange={(e) => setColorToTest(e.target.value)}
                    className="w-12 h-10 p-0 border-0"
                  />
                  <button
                    type="button"
                    onClick={simulateColorTest}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-r-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <Search className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {colorSimulation && (
                <div className="mt-6 bg-gray-50 p-6 rounded-lg">
                  <h3 className="text-lg font-medium mb-4">
                    Color Simulation Results
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div className="flex flex-col items-center">
                      <div
                        style={{
                          backgroundColor: colorSimulation.originalColor,
                        }}
                        className="w-32 h-32 rounded-lg shadow-md mb-3"
                      ></div>
                      <div className="text-center">
                        <div className="font-medium">Original Color</div>
                        <div className="text-gray-600">
                          {colorSimulation.originalColor}
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col items-center">
                      <div
                        style={{
                          backgroundColor: colorSimulation.simulatedColor,
                        }}
                        className="w-32 h-32 rounded-lg shadow-md mb-3"
                      ></div>
                      <div className="text-center">
                        <div className="font-medium">
                          As seen with {colorblindType}
                        </div>
                        <div className="text-gray-600">
                          {colorSimulation.simulatedColor}
                        </div>
                      </div>
                    </div>
                  </div>

                  {colorSimulation.isProblematic && (
                    <div className="mt-4 p-4 border border-amber-200 bg-amber-50 rounded-md">
                      <h4 className="text-amber-800 font-medium mb-2">
                        Potential Accessibility Issue
                      </h4>
                      <p className="text-amber-700 mb-3">
                        This color might be difficult to perceive correctly for
                        people with {colorblindType}. The perceptual distance is{" "}
                        {Math.round(colorSimulation.colorDistance)}, which is
                        significant.
                      </p>

                      {colorSimulation.suggestedAlternative && (
                        <div className="mt-4">
                          <h5 className="text-green-700 font-medium mb-2">
                            Suggested Alternative
                          </h5>
                          <div className="flex items-center">
                            <div
                              style={{
                                backgroundColor: colorSimulation.originalColor,
                              }}
                              className="w-10 h-10 rounded border"
                            ></div>
                            <ArrowRight className="mx-2 h-4 w-4 text-gray-400" />
                            <div
                              style={{
                                backgroundColor:
                                  colorSimulation.suggestedAlternative,
                              }}
                              className="w-10 h-10 rounded border"
                            ></div>
                            <div className="ml-3">
                              <div className="text-sm font-medium">
                                {colorSimulation.suggestedAlternative}
                              </div>
                              <div className="text-xs text-gray-500">
                                This alternative will be more distinguishable
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === "info" && (
            <div>
              <h2 className="text-xl font-semibold mb-4">
                About Colorblindness
              </h2>
              <div className="prose max-w-none">
                <p>
                  Color blindness, or color vision deficiency, affects
                  approximately 1 in 12 men (8%) and 1 in 200 women (0.5%)
                  worldwide. It's a condition where people have difficulty
                  distinguishing certain colors, which can impact their daily
                  life in various ways, especially when interacting with digital
                  interfaces.
                </p>

                <h3 className="text-lg font-medium mt-6 mb-3">
                  Types of Color Blindness
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="border rounded-md p-4 bg-gray-50">
                    <h4 className="font-medium mb-2 text-red-700">
                      Deuteranopia
                    </h4>
                    <p className="text-sm">
                      The most common type, affecting about 6% of males. People
                      with deuteranopia have difficulty distinguishing between
                      red and green colors. Green appears more like beige, and
                      red looks more brownish.
                    </p>
                  </div>

                  <div className="border rounded-md p-4 bg-gray-50">
                    <h4 className="font-medium mb-2 text-amber-700">
                      Protanopia
                    </h4>
                    <p className="text-sm">
                      Affects about 1% of males. People with protanopia cannot
                      perceive red light, seeing reds as darker colors and often
                      confusing reds, greens, and yellows.
                    </p>
                  </div>

                  <div className="border rounded-md p-4 bg-gray-50">
                    <h4 className="font-medium mb-2 text-blue-700">
                      Tritanopia
                    </h4>
                    <p className="text-sm">
                      Very rare, affecting less than 0.01% of the population.
                      People with tritanopia have difficulty distinguishing blue
                      and yellow colors, and often see blues as green and
                      yellows as light gray or violet.
                    </p>
                  </div>
                </div>

                <h3 className="text-lg font-medium mt-6 mb-3">
                  Designing for Color Blind Users
                </h3>

                <ul className="list-disc pl-6 space-y-2">
                  <li>
                    Don't rely solely on color to convey information; use
                    patterns, labels, or icons alongside colors
                  </li>
                  <li>
                    Ensure sufficient contrast between text and background (at
                    least 4.5:1 ratio for normal text)
                  </li>
                  <li>
                    Use color combinations that are distinguishable by
                    colorblind users (avoid red/green or blue/purple
                    combinations)
                  </li>
                  <li>
                    Test your designs with colorblindness simulation tools like
                    this one
                  </li>
                  <li>Include text alternatives for color-coded information</li>
                </ul>

                <h3 className="text-lg font-medium mt-6 mb-3">
                  Safe Color Palettes
                </h3>

                <p className="mb-4">
                  Here are some colors that are generally distinguishable by
                  most people with color vision deficiencies:
                </p>

                <div className="flex flex-wrap gap-3 mb-6">
                  <div className="flex flex-col items-center">
                    <div
                      style={{ backgroundColor: "#004949" }}
                      className="w-12 h-12 rounded border mb-1"
                    ></div>
                    <div className="text-xs">#004949</div>
                  </div>
                  <div className="flex flex-col items-center">
                    <div
                      style={{ backgroundColor: "#009292" }}
                      className="w-12 h-12 rounded border mb-1"
                    ></div>
                    <div className="text-xs">#009292</div>
                  </div>
                  <div className="flex flex-col items-center">
                    <div
                      style={{ backgroundColor: "#ff6db6" }}
                      className="w-12 h-12 rounded border mb-1"
                    ></div>
                    <div className="text-xs">#ff6db6</div>
                  </div>
                  <div className="flex flex-col items-center">
                    <div
                      style={{ backgroundColor: "#ffb6db" }}
                      className="w-12 h-12 rounded border mb-1"
                    ></div>
                    <div className="text-xs">#ffb6db</div>
                  </div>
                  <div className="flex flex-col items-center">
                    <div
                      style={{ backgroundColor: "#490092" }}
                      className="w-12 h-12 rounded border mb-1"
                    ></div>
                    <div className="text-xs">#490092</div>
                  </div>
                  <div className="flex flex-col items-center">
                    <div
                      style={{ backgroundColor: "#006ddb" }}
                      className="w-12 h-12 rounded border mb-1"
                    ></div>
                    <div className="text-xs">#006ddb</div>
                  </div>
                  <div className="flex flex-col items-center">
                    <div
                      style={{ backgroundColor: "#b66dff" }}
                      className="w-12 h-12 rounded border mb-1"
                    ></div>
                    <div className="text-xs">#b66dff</div>
                  </div>
                  <div className="flex flex-col items-center">
                    <div
                      style={{ backgroundColor: "#6db6ff" }}
                      className="w-12 h-12 rounded border mb-1"
                    ></div>
                    <div className="text-xs">#6db6ff</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <footer className="bg-gray-800 text-white py-4">
        <div className="container mx-auto px-6 text-center">
          <p>
            ColorBlind Insight Tool - Making web design more accessible for
            everyone
          </p>
        </div>
      </footer>
    </div>
  );
}
'''