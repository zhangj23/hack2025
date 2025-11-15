const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Sample prescription data
const samplePrescriptions = [
  {
    id: 1,
    doctor: "Dr. Smith",
    facility: "Medical Center",
    medication: "DICLORAN",
    dosage: "500mg",
    instructions: "Take 2x daily",
    date: new Date().toLocaleDateString()
  },
  {
    id: 2,
    doctor: "Dr. Johnson",
    facility: "City Hospital",
    medication: "AMOXICILLIN",
    dosage: "250mg",
    instructions: "Take 3x daily with food",
    date: new Date().toLocaleDateString()
  },
  {
    id: 3,
    doctor: "Dr. Williams",
    facility: "Community Clinic",
    medication: "LISINOPRIL",
    dosage: "10mg",
    instructions: "Take once daily",
    date: new Date().toLocaleDateString()
  }
];

// Routes
app.get('/api/prescriptions', (req, res) => {
  res.json(samplePrescriptions);
});

app.get('/api/prescriptions/random', (req, res) => {
  const randomPrescription = samplePrescriptions[Math.floor(Math.random() * samplePrescriptions.length)];
  res.json(randomPrescription);
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Prescription Digitizer API is running' });
});

// Serve static files from React app in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../client/build')));
  
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../client/build', 'index.html'));
  });
}

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});

