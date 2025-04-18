import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import HomePage from "./components/HomePage";
import ColorDetector from "./components/ColorDetector";
import LiveDetection from "./components/LiveDetection"; // Import LiveDetection

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="/detect-color" element={<ColorDetector />} />
          <Route path="/live" element={<LiveDetection />} />
          {/* Other routes will be added as we implement more features */}
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
