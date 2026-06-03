import { useEffect } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useFormContext } from '../contexts/FormContext';
import { labelFor } from '../displayLabels';
import SummaryList from '../components/SummaryList';
import GovukButton from '../components/GovukButton';

/**
 * Check-your-answers page. Shows the five collected answers with a
 * Change link for each (links back to the question with
 * ?from=check-answers so Continue returns here). Redirects to the
 * first unanswered question if the user lands here mid-journey.
 */
export default function CheckAnswersPage() {
  const navigate = useNavigate();
  const { answers } = useFormContext();

  useEffect(() => {
    document.title = 'Check your answers - Green Home Grant - GOV.UK';
  }, []);

  // Guard: redirect to the first unanswered question
  if (!answers.propertyType) return <Navigate to="/property-type" replace />;
  if (!answers.ownership)    return <Navigate to="/ownership" replace />;
  if (!answers.incomeBand)   return <Navigate to="/income" replace />;
  if (!answers.insulation)   return <Navigate to="/insulation" replace />;
  if (!answers.heating)      return <Navigate to="/heating" replace />;

  const rows = [
    { key: 'Property type',           value: labelFor('propertyType', answers.propertyType), changeHref: '/property-type?from=check-answers', changeHiddenText: 'property type' },
    { key: 'Ownership status',        value: labelFor('ownership', answers.ownership),       changeHref: '/ownership?from=check-answers',     changeHiddenText: 'ownership status' },
    { key: 'Annual household income', value: labelFor('incomeBand', answers.incomeBand),     changeHref: '/income?from=check-answers',        changeHiddenText: 'annual household income' },
    { key: 'Current insulation',      value: labelFor('insulation', answers.insulation),     changeHref: '/insulation?from=check-answers',    changeHiddenText: 'current insulation' },
    { key: 'Current heating system',  value: labelFor('heating', answers.heating),           changeHref: '/heating?from=check-answers',       changeHiddenText: 'current heating system' },
  ];

  return (
    <>
      <Link to="/heating" className="govuk-back-link">Back</Link>

      <h1 className="govuk-heading-xl">Check your answers</h1>
      <p className="govuk-body">Check your answers before you find out if you are eligible.</p>

      <SummaryList rows={rows} />

      <h2 className="govuk-heading-m">Now find out if you are eligible</h2>

      <GovukButton onClick={() => navigate('/result')}>Submit and see result</GovukButton>
    </>
  );
}
