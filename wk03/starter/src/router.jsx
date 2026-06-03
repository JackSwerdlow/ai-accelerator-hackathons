/**
 * Route table for the Green Home Grant eligibility checker.
 * Declares all 10 routes (the 9 in PLAN.md §4.5 plus the tenant-path
 * /landlord-consent question from content plan §11) in a single <Routes>
 * tree so App.jsx stays focused on chrome and provider wiring.
 */
import { Routes, Route } from "react-router-dom";
import StartPage from "./pages/StartPage";
import PropertyTypePage from "./pages/PropertyTypePage";
import OwnershipPage from "./pages/OwnershipPage";
import LandlordConsentPage from "./pages/LandlordConsentPage";
import IncomePage from "./pages/IncomePage";
import InsulationPage from "./pages/InsulationPage";
import HeatingPage from "./pages/HeatingPage";
import CheckAnswersPage from "./pages/CheckAnswersPage";
import ResultPage from "./pages/ResultPage";
import AccessibilityStatementPage from "./pages/AccessibilityStatementPage";

/**
 * Renders the 10 application routes (PLAN.md §4.5 + content plan §11).
 *
 * @returns {JSX.Element}
 */
export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<StartPage />} />
      <Route path="/property-type" element={<PropertyTypePage />} />
      <Route path="/ownership" element={<OwnershipPage />} />
      <Route path="/landlord-consent" element={<LandlordConsentPage />} />
      <Route path="/income" element={<IncomePage />} />
      <Route path="/insulation" element={<InsulationPage />} />
      <Route path="/heating" element={<HeatingPage />} />
      <Route path="/check-answers" element={<CheckAnswersPage />} />
      <Route path="/result" element={<ResultPage />} />
      <Route path="/accessibility-statement" element={<AccessibilityStatementPage />} />
    </Routes>
  );
}
