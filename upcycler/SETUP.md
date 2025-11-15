# Quick Setup Guide

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn

## Installation Steps

1. **Install all dependencies:**

   ```bash
   npm run install-all
   ```

2. **Add style images (optional but recommended):**

   - Add style images to `server/public/styles/`
   - Use public domain images for retro styles (1950s ads, vintage fashion plates, 8-bit art)
   - Use modern patterns for contemporary styles
   - Supported formats: JPG, PNG, GIF, WebP

3. **Start the application:**

   ```bash
   npm run dev
   ```

   This will start both the server (port 5000) and client (port 3000)

4. **Open your browser:**
   Navigate to `http://localhost:3000`

## First Time Setup

The AI model will download automatically on first use. This may take a few minutes depending on your internet connection.

## Troubleshooting

- **Model not loading**: Check your internet connection. The model downloads from Google's servers.
- **Styles not showing**: Make sure you've added images to `server/public/styles/`
- **Upload errors**: Check that the `server/uploads/` directory has write permissions
- **CORS errors**: Make sure the server is running on port 5000

## Development Tips

- The style transfer works best with images around 512x512 pixels
- For best results, use high-contrast style images
- Content images can be any size, but will be resized for processing
