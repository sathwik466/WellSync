import { useState, useRef, useEffect, useCallback } from 'react';
import * as faceapi from 'face-api.js';
import './Movies.css';

const MOODS = [
  { id: 'happy', label: 'Happy', emoji: '😊', color: '#10b981' },
  { id: 'sad', label: 'Sad', emoji: '😢', color: '#6366f1' },
  { id: 'angry', label: 'Angry', emoji: '😠', color: '#ef4444' },
  { id: 'fear', label: 'Fear', emoji: '😨', color: '#8b5cf6' },
  { id: 'surprise', label: 'Surprise', emoji: '😲', color: '#f59e0b' },
  { id: 'neutral', label: 'Neutral', emoji: '😐', color: '#64748b' },
  { id: 'disgust', label: 'Disgust', emoji: '🤢', color: '#14b8a6' },
];

export default function Movies() {
  const [detectedMood, setDetectedMood] = useState(null);
  const [selectedMood, setSelectedMood] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const [error, setError] = useState(null);
  const [posterOnlyMode, setPosterOnlyMode] = useState(false);
  const [activeMovie, setActiveMovie] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    const loadModels = async () => {
      try {
        const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model';
        await Promise.all([
          faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
          faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
        ]);
        setModelsLoaded(true);
      } catch {
        setError('Face detection models could not be loaded from CDN. You can select moods directly below.');
      }
    };
    loadModels();
  }, []);

  const detectMood = useCallback(async () => {
    if (!videoRef.current || !modelsLoaded) return;

    try {
      const detections = await faceapi
        .detectSingleFace(videoRef.current, new faceapi.TinyFaceDetectorOptions())
        .withFaceExpressions();

      if (detections) {
        const expressions = detections.expressions;
        const mood = Object.entries(expressions).reduce(
          (best, [key, val]) => (val > best.val ? { mood: key, val } : best),
          { mood: 'neutral', val: 0 }
        );
        setDetectedMood(mood.mood);

        if (canvasRef.current && videoRef.current) {
          const canvas = canvasRef.current;
          const displaySize = { width: videoRef.current.videoWidth, height: videoRef.current.videoHeight };
          faceapi.matchDimensions(canvas, displaySize);
          const resized = faceapi.resizeResults(detections, displaySize);
          const ctx = canvas.getContext('2d');
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          faceapi.draw.drawDetections(canvas, resized);
        }
      }
    } catch {
      // Ignore frame detection drop
    }
  }, [modelsLoaded]);

  const startCamera = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 480, height: 360, facingMode: 'user' },
      });
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      setIsRunning(true);
      intervalRef.current = setInterval(detectMood, 500);
    } catch {
      setError('Camera access denied or unavailable. You can click any mood button below to view visual recommendations.');
    }
  };

  const stopCamera = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (videoRef.current?.srcObject) {
      videoRef.current.srcObject.getTracks().forEach((t) => t.stop());
      videoRef.current.srcObject = null;
    }
    setIsRunning(false);
    setDetectedMood(null);
  };

  const fetchRecommendations = async (mood) => {
    if (!mood) return;
    setLoading(true);
    setError(null);
    setSelectedMood(mood);
    try {
      const res = await fetch('/api/movies/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mood }),
      });
      const data = await res.json();
      setRecommendations(data);
    } catch {
      setError('Failed to fetch recommendations from the server.');
    } finally {
      setLoading(false);
    }
  };

  const handleGetRecommendationsFromCamera = () => {
    if (detectedMood) {
      fetchRecommendations(detectedMood);
    }
  };

  useEffect(() => {
    // Load initial mood recommendations on page load
    fetchRecommendations('happy');
    return () => stopCamera();
  }, []);

  const activeMoodInfo = MOODS.find((m) => m.id === (selectedMood || detectedMood || 'happy'));

  return (
    <div className="movies-page">
      <div className="movies-header">
        <h1 className="page-title">Visual Movie Recommendations</h1>
        <p className="page-subtitle">
          Powered by <strong>The Movie Database (TMDb)</strong>. Detect mood via webcam or click a mood pill to browse cinema visually through poster artwork.
        </p>
      </div>

      <div className="movies-layout">
        {/* Left Column: Mood Detection & Manual Selectors */}
        <div className="mood-sidebar">
          <div className="card mood-detector">
            <h3>Facial Mood Detection</h3>

            <div className="video-wrapper">
              <video ref={videoRef} className="mood-video" playsInline muted />
              <canvas ref={canvasRef} className="mood-canvas" />
              {!isRunning && (
                <div className="camera-placeholder">
                  <span className="camera-icon">📷</span>
                  <p>Webcam preview will appear here</p>
                </div>
              )}
            </div>

            <div className="mood-display">
              {detectedMood ? (
                <>
                  <span className="mood-emoji">
                    {MOODS.find((m) => m.id === detectedMood)?.emoji || '😐'}
                  </span>
                  <div className="mood-details">
                    <span className="mood-sub">Live Expression</span>
                    <strong className="mood-label">{detectedMood}</strong>
                  </div>
                </>
              ) : (
                <span className="mood-label-muted">
                  {isRunning ? 'Looking for a face...' : 'Camera is off'}
                </span>
              )}
            </div>

            <div className="mood-controls">
              {!isRunning ? (
                <button
                  type="button"
                  className="primary"
                  onClick={startCamera}
                  disabled={!modelsLoaded}
                >
                  {modelsLoaded ? 'Start Camera' : 'Loading models...'}
                </button>
              ) : (
                <button type="button" className="secondary" onClick={stopCamera}>
                  Stop Camera
                </button>
              )}
              <button
                type="button"
                className="accent-btn"
                onClick={handleGetRecommendationsFromCamera}
                disabled={!detectedMood || loading}
              >
                {loading ? 'Finding movies...' : 'Recommend for My Face'}
              </button>
            </div>

            {error && <p className="error-msg">{error}</p>}
          </div>

          {/* Quick Mood Pills */}
          <div className="card mood-pills-card">
            <h3>Select Mood Directly</h3>
            <p className="pills-hint">Click any emotion to explore its TMDb visual collection:</p>
            <div className="mood-pills-grid">
              {MOODS.map((m) => {
                const isActive = (selectedMood || detectedMood) === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    className={`mood-pill ${isActive ? 'active' : ''}`}
                    onClick={() => fetchRecommendations(m.id)}
                    disabled={loading}
                  >
                    <span className="pill-emoji">{m.emoji}</span>
                    <span className="pill-name">{m.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Visual Movie Showcase */}
        <div className="recommendations-container card">
          <div className="rec-header">
            <div className="rec-title-group">
              <h3>
                Recommended Cinema{' '}
                {activeMoodInfo && (
                  <span className="rec-mood-badge">
                    {activeMoodInfo.emoji} {activeMoodInfo.label}
                  </span>
                )}
              </h3>
              {recommendations && (
                <p className="rec-message">{recommendations.message}</p>
              )}
            </div>

            <div className="view-mode-toggle">
              <span className="toggle-label">Browse:</span>
              <button
                type="button"
                className={`toggle-btn ${posterOnlyMode ? 'active' : ''}`}
                onClick={() => setPosterOnlyMode(true)}
                title="Visual Poster View: Explore purely by posters without name text"
              >
                🖼️ Poster Art
              </button>
              <button
                type="button"
                className={`toggle-btn ${!posterOnlyMode ? 'active' : ''}`}
                onClick={() => setPosterOnlyMode(false)}
                title="Standard Card View: Shows posters with title and details"
              >
                📋 Card Details
              </button>
            </div>
          </div>

          {loading ? (
            <div className="loading-state">
              <div className="spinner" />
              <p>Fetching curated visual picks from TMDb...</p>
            </div>
          ) : !recommendations ? (
            <div className="placeholder-box">
              <p>Detect your mood or pick an emotion above to view movies visually.</p>
            </div>
          ) : (
            <div className={`movie-grid ${posterOnlyMode ? 'poster-only-view' : 'detail-view'}`}>
              {recommendations.movies.map((movie, i) => (
                <div
                  key={movie.id || i}
                  className="movie-poster-card"
                  onClick={() => setActiveMovie(movie)}
                >
                  <div className="poster-wrapper">
                    <img
                      src={movie.poster_url}
                      alt={movie.title}
                      className="poster-img"
                      loading="lazy"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                    <div className="poster-fallback" style={{ display: 'none' }}>
                      <span className="fallback-icon">🎬</span>
                      <span className="fallback-title">{movie.title}</span>
                      <span className="fallback-genre">{movie.genre}</span>
                    </div>

                    <div className="poster-overlay-top">
                      <span className="movie-rank-badge">#{i + 1}</span>
                      {movie.vote_average > 0 && (
                        <span className="movie-rating-badge">
                          ⭐ {movie.vote_average}
                        </span>
                      )}
                    </div>

                    {/* Visual Hover Sheet */}
                    <div className="poster-hover-sheet">
                      <h4 className="hover-title">{movie.title}</h4>
                      <p className="hover-meta">
                        {movie.year} &middot; {movie.genre}
                      </p>
                      <p className="hover-overview">{movie.overview}</p>
                      <span className="hover-cta">Click for full details &rarr;</span>
                    </div>
                  </div>

                  {!posterOnlyMode && (
                    <div className="movie-card-footer">
                      <h4 className="movie-card-title" title={movie.title}>
                        {movie.title}
                      </h4>
                      <div className="movie-card-sub">
                        <span className="movie-card-year">{movie.year}</span>
                        <span className="movie-card-genre">{movie.genre}</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Movie Details Modal / Lightbox */}
      {activeMovie && (
        <div className="movie-modal-backdrop" onClick={() => setActiveMovie(null)}>
          <div className="movie-modal-content" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              className="modal-close-btn"
              onClick={() => setActiveMovie(null)}
            >
              &times;
            </button>

            {activeMovie.backdrop_url && (
              <div
                className="modal-backdrop-banner"
                style={{ backgroundImage: `url(${activeMovie.backdrop_url})` }}
              >
                <div className="modal-banner-gradient" />
              </div>
            )}

            <div className="modal-body">
              <div className="modal-poster-col">
                <img
                  src={activeMovie.poster_url}
                  alt={activeMovie.title}
                  className="modal-poster-img"
                />
              </div>

              <div className="modal-info-col">
                <div className="modal-title-row">
                  <h2>{activeMovie.title}</h2>
                  {activeMovie.vote_average > 0 && (
                    <span className="modal-rating">⭐ {activeMovie.vote_average} / 10</span>
                  )}
                </div>

                <div className="modal-meta-row">
                  <span className="meta-tag year">{activeMovie.year}</span>
                  <span className="meta-tag genre">{activeMovie.genre}</span>
                </div>

                <div className="modal-section">
                  <h5>Storyline</h5>
                  <p className="modal-overview">{activeMovie.overview}</p>
                </div>

                <div className="modal-actions">
                  {activeMovie.tmdb_url && (
                    <a
                      href={activeMovie.tmdb_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="tmdb-external-link"
                    >
                      View on TMDb &rarr;
                    </a>
                  )}
                  <button
                    type="button"
                    className="modal-dismiss-btn"
                    onClick={() => setActiveMovie(null)}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
