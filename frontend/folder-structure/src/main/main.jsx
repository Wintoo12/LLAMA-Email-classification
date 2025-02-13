import { useState } from "react";
import styles from "./main.module.css";

const EmailAnalyzer = () => {
  const [email, setEmail] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeEmail = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch("http://localhost:5000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Analysis failed");
      }

      setResult(data.result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.emailArea}>
        <textarea
          className={styles.emailInput}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Paste your email content here..."
          disabled={loading}
        />
        <button
          className={styles.analyzeButton}
          onClick={analyzeEmail}
          disabled={loading || !email.trim()}
        >
          Analyze
        </button>
        {error}

        {result && (
          <div className={styles.resultArea}>
            <h3 className={styles.AnalysisResults}>Analysis Results:</h3>
            <div className={styles.pre}>{result}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailAnalyzer;
