import { Routes, Route } from 'react-router-dom';
import GovukHeader from './components/GovukHeader';
// TODO: Mount PhaseBanner below GovukHeader — import PhaseBanner from './components/PhaseBanner';
// TODO: Mount GovukFooter after the closing </main> — import GovukFooter from './components/GovukFooter';
import StartPage from './pages/StartPage';
import PropertyTypePage from './pages/PropertyTypePage';
import OwnershipPage from './pages/OwnershipPage';
import IncomePage from './pages/IncomePage';
import InsulationPage from './pages/InsulationPage';
import HeatingPage from './pages/HeatingPage';
import CheckAnswersPage from './pages/CheckAnswersPage';
import ResultPage from './pages/ResultPage';
import AccessibilityStatementPage from './pages/AccessibilityStatementPage';

function App() {
  // TODO: Add form state here (useState) to hold all question answers
  // TODO: Pass state and setter to each page component via props

  return (
    <>
      <GovukHeader />
      {/* TODO: Add <PhaseBanner phase="alpha" feedbackHref="#" /> here */}
      <div className="govuk-width-container">
        <main className="govuk-main-wrapper" role="main">
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
        </main>
      </div>
      {/* TODO: Add <GovukFooter /> here */}
    </>
  );
}

export default App;
