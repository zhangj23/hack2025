#!/bin/bash
# Migration script to Vite with masking features

echo "🚀 Migrating AI Upcycler to Vite with Masking Pipeline..."
echo ""

cd client || exit

# Backup current files
echo "📦 Backing up current files..."
mkdir -p backup
cp package.json backup/package.json.backup 2>/dev/null || true
cp src/App.js backup/App.js.backup 2>/dev/null || true
cp src/index.js backup/index.js.backup 2>/dev/null || true

# Install Vite dependencies
echo "📥 Installing Vite dependencies..."
npm install vite @vitejs/plugin-react @tensorflow/tfjs@^4.15.0 --save
npm install -D @vitejs/plugin-react vite

# Update package.json
echo "⚙️  Updating package.json..."
# This is a simplified version - you may need to manually edit package.json
# to add "type": "module" and update scripts

# Activate new files
echo "🔄 Activating new files..."
if [ -f "src/App-v2.jsx" ]; then
  mv src/App.js src/App-old.js 2>/dev/null || true
  mv src/App-v2.jsx src/App.jsx
  echo "✅ Activated App.jsx"
fi

if [ -f "src/index-vite.jsx" ]; then
  mv src/index.js src/index-old.js 2>/dev/null || true
  mv src/index-vite.jsx src/index.jsx
  echo "✅ Activated index.jsx"
fi

echo ""
echo "✨ Migration complete!"
echo ""
echo "Next steps:"
echo "1. Edit package.json to add 'type': 'module'"
echo "2. Update scripts to use 'vite' instead of 'react-scripts'"
echo "3. Run: npm run dev"
echo ""
echo "See SETUP_VITE.md for detailed instructions."

