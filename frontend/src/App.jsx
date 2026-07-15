import { useState } from "react";

const API_BASE_URL = "http://localhost:8000/api/v1";

async function request(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.message ?? data.detail ?? "Something went wrong.");
  }

  return data;
}

export default function App() {
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState("email");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleEmailSubmit(event) {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const data = await request("/password/forgot-password", { email });
      setMessage(data.message);
      setStep("otp");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleOtpSubmit(event) {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const data = await request("/password/verify-otp", { email, otp });
      setMessage(data.message);
      setStep("complete");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="card" aria-labelledby="page-title">
        <p className="eyebrow">Enterprise IT Operations</p>
        <h1 id="page-title">Reset your password</h1>

        {step === "email" && (
          <form onSubmit={handleEmailSubmit}>
            <p className="description">Enter your work email to receive a verification code.</p>
            <label htmlFor="email">Work email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@company.com"
              required
              autoComplete="email"
            />
            <button type="submit" disabled={isLoading}>
              {isLoading ? "Sending…" : "Send verification code"}
            </button>
          </form>
        )}

        {step === "otp" && (
          <form onSubmit={handleOtpSubmit}>
            <p className="description">{message} Enter the code sent to <strong>{email}</strong>.</p>
            <label htmlFor="otp">Verification code</label>
            <input
              id="otp"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength="6"
              value={otp}
              onChange={(event) => setOtp(event.target.value.replace(/\D/g, ""))}
              placeholder="123456"
              required
              autoComplete="one-time-code"
            />
            <button type="submit" disabled={isLoading || otp.length !== 6}>
              {isLoading ? "Verifying…" : "Verify code"}
            </button>
            <button className="text-button" type="button" onClick={() => setStep("email")}>
              Use a different email
            </button>
          </form>
        )}

        {step === "complete" && <p className="success">{message}</p>}
        {error && <p className="error" role="alert">{error}</p>}
      </section>
    </main>
  );
}
