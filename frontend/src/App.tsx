import { ChangeEvent, useEffect, useRef, useState } from 'react';
import './App.css';

type CheckedItems = {
  policy: boolean;
  terms: boolean;
  emails: boolean;
  cookies: boolean;
};

const messages: string[] = [
  'Analyzing face... ',
  'Checking credit score...',
  'Cross-checking your Google search history...',
  'Evaluating meme preferences...',
  'Detecting emotional instability...',
  'Connecting to refrigerator camera...',
  'Comparing with government database...',
];

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

function validateEmail(candidate: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(candidate);
}

const App = () => {
  const [checkedItems, setCheckedItems] = useState<CheckedItems>({
    policy: false,
    terms: false,
    emails: false,
    cookies: false,
  });
  const [accepted, setAccepted] = useState(false);
  const [selfieTaken, setSelfieTaken] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [finalMessage, setFinalMessage] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [selfieURL, setSelfieURL] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const allChecked = Object.values(checkedItems).every(Boolean);

  useEffect(() => {
    if (!accepted || selfieTaken) return;

    let stream: MediaStream | null = null;

    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((incomingStream) => {
        stream = incomingStream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      })
      .catch((err) => {
        console.error('Camera access denied:', err);
        setError('Unable to access the camera. Please grant permissions.');
      });

    return () => {
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, [accepted, selfieTaken]);

  const handleCheckboxChange = (name: keyof CheckedItems) => (event: ChangeEvent<HTMLInputElement>) => {
    const { checked } = event.target;
    setCheckedItems((prev) => ({ ...prev, [name]: checked }));
  };

  const handleAccept = () => {
    if (allChecked) setAccepted(true);
  };

  const handleTakeSelfie = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageDataURL = canvas.toDataURL('image/png');
    setSelfieURL(imageDataURL);
    setSelfieTaken(true);

    const stream = video.srcObject as MediaStream | null;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      video.srcObject = null;
    }
  };

  const startLoading = () => {
    setLoading(true);
    let i = 0;
    const interval = window.setInterval(() => {
      setLoadingMessage(messages[i % messages.length]);
      i += 1;
    }, 1000);
    return () => window.clearInterval(interval);
  };

  const handleSubmitEmailAndGetCode = async () => {
    setError('');
    setFinalMessage('');

    if (!email || !validateEmail(email)) {
      setError('Please enter a valid email address.');
      return;
    }

    if (!selfieURL) {
      setError('Please capture a selfie first.');
      return;
    }

    setSubmitting(true);
    const stopLoading = startLoading();

    try {
      const registerResponse = await fetch(`${BACKEND_URL}/api/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, selfieDataUrl: selfieURL }),
      });

      if (!registerResponse.ok) {
        throw new Error('Failed to register user');
      }

      const codeResponse = await fetch(`${BACKEND_URL}/api/generate-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!codeResponse.ok) {
        throw new Error('Failed to generate code');
      }

      const data = await codeResponse.json();
      const code = data?.code ?? '----';
      setFinalMessage(`✅ Your data has been stored. Here is the code: ${code}`);
    } catch (err) {
      console.error(err);
      setFinalMessage(
        '❌ We stored your data, but could not generate a code right now. Please contact support.',
      );
    } finally {
      stopLoading();
      setLoading(false);
      setSubmitting(false);
    }
  };

  return (
    <div className="app">
      <div className="card">
        <h1 className="title">🛡️ Zustimmung erforderlich</h1>
        <p className="subtitle">Bitte stimme allen Richtlinien zu, um fortzufahren.</p>

        {!accepted && (
          <div className="checkboxes">
            <label>
              <input
                type="checkbox"
                name="policy"
                checked={checkedItems.policy}
                onChange={handleCheckboxChange('policy')}
              />
              Datenschutzrichtlinie
            </label>
            <label>
              <input
                type="checkbox"
                name="terms"
                checked={checkedItems.terms}
                onChange={handleCheckboxChange('terms')}
              />
              Nutzungsbedingungen
            </label>
            <label>
              <input
                type="checkbox"
                name="emails"
                checked={checkedItems.emails}
                onChange={handleCheckboxChange('emails')}
              />
              Erhalt von E-Mails
            </label>
            <label>
              <input
                type="checkbox"
                name="cookies"
                checked={checkedItems.cookies}
                onChange={handleCheckboxChange('cookies')}
              />
              Cookies akzeptieren
            </label>
            <button className="primary" onClick={handleAccept} disabled={!allChecked}>
              ✅ Accept &amp; Continue
            </button>
          </div>
        )}

        {accepted && !selfieTaken && (
          <div className="selfie-section">
            <p>📸 Bitte mache ein Selfie, um fortzufahren:</p>
            <video ref={videoRef} autoPlay playsInline className="video" />
            <button className="primary" onClick={handleTakeSelfie}>
              📷 Take Selfie
            </button>
            <canvas ref={canvasRef} style={{ display: 'none' }} />
          </div>
        )}

        {selfieTaken && selfieURL && (
          <div className="preview-section">
            <p>📷 Dein Selfie wurde aufgenommen:</p>
            <img src={selfieURL} alt="Selfie Preview" className="selfie-preview" />
            <div className="email-section">
              <label htmlFor="email">Email for follow-up:</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                className="email-input"
              />
              <button className="primary" onClick={handleSubmitEmailAndGetCode} disabled={submitting}>
                {submitting ? 'Submitting…' : '✉️ Submit & Get Code'}
              </button>
              {error && <p className="error">{error}</p>}
            </div>
          </div>
        )}

        {loading && (
          <div className="loading-section">
            <div className="loader" />
            <p>{loadingMessage}</p>
          </div>
        )}

        {!loading && finalMessage && <div className="code">{finalMessage}</div>}
      </div>
    </div>
  );
};

export default App;
