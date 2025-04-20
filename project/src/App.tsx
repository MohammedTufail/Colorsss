import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import HomePage from "./components/HomePage";
import ColorDetector from "./components/ColorDetector";
import LiveDetection from "./components/LiveDetection";
import ColorAccessibilityAnalyzer from "./components/ColorAccessibilityAnalyzer";// Import LiveDetection
import PaletteExtractor from "./components/PaletteExtractor";// Import LiveDetection


function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="/detect-color" element={<ColorDetector />} />
          <Route path="/live" element={<LiveDetection />} />
          <Route path="/api/upload" element={<ColorAccessibilityAnalyzer />} />
          <Route path="extract_palette" element={<PaletteExtractor />} />
          {/* Other routes will be added as we implement more features */}
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
