const KEYPOINT_NAMES = [
  'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
  'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
  'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
  'left_knee', 'right_knee', 'left_ankle', 'right_ankle',
];

export function getKeypointByName(keypoints, name) {
  const idx = KEYPOINT_NAMES.indexOf(name);
  if (idx === -1) return null;
  const kp = keypoints[idx];
  return kp && kp.score > 0.3 ? kp : null;
}

export function calculateAngle(a, b, c) {
  if (!a || !b || !c) return null;

  const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
  let angle = Math.abs((radians * 180) / Math.PI);
  if (angle > 180) angle = 360 - angle;
  return Math.round(angle);
}

export function getCorrections(keypoints, poseConfig) {
  const corrections = [];

  if (!poseConfig?.angles) return corrections;

  for (const [name, config] of Object.entries(poseConfig.angles)) {
    const [p1Name, p2Name, p3Name] = config.joint;
    const kp1 = getKeypointByName(keypoints, `left_${p1Name}`) || getKeypointByName(keypoints, `right_${p1Name}`);
    const kp2 = getKeypointByName(keypoints, `left_${p2Name}`) || getKeypointByName(keypoints, `right_${p2Name}`);
    const kp3 = getKeypointByName(keypoints, `left_${p3Name}`) || getKeypointByName(keypoints, `right_${p3Name}`);

    const angle = calculateAngle(kp1, kp2, kp3);
    if (angle === null) continue;

    const diff = angle - config.target;
    if (Math.abs(diff) > config.tolerance) {
      corrections.push({
        joint: name,
        current: angle,
        target: config.target,
        message: diff > 0
          ? `Reduce ${name.replace('_', ' ')} angle by ~${Math.abs(diff)}° (current: ${angle}°, target: ${config.target}°)`
          : `Increase ${name.replace('_', ' ')} angle by ~${Math.abs(diff)}° (current: ${angle}°, target: ${config.target}°)`,
      });
    }
  }

  return corrections;
}

export function drawSkeleton(ctx, keypoints, width, height, corrections = []) {
  const correctionJoints = new Set(corrections.map((c) => c.joint));

  const connections = [
    [5, 6], [5, 7], [7, 9], [6, 8], [8, 10],
    [5, 11], [6, 12], [11, 12],
    [11, 13], [13, 15], [12, 14], [14, 16],
  ];

  ctx.lineWidth = 3;

  for (const [i, j] of connections) {
    const kp1 = keypoints[i];
    const kp2 = keypoints[j];
    if (!kp1 || !kp2 || kp1.score < 0.3 || kp2.score < 0.3) continue;

    ctx.strokeStyle = '#52b788';
    ctx.beginPath();
    ctx.moveTo(kp1.x, kp1.y);
    ctx.lineTo(kp2.x, kp2.y);
    ctx.stroke();
  }

  for (let i = 0; i < keypoints.length; i++) {
    const kp = keypoints[i];
    if (!kp || kp.score < 0.3) continue;

    ctx.beginPath();
    ctx.arc(kp.x, kp.y, 6, 0, 2 * Math.PI);
    ctx.fillStyle = correctionJoints.size > 0 ? '#f59e0b' : '#2d6a4f';
    ctx.fill();
  }
}
