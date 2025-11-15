# Quick Start - v2.0 with Masking

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd upcycler/client
npm install vite @vitejs/plugin-react @tensorflow/tfjs@^4.15.0
npm install -D @vitejs/plugin-react vite
```

### Step 2: Update package.json

Add this to your `package.json`:

```json
{
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

### Step 3: Activate New Files

```bash
# Backup old files
mv src/App.js src/App-old.js
mv src/index.js src/index-old.js

# Activate new files
mv src/App-v2.jsx src/App.jsx
mv src/index-vite.jsx src/index.jsx
```

### Step 4: Start the App

```bash
# Terminal 1: Start server
cd ../server
npm start

# Terminal 2: Start client (Vite)
cd ../client
npm run dev
```

### Step 5: Use the App!

1. Upload a clothing photo
2. See the mask auto-generate
3. Edit mask if needed
4. Select a style
5. Download your transformed clothing!

## ✨ What's Different?

**Before**: Style applied to entire image (including background)

**Now**: Style applied ONLY to clothing (background preserved)

## 🎯 Key Features

- ✅ **Smart Masking**: AI detects clothing automatically
- ✅ **Mask Editor**: Refine the detection manually
- ✅ **Background Preserved**: Only clothing gets styled
- ✅ **Real-time Preview**: See mask before styling

## 📖 Need More Help?

- See `SETUP_VITE.md` for detailed setup
- See `IMPLEMENTATION_SUMMARY.md` for technical details
- See `README_V2.md` for full documentation

Happy styling! 🎨
