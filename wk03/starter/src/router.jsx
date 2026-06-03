import { Routes, Route } from 'react-router-dom';
import StartPage from './pages/StartPage';
import PropertyTypePage from './pages/PropertyTypePage';
import OwnershipPage from './pages/OwnershipPage';
import IncomePage from './pages/IncomePage';
import InsulationPage from './pages/InsulationPage';
import HeatingPage from './pages/HeatingPage';
import CheckAnswersPage from './pages/CheckAnswersPage';
import ResultPage from './pages/ResultPage';
import AccessibilityStatementPage from './pages/AccessibilityStatementPage';

/**
 * Route table for the Green Home Grant eligibility checker.
 * Mounted by App.jsx inside the BrowserRouter set up in main.jsx.
 */
export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<StartPage />} />
      <Route path="/property-type" element={<PropertyTypePage />} />
      <Route path="/ownership" element={<OwnershipPage />} />
      <Route path="/income" element={<IncomePage />} />
      <Route path="/insulation" element={<InsulationPage />} />
      <Route path="/heating" element={<HeatingPage />} />
      <Route path="/check-answers" element={<CheckAnswersPage />} />
      <Route path="/result" element={<ResultPage />} />
      <Route path="/accessibility-statement" element={<AccessibilityStatementPage />} />
    </Routes>
  );
}
