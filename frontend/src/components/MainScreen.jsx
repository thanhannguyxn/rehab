import React, { useRef, useState, useEffect } from "react";
import { Box, Button, Typography, Paper } from "@mui/material";
import { PlayArrow, Stop, SkipNext, CameraAlt, PowerSettingsNew } from "@mui/icons-material";

const MainScreen = () => {
  const videoRef = useRef(null);
  const timerRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [sessionActive, setSessionActive] = useState(false);
  const [seconds, setSeconds] = useState(0);

  const startCamera = async () => {
    try {
      if (!isCameraOn) {
        const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
        setStream(mediaStream);
        if (videoRef.current) videoRef.current.srcObject = mediaStream;
        setIsCameraOn(true);
      }
    } catch (err) {
      console.error("Camera error:", err);
      alert("Unable to access camera. Check permissions.");
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      setStream(null);
    }
    setIsCameraOn(false);
  };

  const startSession = async () => {
    await startCamera();
    if (timerRef.current) clearInterval(timerRef.current);
    setSeconds(0);
    setSessionActive(true);
    timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
  };

  const endSession = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setSessionActive(false);
    setSeconds(0);
    stopCamera();
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      stopCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const formatTime = (s) => {
    const mm = String(Math.floor(s / 60)).padStart(2, "0");
    const ss = String(s % 60).padStart(2, "0");
    return `${mm}:${ss}`;
  };

  return (
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "background.default",
        px: 2,
      }}
    >
      <Box sx={{ width: "100%", maxWidth: 1200 }}>
        <Typography
          variant="h4"
          sx={{ fontWeight: "700", mb: 2, fontSize: { xs: 20, md: 28 }, textAlign: "center" }}
        >
          AI-Powered Home Rehabilitation
        </Typography>

        {/* Horizontal panels: Camera (left) + Tutorial (right) */}
        <Box
          sx={{
            display: "flex",
            gap: 2,
            alignItems: "stretch",
            height: { xs: 420, md: 520 },
          }}
        >
          {/* Camera panel - larger */}
          <Paper
            elevation={6}
            sx={{
              flex: "0 0 70%",
              position: "relative",
              borderRadius: 3,
              overflow: "hidden",
              border: "4px solid",
              borderColor: sessionActive ? "success.dark" : "grey.300",
              boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
              bgcolor: "black",
            }}
          >
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                display: "block",
                transform: "scaleX(-1)", // mirror fixed
              }}
            />
            {!isCameraOn && (
              <Typography
                sx={{
                  position: "absolute",
                  top: "50%",
                  left: "50%",
                  transform: "translate(-50%, -50%)",
                  bgcolor: "rgba(255,255,255,0.06)",
                  color: "grey.300",
                  px: 2,
                  py: 1,
                  borderRadius: 1,
                  fontSize: 18,
                  fontWeight: 600,
                }}
              >
                Camera Off
              </Typography>
            )}

            {/* Timer badge */}
            <Box sx={{ position: "absolute", top: 12, right: 12, display: "flex", flexDirection: "row", gap: 1, alignItems: "center" }}>
              <Paper elevation={3} sx={{ px: 2, py: 0.8, borderRadius: 2, bgcolor: sessionActive ? "success.main" : "grey.100", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Typography sx={{ fontWeight: 400, fontSize: { xs: 18, md: 22 }, color: sessionActive ? "#fff" : "text.primary", textAlign: "center" }}>
                  {sessionActive ? "In Session" : "Ready"}
                </Typography>
              </Paper>
              <Paper elevation={3} sx={{ px: 2, py: 0.6, borderRadius: 2, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Typography sx={{ fontWeight: 400, fontSize: { xs: 18, md: 22 }, textAlign: "center" }} aria-live="polite">
                  {formatTime(seconds)}
                </Typography>
              </Paper>
            </Box>
          </Paper>

          {/* Tutorial panel - smaller */}
          <Paper
            elevation={4}
            sx={{
              flex: "0 0 30%",
              borderRadius: 3,
              p: 1.5,
              boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
              display: "flex",
              flexDirection: "column",
              gap: 1,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Typography sx={{ fontSize: { xs: 16, md: 18 }, fontWeight: 700 }}>Exercise Guide</Typography>
            <video
              src=""
              controls
              style={{ width: "100%", height: "100%", maxHeight: 360, borderRadius: 8, objectFit: "cover" }}
            />
          </Paper>
        </Box>

        {/* Controls - compact row below panels */}
        <Box
          sx={{
            mt: 3,
            display: "flex",
            gap: 2,
            alignItems: "center",
            justifyContent: "center",
            flexWrap: "wrap",
          }}
        >
          <Button
            variant="contained"
            color="primary"
            startIcon={<CameraAlt />}
            onClick={startCamera}
            disabled={isCameraOn}
            size="large"
            sx={{ fontSize: 18, minWidth: 160, px: 3, py: 1.25, borderRadius: 2, textTransform: "none" }}
            aria-label="Start camera"
          >
            Start Camera
          </Button>

          <Button
            variant="outlined"
            color="error"
            startIcon={<PowerSettingsNew />}
            onClick={stopCamera}
            disabled={!isCameraOn}
            size="large"
            sx={{ fontSize: 18, minWidth: 160, px: 3, py: 1.25, borderRadius: 2, textTransform: "none", borderWidth: 2 }}
            aria-label="Stop camera"
          >
            Stop Camera
          </Button>

          {!sessionActive ? (
            <Button
              variant="contained"
              color="success"
              startIcon={<PlayArrow />}
              onClick={startSession}
              size="large"
              sx={{ fontSize: 20, minWidth: 220, px: 4, py: 1.25, borderRadius: 3, textTransform: "none" }}
              aria-label="Start session"
            >
              Start Session
            </Button>
          ) : (
            <Button
              variant="contained"
              color="error"
              startIcon={<Stop />}
              onClick={endSession}
              size="large"
              sx={{ fontSize: 20, minWidth: 220, px: 4, py: 1.25, borderRadius: 3, textTransform: "none" }}
              aria-label="End session"
            >
              End Session
            </Button>
          )}

          <Button
            variant="outlined"
            color="primary"
            startIcon={<SkipNext />}
            onClick={() => alert("Next exercise")}
            size="large"
            sx={{ fontSize: 18, minWidth: 160, px: 3, py: 1.25, borderRadius: 2, textTransform: "none" }}
            aria-label="Next exercise"
          >
            Next Exercise
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default MainScreen;
