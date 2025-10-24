import React from "react";
import { AppBar, Toolbar, Typography, Button, Box } from "@mui/material";
import { Link, useLocation } from "react-router-dom";
import LocalHospitalIcon from "@mui/icons-material/LocalHospital";

const Navbar = () => {
  const location = useLocation();
  const fontStack =
    '"Poppins", "Inter", "Nunito", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';

  const navButton = (path, label) => {
    const isActive = location.pathname === path;
    return (
      <Button
        key={path}
        component={Link}
        to={path}
        disableElevation
        sx={{
          fontFamily: fontStack,
          mx: 1,
          px: 2.5,
          py: 1,
          textTransform: "none",
          fontSize: 17,
          fontWeight: 600, // giảm độ đậm ở đây
          color: isActive ? "#044e54" : "#0f172a",
          backgroundColor: isActive ? "rgba(6,182,212,0.12)" : "transparent",
          borderRadius: 2,
          transition: "all 150ms ease",
          boxShadow: isActive ? "0 4px 12px rgba(6,182,212,0.08)" : "none",
          "&:hover": {
            transform: "translateY(-2px)",
            backgroundColor: isActive ? "rgba(6,182,212,0.16)" : "rgba(15,23,42,0.04)",
          },
        }}
      >
        {label}
      </Button>
    );
  };

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        fontFamily: fontStack,
        backgroundColor: "#ffffff",
        color: "#0f172a",
        borderBottom: "1px solid rgba(15,23,42,0.06)",
        boxShadow: "0 6px 20px rgba(15,23,42,0.04)",
      }}
    >
      <Toolbar sx={{ display: "flex", justifyContent: "space-between", minHeight: 72 }}>
        <Box
          component={Link}
          to="/"
          sx={{
            display: "flex",
            alignItems: "center",
            textDecoration: "none",
            gap: 1,
            fontFamily: fontStack,
          }}
        >
          <LocalHospitalIcon sx={{ color: "#06b6d4", fontSize: 34 }} />
          <Typography
            sx={{
              color: "#044e54",
              fontWeight: 900,
              fontSize: 22,
              letterSpacing: 0.4,
              fontFamily: fontStack,
            }}
          >
            Medic 1
          </Typography>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center" }}>
          {navButton("/", "Home")}
          {navButton("/exercises", "Exercises")}
          {navButton("/reports", "Reports")}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
