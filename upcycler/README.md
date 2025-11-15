# The AI Upcycler - Your Personal Stylist

Transform retro thrift-store clothing into modern designs using AI-powered style transfer.

## 🎨 Concept

Fast fashion is a sustainability disaster. The AI Upcycler helps you breathe new life into vintage clothing by showing you how to transform that 1980s blazer into 100 different modern designs using AI style transfer.

**Retro vs. Modern**: Transform "retro" thrift-store clothing (sourced from public domain archives) with "modern" AI-driven style transfer.

## 🚀 Features

- **Instant Style Transfer**: Upload a photo of your clothing and see it transformed instantly
- **Pre-populated Style Gallery**: Choose from retro and modern patterns
- **Custom Style Upload**: Upload your own style images
- **Three-Panel Layout**: Content (left), Style Gallery (middle), Output (right)
- **Download Results**: Save your transformed designs

## 🛠️ Tech Stack

- **Frontend**: React with Tailwind CSS
- **Backend**: Express.js
- **AI**: Magenta.js (Arbitrary Image Stylization)
- **Styling**: Tailwind CSS

## 📦 Installation

1. Install dependencies for all packages:

```bash
npm run install-all
```

Or install individually:

```bash
# Root
npm install

# Server
cd server
npm install

# Client
cd ../client
npm install
```

## 🎯 Running the Application

### Development Mode (runs both server and client)

From the root directory:

```bash
npm run dev
```

### Run Separately

**Backend Server:**

```bash
cd server
npm start
```

Server runs on `http://localhost:5000`

**Frontend Client:**

```bash
cd client
npm start
```

Client runs on `http://localhost:3000`

## 📁 Project Structure

```
upcycler/
├── server/
│   ├── index.js          # Express server
│   ├── public/
│   │   └── styles/       # Style gallery images
│   └── uploads/          # Uploaded images (auto-created)
├── client/
│   ├── src/
│   │   ├── App.js        # Main React component
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   └── public/
└── README.md
```

## 🖼️ Adding Style Images

**📖 See detailed guides:**

- **[QUICK_DOWNLOAD.md](QUICK_DOWNLOAD.md)** - Fastest way to get started with direct links
- **[STYLE_GUIDE.md](STYLE_GUIDE.md)** - Complete guide with all sources and methods
- **[DOWNLOAD_IMAGES.md](DOWNLOAD_IMAGES.md)** - Automated download script guide

**Quick Steps:**

### Option 1: Automated Download (Recommended)

```bash
# Download images from URLs
npm run download-images "https://example.com/image1.jpg" "https://example.com/image2.png"

# Or use a file with URLs
npm run download-images --urls example-urls.txt
```

### Option 2: Manual Download

1. Add style images to `server/public/styles/`
2. Supported formats: JPG, PNG, GIF, WebP
3. Naming convention: Use descriptive names (e.g., `retro-1950s-ad.png`, `modern-geometric.jpg`)
4. The app will automatically detect and display all images in the style gallery

### Quick Links for Style Images

**Retro Styles (Public Domain):**

- [Wikimedia Commons - 1950s Fashion](https://commons.wikimedia.org/wiki/Category:1950s_fashion)
- [Library of Congress - Vintage Fashion](https://www.loc.gov/pictures/search/?q=vintage+fashion+plate)
- [Internet Archive - Vintage Fashion](https://archive.org/search.php?query=vintage%20fashion%20plate)

**Modern Styles (Free to Use):**

- [Unsplash - Abstract Patterns](https://unsplash.com/s/photos/abstract-pattern)
- [Pexels - Geometric Patterns](https://www.pexels.com/search/geometric%20pattern/)
- [Pixabay - Modern Textures](https://pixabay.com/images/search/abstract%20pattern/)

### Style Image Suggestions

**Retro Styles:**

- 1950s fashion advertisements (public domain)
- Vintage fashion plates
- 8-bit pixel art patterns
- Retro geometric patterns

**Modern Styles:**

- Contemporary abstract patterns
- Modern textures
- Geometric designs
- Digital art patterns

## 🎨 How to Use

1. **Upload Content**: Click "Choose Clothing Photo" and select an image of your clothing item
2. **Select Style**:
   - Choose from the pre-populated style gallery, OR
   - Upload your own custom style image
3. **View Result**: The stylized output appears instantly in the right panel
4. **Download**: Click "Download Result" to save your transformed design

## 🔧 Configuration

Create a `.env` file in the `server` directory (optional):

```
PORT=5000
```

Create a `.env` file in the `client` directory (optional):

```
REACT_APP_API_URL=http://localhost:5000
```

## 📝 API Endpoints

- `GET /api/health` - Health check
- `POST /api/upload-content` - Upload content image
- `POST /api/upload-style` - Upload style image
- `GET /api/styles` - Get list of available styles
- `GET /uploads/:filename` - Serve uploaded images
- `GET /styles/:filename` - Serve style gallery images

## 🎯 Demo Features

- **Visually Stunning**: Three-panel layout with instant transformations
- **Instant Results**: Real-time style transfer using Magenta.js
- **Shareable**: Download and share your transformed designs
- **Sustainable**: Promotes upcycling and reducing fashion waste

## 🤝 Contributing

This is a hackathon project. Feel free to fork and improve!

## 📄 License

MIT

## 🙏 Acknowledgments

- Magenta.js for the Arbitrary Style Transfer model
- Public domain image archives for retro style references
