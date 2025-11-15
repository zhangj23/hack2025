# Migration to Vite with Masking Pipeline

This document explains the migration to Vite and the new masking features.

## New Features

### 1. Smart Masking (2D Masking Pipeline)

- **Automatic Segmentation**: Uses AI to automatically detect and isolate clothing
- **Mask Editing**: Interactive mask editor to refine the clothing detection
- **Masked Style Transfer**: Applies style only to the clothing area, preserving background

### 2. Improved Style Transfer

- **Style Strength Control**: Adjustable slider (10% - 100%)
- **Better Blending**: More natural style application
- **Mask-Based Application**: Style only applied to detected clothing

## Migration Steps

### Option 1: Use Vite (Recommended)

1. **Backup current setup** (optional):

   ```bash
   cd upcycler/client
   cp package.json package.json.backup
   ```

2. **Install Vite dependencies**:

   ```bash
   npm install vite @vitejs/plugin-react --save-dev
   npm install @tensorflow/tfjs@^4.15.0 --save
   ```

3. **Update package.json**:

   - Replace scripts section with:
     ```json
     "scripts": {
       "dev": "vite",
       "build": "vite build",
       "preview": "vite preview"
     }
     ```
   - Add `"type": "module"` to package.json
   - Update TensorFlow.js to version 4.15.0

4. **Rename files**:

   ```bash
   mv src/App.js src/App-old.js
   mv src/App-v2.jsx src/App.jsx
   mv src/index.js src/index-old.js
   mv src/index-vite.jsx src/index.jsx
   mv index.html public/index.html  # if needed
   ```

5. **Start development server**:
   ```bash
   npm run dev
   ```

### Option 2: Keep Create React App (Current Setup)

The new masking features will work with the current setup, but you'll need to:

1. **Install additional dependencies**:

   ```bash
   npm install @tensorflow/tfjs@^4.15.0
   ```

2. **Update App.js**:
   - Copy the masking logic from App-v2.jsx
   - Import the segmentation utilities
   - Add the MaskEditor component

## New File Structure

```
client/
├── src/
│   ├── components/
│   │   └── MaskEditor.jsx      # Interactive mask editor
│   ├── utils/
│   │   └── segmentation.js     # Mask generation utilities
│   ├── App.jsx                  # Main app (Vite version)
│   ├── App-v2.jsx              # New app with masking
│   └── index.jsx                # Entry point (Vite)
├── vite.config.js               # Vite configuration
└── index.html                   # HTML entry (Vite)
```

## How Masking Works

1. **Upload Content Image**: User uploads a photo of clothing
2. **Auto-Generate Mask**: AI automatically detects clothing area
3. **Edit Mask (Optional)**: User can refine the mask using the editor
4. **Apply Style**: Style is applied only to the masked (clothing) area
5. **Result**: Background is preserved, only clothing gets styled

## API Changes

- Uses `import.meta.env.VITE_API_URL` instead of `process.env.REACT_APP_API_URL` (Vite)
- All imports use ES6 modules

## Troubleshooting

### TensorFlow.js Version

- Vite version uses TF.js 4.15.0
- CRA version uses TF.js 0.14.2 (for compatibility)

### Segmentation Model

- Tries to load DeepLabV3 from TensorFlow Hub
- Falls back to simple color-based segmentation if model fails to load
- This ensures the app works even without internet or model access

### Mask Editor

- Opens in a modal overlay
- Allows brush-based editing
- Changes apply immediately to style transfer

## Next Steps (Future Enhancements)

1. **Better Segmentation**: Integrate more accurate clothing segmentation models
2. **VTON Pipeline**: Add virtual try-on capabilities (Solution 2)
3. **Batch Processing**: Process multiple images at once
4. **Mask Templates**: Pre-defined masks for common clothing types
