// MoveNet keypoint index → name mapping (17 keypoints)
const KEYPOINT_NAMES = [
  'nose',           // 0
  'left_eye',       // 1
  'right_eye',      // 2
  'left_ear',       // 3
  'right_ear',      // 4
  'left_shoulder',  // 5
  'right_shoulder', // 6
  'left_elbow',     // 7
  'right_elbow',    // 8
  'left_wrist',     // 9
  'right_wrist',    // 10
  'left_hip',       // 11
  'right_hip',      // 12
  'left_knee',      // 13
  'right_knee',     // 14
  'left_ankle',     // 15
  'right_ankle',    // 16
];

const SCORE_THRESHOLD = 0.25;

// Get a keypoint by its full MoveNet name e.g. 'left_knee'
export function getKeypointByName(keypoints, fullName) {
  const idx = KEYPOINT_NAMES.indexOf(fullName);
  if (idx === -1) return null;
  const kp = keypoints[idx];
  return kp && kp.score > SCORE_THRESHOLD ? kp : null;
}

// Count how many keypoints are visible at sufficient confidence
export function countVisibleKeypoints(keypoints) {
  return keypoints.filter((kp) => kp && kp.score > SCORE_THRESHOLD).length;
}

// Calculate angle (degrees) at vertex b, given three points a-b-c
export function calculateAngle(a, b, c) {
  if (!a || !b || !c) return null;
  const radians =
    Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
  let angle = Math.abs((radians * 180) / Math.PI);
  if (angle > 180) angle = 360 - angle;
  return Math.round(angle);
}

/**
 * Returns { corrections, anglesChecked, anglesDetected }
 *
 * - corrections: array of correction objects
 * - anglesChecked: total angle rules in the pose config
 * - anglesDetected: how many angles were actually computable from visible keypoints
 *
 * When anglesDetected === 0, the caller should show "body not detected" instead of ✅.
 */
export function getCorrections(keypoints, poseConfig) {
  const corrections = [];
  if (!poseConfig?.angles) return { corrections, anglesChecked: 0, anglesDetected: 0 };

  const entries = Object.entries(poseConfig.angles);
  let anglesDetected = 0;

  for (const [angleName, config] of entries) {
    const [j1, j2, j3] = config.joint; // e.g. ["hip", "knee", "ankle"]

    // If angle name starts with left_ or right_, only check that side
    const nameHint = angleName.startsWith('left_')
      ? ['left']
      : angleName.startsWith('right_')
      ? ['right']
      : ['left', 'right'];

    let bestAngle = null;
    let bestDiff = 0;

    for (const side of nameHint) {
      const kp1 = getKeypointByName(keypoints, `${side}_${j1}`);
      const kp2 = getKeypointByName(keypoints, `${side}_${j2}`);
      const kp3 = getKeypointByName(keypoints, `${side}_${j3}`);

      const angle = calculateAngle(kp1, kp2, kp3);
      if (angle === null) continue;

      const diff = angle - config.target;
      // Keep whichever side deviates more from target
      if (Math.abs(diff) > Math.abs(bestDiff)) {
        bestAngle = angle;
        bestDiff = diff;
      }
    }

    if (bestAngle === null) continue; // keypoints not visible for this angle
    anglesDetected++;

    if (Math.abs(bestDiff) > config.tolerance) {
      const label = angleName.replace(/_/g, ' ');
      const direction = bestDiff > 0 ? 'Reduce' : 'Increase';
      corrections.push({
        joint: angleName,
        current: bestAngle,
        target: config.target,
        message: `${direction} ${label}: currently ${bestAngle}°, target ${config.target}°`,
      });
    }
  }

  return { corrections, anglesChecked: entries.length, anglesDetected };
}

// Skeleton connections by MoveNet keypoint index pairs
const CONNECTIONS = [
  // Torso
  [5, 6], [5, 11], [6, 12], [11, 12],
  // Left arm
  [5, 7], [7, 9],
  // Right arm
  [6, 8], [8, 10],
  // Left leg
  [11, 13], [13, 15],
  // Right leg
  [12, 14], [14, 16],
];

export function drawSkeleton(ctx, keypoints, width, height, corrections = []) {
  const hasCorrections = corrections.length > 0;

  // Draw bone connections
  for (const [i, j] of CONNECTIONS) {
    const kp1 = keypoints[i];
    const kp2 = keypoints[j];
    if (!kp1 || !kp2 || kp1.score < SCORE_THRESHOLD || kp2.score < SCORE_THRESHOLD) continue;

    ctx.strokeStyle = hasCorrections ? '#f97316' : '#22c55e';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(kp1.x, kp1.y);
    ctx.lineTo(kp2.x, kp2.y);
    ctx.stroke();
  }

  // Draw keypoint circles
  for (let i = 0; i < keypoints.length; i++) {
    const kp = keypoints[i];
    if (!kp || kp.score < SCORE_THRESHOLD) continue;

    // Outer glow
    ctx.beginPath();
    ctx.arc(kp.x, kp.y, 7, 0, 2 * Math.PI);
    ctx.fillStyle = hasCorrections ? 'rgba(239,68,68,0.3)' : 'rgba(34,197,94,0.3)';
    ctx.fill();

    // Inner dot
    ctx.beginPath();
    ctx.arc(kp.x, kp.y, 4, 0, 2 * Math.PI);
    ctx.fillStyle = hasCorrections ? '#ef4444' : '#16a34a';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }
}
