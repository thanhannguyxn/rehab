"""
Post-session face-based pain/fatigue analyzer.

Runs on still frames (static_image_mode=True) — NOT called during live
skeleton tracking so it never competes with pose processing.

Geometric pipeline (no ML model training required):
  - Eye Aspect Ratio (EAR)  → squinting = pain signal
  - Brow depression score   → furrowed brows = pain signal
  - Lip compression ratio   → pressed lips = pain signal
  - Jaw slack ratio         → slack jaw = fatigue signal
  - Combined scoring into pain_score / fatigue_score ∈ [0, 1]
"""

import math
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

# ---------------------------------------------------------------------------
# FaceMesh landmark indices used for analysis
# ---------------------------------------------------------------------------
# Left eye
_L_EYE_TOP     = 159
_L_EYE_BOT     = 145
_L_EYE_INNER   = 33
_L_EYE_OUTER   = 133

# Right eye
_R_EYE_TOP     = 386
_R_EYE_BOT     = 374
_R_EYE_INNER   = 263
_R_EYE_OUTER   = 362

# Brow inner corners (closest to nose bridge)
_L_INNER_BROW  = 55
_R_INNER_BROW  = 285

# Brow mid-points (used for depression measurement)
_L_BROW_MID    = 105
_R_BROW_MID    = 334

# Face width reference points (left/right cheeks)
_FACE_LEFT     = 234
_FACE_RIGHT    = 454

# Face height reference points
_FACE_TOP      = 10
_FACE_CHIN     = 152

# Mouth corners and center lips
_MOUTH_TOP     = 13
_MOUTH_BOT     = 14
_MOUTH_LEFT    = 78
_MOUTH_RIGHT   = 308


def _ear(lm, top: int, bot: int, inner: int, outer: int) -> float:
    """Eye Aspect Ratio — lower = more closed/squinting."""
    h = abs(lm[bot].y - lm[top].y)
    w = abs(lm[outer].x - lm[inner].x)
    return h / (w + 1e-6)


def _brow_depression(lm, brow_mid: int, eye_top: int, face_h: float) -> float:
    """
    Normalised brow-to-eye gap (positive = brow above eye = healthy gap).
    Value shrinks / goes near-zero when brows are heavily depressed.
    Returned as a *score* where higher = more depressed.
    """
    gap = (lm[eye_top].y - lm[brow_mid].y)   # positive because y increases downward
    normalised = gap / (face_h + 1e-6)
    # Typical neutral gap ~0.05-0.09; clamped to [0, 0.12]
    normalised = max(0.0, min(normalised, 0.12))
    # Invert so that low gap → high depression score
    return 1.0 - (normalised / 0.12)


def _lip_compression(lm, top: int, bot: int, left: int, right: int) -> float:
    """
    Mouth Aspect Ratio for the vertical opening.
    Low value = lips pressed together (pain signal).
    Returns a *compression score* where 1 = very compressed.
    """
    v = abs(lm[bot].y - lm[top].y)
    w = abs(lm[right].x - lm[left].x)
    mar = v / (w + 1e-6)
    # Neutral lip MAR ~ 0.04-0.10; compress is near 0, open is ~0.3+
    threshold = 0.06
    if mar >= threshold:
        return 0.0
    return (threshold - mar) / threshold


def _jaw_slack(lm, top: int, bot: int, left: int, right: int) -> float:
    """
    Moderate mouth openness without pain markers.
    Returns score 0-1; peaks around MAR=0.20 (slightly agape, not wide open).
    """
    v = abs(lm[bot].y - lm[top].y)
    w = abs(lm[right].x - lm[left].x)
    mar = v / (w + 1e-6)
    # Bell-shaped peak around 0.15-0.25
    peak = 0.20
    spread = 0.12
    score = math.exp(-((mar - peak) ** 2) / (2 * spread ** 2))
    # Only meaningful when mouth is more open than neutral closed
    if mar < 0.04:
        return 0.0
    return min(score, 1.0)


class FacePainAnalyzer:
    """
    Lazy-initialised singleton wrapper around MediaPipe FaceMesh.

    Usage::

        analyzer = FacePainAnalyzer()
        result = analyzer.analyze_frame(bgr_frame)
        # result → {"pain_score": 0.0-1.0, "fatigue_score": 0.0-1.0,
        #            "expression": "neutral"|"discomfort"|"pain"|"tired"}
        # or None if no face detected
    """

    _face_mesh = None

    @classmethod
    def _get_mesh(cls):
        if cls._face_mesh is None:
            cls._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=False,
                min_detection_confidence=0.5,
            )
        return cls._face_mesh

    def analyze_frame(self, bgr_frame: np.ndarray) -> Optional[dict]:
        """
        Analyse a single BGR frame.

        Returns a dict with pain_score, fatigue_score, expression; or None if
        no face is detected.
        """
        if bgr_frame is None:
            return None

        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        results = self._get_mesh().process(rgb)

        if not results.multi_face_landmarks:
            return None

        lm = results.multi_face_landmarks[0].landmark

        # Reference dimensions
        face_h = abs(lm[_FACE_CHIN].y - lm[_FACE_TOP].y)

        # --- Feature extraction ---
        left_ear  = _ear(lm, _L_EYE_TOP, _L_EYE_BOT, _L_EYE_INNER, _L_EYE_OUTER)
        right_ear = _ear(lm, _R_EYE_TOP, _R_EYE_BOT, _R_EYE_INNER, _R_EYE_OUTER)
        avg_ear   = (left_ear + right_ear) / 2.0

        # Squint: EAR drops below ~0.25 in a normal open eye
        # Threshold 0.22 chosen conservatively to avoid flagging natural small eyes
        normal_ear = 0.25
        squint_score = max(0.0, (normal_ear - avg_ear) / normal_ear)

        # Brow depression (average both sides)
        l_dep = _brow_depression(lm, _L_BROW_MID, _L_EYE_TOP, face_h)
        r_dep = _brow_depression(lm, _R_BROW_MID, _R_EYE_TOP, face_h)
        brow_score = (l_dep + r_dep) / 2.0

        lip_score = _lip_compression(
            lm, _MOUTH_TOP, _MOUTH_BOT, _MOUTH_LEFT, _MOUTH_RIGHT
        )

        jaw_score = _jaw_slack(
            lm, _MOUTH_TOP, _MOUTH_BOT, _MOUTH_LEFT, _MOUTH_RIGHT
        )

        # --- Combined scores ---
        # Pain: squinting + brow furrow + lip compression
        pain_score = (
            0.40 * squint_score
            + 0.35 * brow_score
            + 0.25 * lip_score
        )

        # Fatigue: drooping eyes (low EAR without much brow furrow) + jaw slack
        # Subtract brow_score because furrowed brows are a pain signal, not fatigue
        droop = max(0.0, squint_score - brow_score * 0.5)
        fatigue_score = (
            0.55 * droop
            + 0.30 * jaw_score
            + 0.15 * max(0.0, squint_score - brow_score)
        )

        pain_score    = round(min(pain_score, 1.0), 4)
        fatigue_score = round(min(fatigue_score, 1.0), 4)

        # --- Expression classification ---
        if pain_score > 0.55:
            expression = "pain"
        elif pain_score > 0.35:
            expression = "discomfort"
        elif fatigue_score > 0.50:
            expression = "tired"
        else:
            expression = "neutral"

        return {
            "pain_score":    pain_score,
            "fatigue_score": fatigue_score,
            "expression":    expression,
        }
