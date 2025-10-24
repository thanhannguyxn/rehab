import React from "react";
import { Typography, Box, Paper } from "@mui/material";

const Home = () => {
  return (
    <Box display="flex" justifyContent="center" mt={8}>
      <Paper elevation={3} sx={{ p: 4, maxWidth: 700, textAlign: "center" }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Welcome to Medic 1
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Your AI-powered home rehabilitation assistant for elderly care.
          Follow guided exercises, get real-time feedback, and track your progress safely from home.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Home;
