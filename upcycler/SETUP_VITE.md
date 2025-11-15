# Complete Setup Guide - Vite + Masking Pipeline

## 🚀 Quick Start

### Step 1: Install Vite Dependencies

```bash
cd upcycler/client
npm install vite @vitejs/plugin-react @tensorflow/tfjs@^4.15.0 --save
npm install -D @vitejs/plugin-react vite
```

### Step 2: Update Package.json

Replace your `package.json` scripts section with:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "type": "module"
}
```

### Step 3: Activate New Files

```bash
# Rename old files (backup)
mv src/App.js src/App-old.js
mv src/index.js src/index-old.js

# Activate new files
mv src/App-v2.jsx src/App.jsx
mv src/index-vite.jsx src/index.jsx
```

### Step 4: Start Development

```bash
npm run dev
```

## ✨ New Features

### 1. Smart Masking

- **Automatic Detection**: AI automatically detects clothing in your photo
- **Mask Preview**: See the detected clothing area before styling
- **Mask Editor**: Refine the mask with brush tools
- **Background Preservation**: Style only applies to clothing, background stays original

### 2. Improved UI

- **Mask Toggle**: Enable/disable masking
- **Mask Editor Modal**: Full-screen mask editing
- **Real-time Preview**: See mask changes instantly

## 🎯 How to Use

1. **Upload Content**: Upload a photo of clothing
2. **Enable Masking**: Check "Use Smart Masking" (enabled by default)
3. **Review Mask**: Check the mask preview - white areas will be styled
4. **Edit Mask** (Optional): Click "Edit Mask" to refine the detection
5. **Select Style**: Choose a style from gallery or upload your own
6. **Adjust Strength**: Use the slider to control style intensity
7. **Download**: Save your transformed clothing!

## 🔧 Technical Details

### Masking Pipeline

1. **Segmentation**: Uses DeepLabV3 model (or fallback) to detect clothing
2. **Mask Generation**: Creates black/white mask (white = clothing area)
3. **Mask Application**: Style transfer only applies to white areas
4. **Blending**: Original background + styled clothing = final result

### Fallback Behavior

- If DeepLabV3 model fails to load, uses simple color-based segmentation
- App works offline with fallback method
- Mask editor always available for manual refinement

## 📦 File Structure

```
client/
├── src/
│   ├── components/
│   │   └── MaskEditor.jsx       # Interactive mask editor
│   ├── utils/
│   │   └── segmentation.js      # Mask generation & utilities
│   ├── App.jsx                   # Main app (with masking)
│   └── index.jsx                 # Vite entry point
├── vite.config.js                # Vite configuration
└── index.html                    # HTML entry
```

## 🐛 Troubleshooting

### "Cannot find module" errors

- Make sure you've installed all dependencies
- Check that `type: "module"` is in package.json

### Segmentation model not loading

- This is normal - fallback method will be used
- App works fine without the model
- Check browser console for details

### Mask not showing

- Make sure "Use Smart Masking" is checked
- Try uploading a new image
- Check browser console for errors

## 🎨 Mask Editor Tips

- **Add Mode**: Paint white areas (will receive style)
- **Erase Mode**: Paint black areas (will keep original)
- **Brush Size**: Adjust for precision vs speed
- **Real-time**: Changes apply immediately to output

## 🚀 Next Steps

The app now supports:

- ✅ Smart masking with automatic detection
- ✅ Manual mask editing
- ✅ Masked style transfer
- ✅ Background preservation

Future enhancements:

- Better segmentation models
- VTON (Virtual Try-On) pipeline
- Batch processing
- Mask templates

Enjoy your upgraded AI Upcycler! 🎨
