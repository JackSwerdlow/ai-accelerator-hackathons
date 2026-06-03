/**
 * Tenant-path question: landlord permission. Shown only to renters after the
 * ownership branch. Thin wrapper around <QuestionPage> per content plan §11.
 */
import QuestionPage from "../components/QuestionPage";
import { totalSteps } from "../flow";

const OPTIONS = [
  { value: "yes", label: "Yes" },
  { value: "no", label: "No" },
  { value: "not-sure", label: "Not sure" },
];

/**
 * Renders the "Do you have your landlord's permission to make energy
 * efficiency improvements?" question (step 3 on the tenant path), with a
 * help-details disclosure explaining why permission is needed.
 *
 * @returns {JSX.Element}
 */
export default function LandlordConsentPage() {
  return (
    <QuestionPage
      pageTitle="Do you have your landlord's permission to make energy efficiency improvements?"
      fieldName="landlordConsent"
      step={3}
      totalSteps={totalSteps}
      options={OPTIONS}
      hint="The work is paid for by the grant, but your landlord must agree to it because they own the property."
      helpDetails={{
        summaryText: "Why we need to know about landlord permission",
        bodyText:
          "Energy efficiency improvements like insulation and heat pumps are fixed to the property, so the owner has to agree before they can be installed. If you are not sure, you can still continue and we will tell you how to ask your landlord.",
      }}
      errorMessage="Select whether you have your landlord's permission"
      backHref="/ownership"
      onContinueNavigateTo="/insulation"
    />
  );
}
