/**
 * Application shell: wraps the route tree in FormProvider, mounts the
 * GOV.UK chrome (skip link / header / phase banner / footer), and moves
 * keyboard focus to <main> on every route change per PLAN.md §6.4.
 */
import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { FormProvider } from "./contexts/FormContext";
import SkipLink from "./components/SkipLink";
import GovukHeader from "./components/GovukHeader";
import PhaseBanner from "./components/PhaseBanner";
import GovukFooter from "./components/GovukFooter";
import AppRoutes from "./router";

/**
 * Top-level App component. Owns the shared form state via FormProvider,
 * renders persistent chrome around the routed page, and focuses the
 * <main> element whenever the route changes so screen readers and
 * keyboard users land in the new page content.
 *
 * @returns {JSX.Element}
 */
export default function App() {
  const mainRef = useRef(null);
  const { pathname } = useLocation();
  useEffect(() => {
    mainRef.current?.focus();
  }, [pathname]);

  return (
    <FormProvider>
      <SkipLink />
      <GovukHeader />
      <PhaseBanner phase="alpha" feedbackHref="/feedback" />
      <div className="govuk-width-container">
        <main
          id="main-content"
          className="govuk-main-wrapper"
          role="main"
          ref={mainRef}
          tabIndex={-1}
          key={pathname}
        >
          <AppRoutes />
        </main>
      </div>
      <GovukFooter />
    </FormProvider>
  );
}
