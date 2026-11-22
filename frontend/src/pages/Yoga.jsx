import { useState, useRef, useEffect, useCallback } from 'react';
import * as tf from '@tensorflow/tfjs';
import '@tensorflow/tfjs-backend-webgl';
import * as poseDetection from '@tensorflow-models/pose-detection';
import { getCorrections, drawSkeleton, countVisibleKeypoints } from '../utils/poseUtils';
import './Yoga.css';

export default function Yoga() {
  const [poses, setPoses] = useState([]);
  const [selectedPose, setSelectedPose] = useState(null);
  const [corrections, setCorrections] = useState([]);
  const [detectionStatus, setDetectionStatus] = useState('idle'); // 'idle' | 'no_body' | 'partial' | 'ok' | 'correcting'
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [modelReady, setModelReady] = useState(false);
  const [error, setError] = useState(null);
  const [imgError, setImgError] = useState(false);
  const [imgLoaded, setImgLoaded] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const detectorRef = useRef(null);
  const animFrameRef = useRef(null);
  const streamRef = useRef(null);

  // Load poses from backend
  useEffect(() => {
    fetch('/api/yoga/poses')
      .then((res) => res.json())
      .then(setPoses)
      .catch(() => setError('Failed to load yoga poses from server.'));
  }, []);

  // Pre-warm TF backend on mount
  useEffect(() => {
    const initTF = async () => {
      try {
        await tf.setBackend('webgl');
        await tf.ready();
        setModelReady(true);
      } catch {
        try {
          await tf.setBackend('cpu');
          await tf.ready();
          setModelReady(true);
        } catch (e) {
          setError('TensorFlow failed to initialize: ' + e.message);
        }
      }
    };
    initTF();
  }, []);

  const detectPose = useCallback(async () => {
    if (!detectorRef.current || !videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (video.readyState < 2) {
      animFrameRef.current = requestAnimationFrame(detectPose);
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    try {
      const detectedPoses = await detectorRef.current.estimatePoses(video);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(video, 0, 0);

      if (detectedPoses.length === 0) {
        // No person detected at all
        setDetectionStatus('no_body');
        setCorrections([]);
      } else if (selectedPose) {
        const keypoints = detectedPoses[0].keypoints;
        const visible = countVisibleKeypoints(keypoints);

        if (visible < 6) {
          // Person in frame but too few keypoints visible
          setDetectionStatus('partial');
          setCorrections([]);
        } else {
          const { corrections: newCorrections, anglesChecked, anglesDetected } = getCorrections(keypoints, selectedPose);

          if (anglesDetected === 0 && anglesChecked > 0) {
            // Keypoints exist but none relevant to this pose were visible
            setDetectionStatus('partial');
            setCorrections([]);
          } else if (newCorrections.length === 0) {
            setDetectionStatus('ok');
            setCorrections([]);
          } else {
            setDetectionStatus('correcting');
            setCorrections(newCorrections);
          }

          drawSkeleton(ctx, keypoints, canvas.width, canvas.height, newCorrections);
        }
      }
    } catch (e) {
      console.warn('Pose estimation error:', e);
    }

    animFrameRef.current = requestAnimationFrame(detectPose);
  }, [selectedPose]);

  const startCamera = async () => {
    setLoading(true);
    setError(null);
    setDetectionStatus('idle');

    // 1. Camera access
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      });
    } catch (err) {
      const msg =
        err.name === 'NotAllowedError'
          ? 'Camera permission denied. Please allow camera access in your browser settings and try again.'
          : err.name === 'NotFoundError'
          ? 'No camera found. Please connect a camera and try again.'
          : `Camera error: ${err.message}`;
      setError(msg);
      setLoading(false);
      return;
    }

    streamRef.current = stream;
    videoRef.current.srcObject = stream;

    try {
      await videoRef.current.play();
    } catch (err) {
      setError('Video playback failed: ' + err.message);
      stream.getTracks().forEach((t) => t.stop());
      setLoading(false);
      return;
    }

    // 2. Load MoveNet model (cached after first load)
    try {
      if (!detectorRef.current) {
        await tf.ready();
        detectorRef.current = await poseDetection.createDetector(
          poseDetection.SupportedModels.MoveNet,
          {
            modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING,
            enableSmoothing: true,
          }
        );
      }
    } catch (err) {
      setError('AI model failed to load: ' + err.message + '. Check your internet connection.');
      stream.getTracks().forEach((t) => t.stop());
      videoRef.current.srcObject = null;
      setLoading(false);
      return;
    }

    setIsRunning(true);
    setLoading(false);
    detectPose();
  };

  const stopCamera = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setIsRunning(false);
    setCorrections([]);
    setDetectionStatus('idle');
  };

  useEffect(() => {
    return () => stopCamera();
  }, []);

  const handlePoseSelect = (pose) => {
    setSelectedPose(pose);
    setImgError(false);
    setImgLoaded(false);
    setCorrections([]);
    setDetectionStatus('idle');
    if (isRunning) stopCamera();
  };

  // Status banner config
  const statusConfig = {
    idle: null,
    no_body:  { cls: 'status-warn',  text: '👤 No person detected — step back so your full body is visible' },
    partial:  { cls: 'status-warn',  text: '⚠️ Partial body detected — ensure good lighting and step further back' },
    ok:       { cls: 'status-good',  text: '✅ Great form! Hold this pose.' },
    correcting: null, // corrections list shown below
  };

  return (
    <div className="yoga-page">
      <h1 className="page-title">Yoga Pose Detection</h1>
      <p className="page-subtitle">
        Select a pose, study the reference image, then start your camera for real-time AI corrections.
      </p>

      {!modelReady && !error && (
        <div className="model-status">⚙️ Initializing AI engine...</div>
      )}

      <div className="yoga-layout">
        {/* ── Left panel ── */}
        <div className="pose-selector card">
          <h3>Select a Pose</h3>
          <div className="pose-list">
            {poses.map((pose) => (
              <button
                key={pose.id}
                className={`pose-btn ${selectedPose?.id === pose.id ? 'selected' : ''}`}
                onClick={() => handlePoseSelect(pose)}
              >
                {pose.name}
              </button>
            ))}
          </div>

          {selectedPose && (
            <div className="pose-info">
              <p className="pose-description">{selectedPose.description}</p>
              <div className="pose-instructions">
                <h4>📋 How to do it</h4>
                <ol>
                  {selectedPose.instructions.map((inst, i) => (
                    <li key={i}>{inst}</li>
                  ))}
                </ol>
              </div>
            </div>
          )}

          <div className="camera-controls">
            {!isRunning ? (
              <button
                className="btn-primary"
                onClick={startCamera}
                disabled={!selectedPose || loading || !modelReady}
              >
                {loading ? '⏳ Loading...' : modelReady ? '📷 Start Camera' : '⚙️ Initializing...'}
              </button>
            ) : (
              <button className="btn-secondary" onClick={stopCamera}>
                ⏹ Stop Camera
              </button>
            )}
          </div>
        </div>

        {/* ── Right panel ── */}
        <div className="camera-panel card">

          {/* Reference image — full size before camera, thumbnail during */}
          {selectedPose && (
            <div className={`pose-reference ${isRunning ? 'mini' : ''}`}>
              {!isRunning && <h3>📸 Reference Pose</h3>}
              <div className="pose-ref-container">
                {!imgError ? (
                  <>
                    {!imgLoaded && (
                      <div className="pose-ref-skeleton">
                        <div className="skeleton-shimmer" />
                        <span>Loading image...</span>
                      </div>
                    )}
                    <img
                      key={selectedPose.id}
                      src={selectedPose.image}
                      alt={`${selectedPose.name} reference`}
                      className={`pose-ref-img ${imgLoaded ? 'visible' : 'hidden'}`}
                      onLoad={() => setImgLoaded(true)}
                      onError={() => { setImgError(true); setImgLoaded(true); }}
                    />
                  </>
                ) : (
                  <div className="pose-ref-placeholder">
                    <span>🧘</span>
                    <p>{selectedPose.name}</p>
                  </div>
                )}
              </div>
              {!isRunning && (
                <p className="ref-hint">
                  Study the pose, then click <strong>Start Camera</strong> when ready!
                </p>
              )}
              {isRunning && (
                <p className="mini-label">Reference</p>
              )}
            </div>
          )}

          {/* Camera canvas */}
          <div className={`video-wrapper ${isRunning ? 'active' : ''}`}>
            <video ref={videoRef} className="yoga-video" playsInline muted />
            <canvas ref={canvasRef} className="yoga-canvas" />
            {!isRunning && !selectedPose && (
              <div className="camera-placeholder">
                <span>🧘</span>
                <p>Select a pose to begin</p>
              </div>
            )}
            {!isRunning && selectedPose && (
              <div className="camera-placeholder">
                <span>📷</span>
                <p>Click Start Camera when ready</p>
              </div>
            )}
          </div>

          {error && (
            <div className="error-box">
              <span>⚠️</span>
              <p>{error}</p>
            </div>
          )}

          {/* Detection status banner */}
          {isRunning && statusConfig[detectionStatus] && (
            <div className={`detection-status ${statusConfig[detectionStatus].cls}`}>
              {statusConfig[detectionStatus].text}
            </div>
          )}

          {/* Corrections panel */}
          <div className="corrections-panel">
            <h3>🤖 AI Corrections</h3>
            {!isRunning ? (
              <p className="correction-idle">Start camera to get real-time feedback.</p>
            ) : detectionStatus === 'no_body' || detectionStatus === 'partial' ? (
              <p className="correction-idle">
                Position yourself so your full body is visible in the camera.
              </p>
            ) : detectionStatus === 'ok' ? (
              <p className="correction-ok">✅ Perfect form! Hold this pose.</p>
            ) : corrections.length > 0 ? (
              <ul className="corrections-list">
                {corrections.map((c, i) => (
                  <li key={i} className="correction-item">
                    <span className="correction-icon">⚠️</span>
                    <div>
                      <strong>{c.joint.replace(/_/g, ' ')}</strong>
                      <div className="correction-detail">{c.message}</div>
                      <div className="correction-bar-wrap">
                        <div
                          className="correction-bar"
                          style={{ width: `${Math.min(100, Math.abs(c.current - c.target))}%` }}
                        />
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="correction-idle">Analyzing your pose...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
