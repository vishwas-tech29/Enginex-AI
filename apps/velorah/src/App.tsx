import { FormEvent, useEffect, useState } from "react";
import { ApiError, APP_URL, landingApi, PlanPricing, PlanTier } from "./api/landingApi";

const TIER_LABELS: Record<PlanTier, string> = {
  free: "Free",
  hobbyist: "Hobbyist",
  professional: "Professional",
  enterprise: "Enterprise",
};

export default function App() {
  const [plans, setPlans] = useState<PlanPricing[] | null>(null);
  const [pricingError, setPricingError] = useState<string | null>(null);
  const [signupTier, setSignupTier] = useState<PlanTier | null>(null);

  useEffect(() => {
    void landingApi.trackEvent("page_view", { page: "landing" });
    void landingApi.trackEvent("hero_visible");

    landingApi
      .getPricing()
      .then((data) => {
        setPlans(data.plans);
        void landingApi.trackEvent("pricing_visible");
      })
      .catch((err) => setPricingError(err instanceof Error ? err.message : "Failed to load pricing"));
  }, []);

  function handleCTA(tier: PlanTier) {
    void landingApi.trackEvent("cta_clicked", { tier });
    setSignupTier(tier);
  }

  return (
    <div className="min-h-screen">
      <Hero onGetStarted={() => handleCTA("hobbyist")} />
      <Pricing plans={plans} error={pricingError} onSelectTier={handleCTA} />
      <Footer />
      {signupTier && <SignupModal planTier={signupTier} onClose={() => setSignupTier(null)} />}
    </div>
  );
}

function Hero({ onGetStarted }: { onGetStarted: () => void }) {
  return (
    <section className="mx-auto max-w-4xl px-6 py-24 text-center">
      <h1
        className="text-5xl font-normal tracking-tight sm:text-6xl"
        style={{ fontFamily: "'Instrument Serif', serif" }}
      >
        Design hardware, faster.
      </h1>
      <p className="mx-auto mt-6 max-w-2xl text-lg text-white/60">
        Velorah is the AI-native engineering platform for CAD, PCB, and simulation —
        real-time collaboration, an AI copilot, and a parametric solid modeling engine
        in your browser.
      </p>
      <div className="mt-10 flex justify-center gap-4">
        <button
          type="button"
          onClick={onGetStarted}
          className="rounded-full bg-white/10 px-8 py-3 font-medium text-white ring-1 ring-white/20 backdrop-blur transition hover:scale-[1.02] hover:bg-white/15"
        >
          Start building
        </button>
      </div>
    </section>
  );
}

function Pricing({
  plans,
  error,
  onSelectTier,
}: {
  plans: PlanPricing[] | null;
  error: string | null;
  onSelectTier: (tier: PlanTier) => void;
}) {
  return (
    <section className="mx-auto max-w-6xl px-6 py-16">
      <h2 className="text-center text-3xl" style={{ fontFamily: "'Instrument Serif', serif" }}>
        Pricing
      </h2>

      {error && <p className="mt-6 text-center text-sm text-red-400">{error}</p>}
      {!plans && !error && <p className="mt-6 text-center text-sm text-white/50">Loading plans…</p>}

      {plans && (
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {plans.map((plan) => (
            <div
              key={plan.tier}
              className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 backdrop-blur"
            >
              <h3 className="text-lg font-medium">{TIER_LABELS[plan.tier]}</h3>
              <p className="mt-2 text-3xl">
                {plan.is_custom ? (
                  "Custom"
                ) : (
                  <>
                    ${plan.price_monthly}
                    <span className="text-sm text-white/50">/mo</span>
                  </>
                )}
              </p>
              <ul className="mt-4 space-y-1 text-sm text-white/60">
                <li>{formatLimit(plan.features.projects_limit, "project")}</li>
                <li>{formatLimit(plan.features.storage_gb, "GB storage")}</li>
                <li>{plan.features.ai_suggestions ? "AI suggestions" : "No AI suggestions"}</li>
              </ul>
              <button
                type="button"
                onClick={() => onSelectTier(plan.tier)}
                className="mt-6 w-full rounded-full bg-white/10 px-4 py-2 text-sm font-medium ring-1 ring-white/20 transition hover:bg-white/15"
              >
                {plan.tier === "enterprise" ? "Contact sales" : "Get started"}
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function formatLimit(value: number | null, unit: string): string {
  return value === null ? `Unlimited ${unit}s` : `${value} ${unit}${value === 1 ? "" : "s"}`;
}

function Footer() {
  return (
    <footer className="border-t border-white/10 py-10 text-center text-xs text-white/40">
      Velorah — an Enginex AI product ·{" "}
      <a href="mailto:support@velorah.io" className="text-white/60">
        support@velorah.io
      </a>
    </footer>
  );
}

type SignupStep = "account" | "age" | "done";

function SignupModal({ planTier, onClose }: { planTier: PlanTier; onClose: () => void }) {
  const [step, setStep] = useState<SignupStep>("account");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [company, setCompany] = useState("");
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [checkoutUrl, setCheckoutUrl] = useState<string | null>(null);
  const [birthYear, setBirthYear] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAccountSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      void landingApi.trackEvent("signup_started", { tier: planTier });
      const response = await landingApi.signup({
        email,
        password,
        name: fullName,
        plan_tier: planTier,
        company: company || undefined,
        referral_source: "landing_page",
      });
      setAccessToken(response.access_token);
      setCheckoutUrl(response.checkout_url);
      void landingApi.trackEvent("signup_completed", { tier: planTier });
      setStep("age");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Signup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleAgeSubmit(e: FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    try {
      await landingApi.verifyAge(accessToken, Number(birthYear));
      finish();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Age verification failed.");
    } finally {
      setLoading(false);
    }
  }

  function finish() {
    setStep("done");
    if (checkoutUrl) {
      window.location.href = checkoutUrl;
      return;
    }
    window.location.href = `${APP_URL}/login?email=${encodeURIComponent(email)}`;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#0d0f1a] p-8">
        <h2 className="text-2xl" style={{ fontFamily: "'Instrument Serif', serif" }}>
          {step === "account" && `Start your ${TIER_LABELS[planTier]} plan`}
          {step === "age" && "Confirm your age"}
          {step === "done" && "You're all set"}
        </h2>

        {step === "account" && (
          <form onSubmit={handleAccountSubmit} className="mt-6 space-y-4">
            <Field label="Full name" value={fullName} onChange={setFullName} required />
            <Field label="Email" type="email" value={email} onChange={setEmail} required />
            <Field
              label="Password"
              type="password"
              value={password}
              onChange={setPassword}
              required
              minLength={8}
            />
            <Field label="Company (optional)" value={company} onChange={setCompany} />
            {error && <p className="text-sm text-red-400">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-white/10 px-6 py-3 font-medium ring-1 ring-white/20 transition hover:scale-[1.01] hover:bg-white/15 disabled:opacity-50"
            >
              {loading ? "Creating account…" : "Continue"}
            </button>
          </form>
        )}

        {step === "age" && (
          <form onSubmit={handleAgeSubmit} className="mt-6 space-y-4">
            <p className="text-sm text-white/60">
              Velorah requires account holders to be 18 or older. What year were you born?
            </p>
            <Field
              label="Birth year"
              type="number"
              value={birthYear}
              onChange={setBirthYear}
              required
              min={1900}
              max={2100}
            />
            {error && <p className="text-sm text-red-400">{error}</p>}
            <button
              type="submit"
              disabled={loading || birthYear.length !== 4}
              className="w-full rounded-full bg-white/10 px-6 py-3 font-medium ring-1 ring-white/20 transition hover:scale-[1.01] hover:bg-white/15 disabled:opacity-50"
            >
              {loading ? "Verifying…" : "Confirm"}
            </button>
            <button
              type="button"
              onClick={finish}
              className="w-full text-xs text-white/40 hover:text-white/60"
            >
              Skip for now
            </button>
          </form>
        )}

        <button
          type="button"
          onClick={onClose}
          className="mt-4 w-full text-sm text-white/40 transition hover:text-white/70"
        >
          Close
        </button>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  required,
  minLength,
  min,
  max,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
  minLength?: number;
  min?: number;
  max?: number;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-medium text-white/80">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        minLength={minLength}
        min={min}
        max={max}
        className="w-full rounded-lg border border-white/15 bg-white/5 px-4 py-2 text-white outline-none focus:border-white/40"
      />
    </label>
  );
}
