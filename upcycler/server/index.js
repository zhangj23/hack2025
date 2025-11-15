const express = require("express");
const cors = require("cors");
const multer = require("multer");
const path = require("path");
const fs = require("fs");

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

// Configure multer for file uploads
const uploadsDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + "-" + file.originalname);
  },
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
});

// Serve uploaded files
app.use("/uploads", express.static(uploadsDir));

// Health check endpoint
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", message: "AI Upcycler API is running" });
});

// Upload content image endpoint
app.post("/api/upload-content", upload.single("content"), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No file uploaded" });
  }
  res.json({
    success: true,
    url: `/uploads/${req.file.filename}`,
    filename: req.file.filename,
  });
});

// Upload style image endpoint
app.post("/api/upload-style", upload.single("style"), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No file uploaded" });
  }
  res.json({
    success: true,
    url: `/uploads/${req.file.filename}`,
    filename: req.file.filename,
  });
});

// Serve style gallery images
app.get("/api/styles", (req, res) => {
  const stylesDir = path.join(__dirname, "public", "styles");
  const styles = [];

  if (fs.existsSync(stylesDir)) {
    const files = fs.readdirSync(stylesDir);
    files.forEach((file) => {
      if (/\.(jpg|jpeg|png|gif|webp)$/i.test(file)) {
        styles.push({
          name: file.replace(/\.[^/.]+$/, ""),
          url: `/styles/${file}`,
          category: file.includes("retro") ? "retro" : "modern",
        });
      }
    });
  }

  res.json(styles);
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
