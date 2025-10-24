import React from "react";
import { Typography, Box, Paper } from "@mui/material";

const Reports = () => {
  return (
    <Box display="flex" justifyContent="center" mt={8}>
      <Paper elevation={3} sx={{ p: 4, maxWidth: 700, textAlign: "center" }}>
        <Typography variant="h5" fontWeight="bold" gutterBottom>
          Performance Reports
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View detailed analytics of your rehabilitation sessions here.
          (Coming soon!)
        </Typography>
      </Paper>
    </Box>
  );
};

export default Reports;
