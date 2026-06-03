import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { FormProvider } from './contexts/FormContext';
import SkipLink from './components/SkipLink';
import GovukHeader from './components/GovukHeader';
import PhaseBanner from './components/PhaseBanner';
import GovukFooter from './components/GovukFooter';
import AppRoutes from './router';
import './App.css';

/**
 * Application shell for the Green Home Grant eligibility checker.
 *
 * Renders the standard GOV.UK page chrome (skip link, header, phase
 * banner, footer) around the route table. On every route change,
 * focus moves to the <main> landmark so screen readers and keyboard
 * users get a predictable starting position. The skip link is the
 * first focusable element and targets <main id="main-content">.
 *
 * App state (the five answers) lives in FormProvider so any route
 * can read or update it without prop drilling.
 */
function App() {
  const mainRef = useRef(null);
  const { pathname } = useLocation();

  useEffect(() => {
    mainRef.current?.focus();
  }, [pathname]);

  return (
    <FormProvider>
      <SkipLink />
      <GovukHeader />
      <PhaseBanner phase="alpha" feedbackHref="#" />
      <div className="govuk-width-container">
        <main
          id="main-content"
          className="govuk-main-wrapper"
          role="main"
          ref={mainRef}
          tabIndex={-1}
        >
          <AppRoutes />
        </main>
      </div>
      <GovukFooter />
    </FormProvider>
  );
}

export default App;
