import { useState, useRef, useEffect, useCallback } from 'react';
import * as poseDetection from '@tensorflow-models/pose-detection';
import '@tensorflow/tfjs-backend-webgl';
import { getCorrections, drawSkeleton } from '../utils/poseUtils';
import './Yoga.css';

export default function Yoga() {
  const [poses, setPoses] = useState([]);
  const [selectedPose, setSelectedPose] = useState(null);
  const [corrections, setCorrections] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const detectorRef = useRef(null);
  const animFrameRef = useRef(null);

  useEffect(() => {
    fetch('/api/yoga/poses')
      .then((res) => res.json())
      .then(setPoses)
      .catch(() => setError('Failed to load yoga poses'));
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

    const detectedPoses = await detectorRef.current.estimatePoses(video);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(video, 0, 0);

    if (detectedPoses.length > 0 && selectedPose) {
      const keypoints = detectedPoses[0].keypoints;
      const newCorrections = getCorrections(keypoints, selectedPose);
      setCorrections(newCorrections);
      drawSkeleton(ctx, keypoints, canvas.width, canvas.height, newCorrections);
    }

    animFrameRef.current = requestAnimationFrame(detectPose);
  }, [selectedPose]);

  const startCamera = async () => {
    setLoading(true);
    setError(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
      });
      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      const detector = await poseDetection.createDetector(
        poseDetection.SupportedModels.MoveNet,
        { modelType: poseDetection.movenet.modelType.SINGLEPOSE_THUNDER }
      );
      detectorRef.current = detector;
      setIsRunning(true);
      detectPose();
    } catch (err) {
      setError('Camera access denied or model failed to load. Please allow camera permissions.');
    } finally {
      setLoading(false);
    }
  };

  const stopCamera = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (videoRef.current?.srcObject) {
      videoRef.current.srcObject.getTracks().forEach((t) => t.stop());
      videoRef.current.srcObject = null;
    }
    detectorRef.current = null;
    setIsRunning(false);
    setCorrections([]);
  };

  useEffect(() => {
    return () => stopCamera();
  }, []);

  return (
    <div className="yoga-page">
      <h1 className="page-title">Yoga Pose Detection</h1>
      <p className="page-subtitle">
        Select a pose, enable your camera, and get real-time angle corrections with MoveNet Thunder.
      </p>

      <div className="yoga-layout">
        <div className="pose-selector card">
          <h3>Select a Pose</h3>
          <div className="pose-list">
            {poses.map((pose) => (
              <button
                key={pose.id}
                className={`pose-btn ${selectedPose?.id === pose.id ? 'selected' : ''}`}
                onClick={() => setSelectedPose(pose)}
              >
                {pose.name}
              </button>
            ))}
          </div>

          {selectedPose && (
            <div className="pose-instructions">
              <h4>Instructions</h4>
              <ul>
                {selectedPose.instructions.map((inst, i) => (
                  <li key={i}>{inst}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="camera-controls">
            {!isRunning ? (
              <button className="primary" onClick={startCamera} disabled={!selectedPose || loading}>
                {loading ? 'Loading model...' : 'Start Camera'}
              </button>
            ) : (
              <button className="secondary" onClick={stopCamera}>Stop Camera</button>
            )}
          </div>
        </div>

        <div className="camera-panel card">
          <div className="video-wrapper">
            <video ref={videoRef} className="yoga-video" playsInline muted />
            <canvas ref={canvasRef} className="yoga-canvas" />
          </div>

          {error && <p className="error-msg">{error}</p>}

          <div className="corrections-panel">
            <h3>Corrections</h3>
            {corrections.length === 0 ? (
              <p className="correction-ok">
                {isRunning && selectedPose ? '✓ Pose looks good!' : 'Start camera to see corrections'}
              </p>
            ) : (
              <ul>
                {corrections.map((c, i) => (
                  <li key={i} className="correction-item">{c.message}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
