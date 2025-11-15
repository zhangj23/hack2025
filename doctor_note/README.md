# 🩺 Retro Prescription Digitizer

**Modern AI solving a retro problem: Illegible doctor's handwriting**

A browser-based, real-time OCR tool that digitizes and validates handwritten medical prescriptions before they're filled, preventing costly and dangerous errors.

## 🎯 The Problem

Doctor's handwriting is a "retro" data-entry problem that has become a punchline. But it's a serious patient safety issue. Medication errors from illegible prescriptions cost lives and millions of dollars annually.

## ✨ The Solution

This modern AI tool uses TensorFlow.js to:
- Recognize handwritten text in real-time
- Digitize prescriptions instantly
- Validate medication names and dosages
- Prevent errors before prescriptions are filled

## 🚀 Tech Stack

- **Frontend**: React + Vite + Tailwind CSS
- **AI/ML**: TensorFlow.js
- **Backend**: Express.js
- **Build Tool**: Vite (fast HMR and builds)
- **Features**: Canvas drawing, image upload, real-time OCR

## 📦 Installation

1. Install all dependencies:
```bash
npm run install-all
```

2. Start the development servers:
```bash
npm run dev
```

This will start:
- Backend server on `http://localhost:5000`
- React frontend on `http://localhost:3000`

## 🎮 Usage

1. **View Retro Prescription**: See a sample handwritten prescription (like "DICLORAN")
2. **Draw or Upload**: 
   - Draw on the canvas with your mouse
   - Or upload an image of a prescription
3. **Recognize**: Click "Recognize" to see AI digitize the text
4. **Compare**: See the difference between retro problems and modern solutions

## 🏗️ Project Structure

```
doctor_note/
├── client/          # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── PrescriptionDisplay.js
│   │   │   ├── DrawingCanvas.js
│   │   │   └── ComparisonSection.js
│   │   ├── App.js
│   │   └── index.js
│   └── public/
├── server/          # Express backend
│   └── index.js
└── package.json
```

## 🎨 Features

- **Interactive Canvas**: Draw prescriptions with mouse
- **Image Upload**: Upload prescription images
- **AI Recognition**: TensorFlow.js-powered OCR
- **Retro Styling**: Vintage prescription card design
- **Real-time Feedback**: Confidence scores and instant results
- **Sample Prescriptions**: Multiple prescription examples

## 🔮 Future Enhancements

- Integration with actual handwriting recognition models
- Medication database validation
- Prescription format validation
- Export to digital prescription systems
- Mobile app version

## 📝 License

MIT

## 👥 Built For

Hack 2025 - Demonstrating how modern AI can solve retro healthcare problems

