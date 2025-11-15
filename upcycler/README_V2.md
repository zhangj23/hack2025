# The AI Upcycler v2.0 - With Smart Masking

Transform retro thrift-store clothing into modern designs using **AI-powered style transfer with intelligent masking**.

## 🎯 What's New in v2.0

### ✨ Smart Masking Pipeline (Solution 1)

- **Automatic Clothing Detection**: AI automatically identifies and isolates clothing in photos
- **Mask-Based Style Transfer**: Style is applied ONLY to clothing, preserving the background
- **Interactive Mask Editor**: Refine the AI-detected mask with brush tools
- **Real-time Preview**: See exactly what will be styled before applying

### 🚀 Key Improvements

- **Background Preservation**: No more styling the background - only clothing gets transformed
- **Better Results**: More realistic transformations that respect clothing boundaries
- **User Control**: Edit masks manually for perfect results
- **Faster Development**: Migrated to Vite for better performance

## 🛠️ Tech Stack

- **Frontend**: React 18 + Vite
- **Backend**: Express.js
- **AI Models**:
  - Magenta.js (Arbitrary Style Transfer)
  - TensorFlow.js (Segmentation - DeepLabV3 or fallback)
- **Styling**: Tailwind CSS

## 📦 Installation

### Option 1: Use Vite (Recommended)

```bash
cd upcycler/client
npm install vite @vitejs/plugin-react @tensorflow/tfjs@^4.15.0
npm install -D @vitejs/plugin-react vite

# Update package.json to add "type": "module" and new scripts
# See SETUP_VITE.md for details

npm run dev
```

### Option 2: Keep Create React App

The masking features work with CRA too! Just:

1. Install TensorFlow.js 4.15.0
2. Copy the new components and utils
3. Integrate masking logic into your App.js

See `MIGRATION_TO_VITE.md` for detailed instructions.

## 🎨 How It Works

### The Masking Pipeline

1. **Upload Photo** → User uploads clothing photo
2. **Auto-Segmentation** → AI detects clothing area (white mask)
3. **Mask Preview** → User sees detected area
4. **Edit Mask** (Optional) → User refines with brush tools
5. **Style Transfer** → Style applied ONLY to masked (white) areas
6. **Blend** → Original background + Styled clothing = Final result

### Why This Works Better

**Before (v1.0)**:

- Style applied to entire image
- Background gets styled too
- Unrealistic results

**After (v2.0)**:

- Style applied only to clothing
- Background preserved
- More realistic transformations

## 🎯 Usage

1. **Upload Content**: Click "Choose Clothing Photo"
2. **Enable Masking**: Check "Use Smart Masking" (default: ON)
3. **Review Mask**: Check the mask preview below your image
4. **Edit Mask** (if needed): Click "Edit Mask" to refine
5. **Select Style**: Choose from gallery or upload custom
6. **Adjust Strength**: Use slider (10%-100%)
7. **Download**: Save your transformed clothing!

## 🔧 Mask Editor

The mask editor allows you to:

- **Add Areas**: Paint white to include in styling
- **Erase Areas**: Paint black to exclude from styling
- **Adjust Brush**: Change brush size (5-50px)
- **Real-time**: See changes immediately

## 📁 Project Structure

```
upcycler/
├── client/
│   ├── src/
│   │   ├── components/
│   │   │   └── MaskEditor.jsx      # Mask editing UI
│   │   ├── utils/
│   │   │   └── segmentation.js     # Mask generation
│   │   ├── App.jsx                  # Main app (Vite)
│   │   └── App-v2.jsx               # New app with masking
│   ├── vite.config.js               # Vite config
│   └── index.html                   # HTML entry
├── server/
│   └── index.js                      # Express API
└── README_V2.md                      # This file
```

## 🎨 Features

### Core Features

- ✅ Smart masking with automatic detection
- ✅ Manual mask editing
- ✅ Masked style transfer
- ✅ Background preservation
- ✅ Style strength control
- ✅ Style gallery
- ✅ Custom style upload

### Technical Features

- ✅ DeepLabV3 segmentation (with fallback)
- ✅ Real-time mask preview
- ✅ Canvas-based mask editing
- ✅ Efficient blending pipeline

## 🚀 Future Enhancements (Solution 2: VTON)

The next evolution would be Virtual Try-On (VTON):

- 3D-aware transformations
- Realistic fabric folding
- Pose-aware styling
- True virtual try-on experience

This requires more complex models (StableVITON, OOTDiffusion) and is planned for v3.0.

## 📝 API Endpoints

Same as before:

- `GET /api/health` - Health check
- `POST /api/upload-content` - Upload content image
- `POST /api/upload-style` - Upload style image
- `GET /api/styles` - Get style gallery
- `GET /uploads/:filename` - Serve uploaded images
- `GET /styles/:filename` - Serve style images

## 🐛 Troubleshooting

**Mask not generating?**

- Check browser console for errors
- Try disabling and re-enabling masking
- Fallback method will work even if model fails

**Style not applying correctly?**

- Check mask preview - is clothing area white?
- Try editing the mask manually
- Adjust style strength slider

**Model loading slowly?**

- First load downloads models (~10-50MB)
- Subsequent loads are cached
- Works offline with fallback method

## 📄 License

MIT

## 🙏 Acknowledgments

- Magenta.js for style transfer
- TensorFlow.js for segmentation
- DeepLabV3 model for clothing detection

---

**Ready to transform your clothing?** Upload a photo and watch the magic happen! 🎨✨
