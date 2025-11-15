# Style Image Guide - How to Add Style Images

## 📁 Where to Place Images

All style images should be placed in: `server/public/styles/`

Supported formats: **JPG, PNG, GIF, WebP**

## 🎨 Retro Style Sources (Public Domain)

### 1950s Advertisements & Vintage Fashion

1. **Library of Congress** (https://www.loc.gov/)

   - Search: "1950s fashion", "vintage advertisements"
   - Filter by: "Available Online" and "Public Domain"
   - Direct link: https://www.loc.gov/pictures/

2. **Internet Archive** (https://archive.org/)

   - Search: "1950s fashion plates", "vintage fashion illustrations"
   - Collections: "Vintage Fashion", "Retro Advertisements"
   - Direct link: https://archive.org/details/vintagefashion

3. **Wikimedia Commons** (https://commons.wikimedia.org/)

   - Search: "1950s fashion", "vintage fashion plate"
   - Filter by: "Public Domain"
   - Direct link: https://commons.wikimedia.org/wiki/Category:1950s_fashion

4. **Public Domain Review** (https://publicdomainreview.org/)
   - Collections: Historical fashion plates, vintage ads
   - All images are public domain

### 8-Bit Art & Pixel Art

1. **OpenGameArt** (https://opengameart.org/)

   - Search: "8-bit", "pixel art", "retro patterns"
   - Filter by: CC0 (public domain) or CC-BY

2. **Itch.io** (https://itch.io/)

   - Search: "8-bit textures", "pixel art patterns"
   - Many free assets with public domain licenses

3. **Lospec** (https://lospec.com/)
   - Pixel art palette library
   - Free pixel art patterns and textures

## 🚀 Modern Style Sources

### Contemporary Patterns & Textures

1. **Unsplash** (https://unsplash.com/)

   - Search: "abstract pattern", "geometric texture", "modern design"
   - Free to use (Unsplash License)

2. **Pexels** (https://www.pexels.com/)

   - Search: "abstract", "pattern", "texture"
   - Free to use

3. **Pixabay** (https://pixabay.com/)

   - Search: "abstract pattern", "geometric design"
   - Free for commercial use

4. **Freepik** (https://www.freepik.com/)
   - Search: "modern pattern", "contemporary texture"
   - Free with attribution (check license)

## 📥 Quick Download Guide

### Method 1: Manual Download

1. Visit any of the sources above
2. Search for your desired style
3. Download the image
4. Save it to `server/public/styles/`
5. Use descriptive names like:
   - `retro-1950s-ad-1.jpg`
   - `retro-vintage-fashion-plate.png`
   - `retro-8bit-pattern.gif`
   - `modern-geometric-1.jpg`
   - `modern-abstract-texture.png`

### Method 2: Using Command Line (if you have image URLs)

**Windows PowerShell:**

```powershell
cd server/public/styles
# Download example (replace URL with actual image URL)
Invoke-WebRequest -Uri "https://example.com/image.jpg" -OutFile "retro-style-1.jpg"
```

**Mac/Linux:**

```bash
cd server/public/styles
# Download example
curl -o retro-style-1.jpg "https://example.com/image.jpg"
```

## 🎯 Recommended Image Specifications

- **Size**: 256x256 to 512x512 pixels (works best with the AI model)
- **Format**: PNG or JPG
- **Aspect Ratio**: Square (1:1) preferred
- **Style**: High contrast patterns work best

## 📝 Naming Convention

Use descriptive names that indicate the style:

- **Retro**: `retro-*` prefix (e.g., `retro-1950s-ad.png`)
- **Modern**: `modern-*` prefix (e.g., `modern-geometric.png`)

The app automatically categorizes based on filename!

## ✅ Verification

After adding images:

1. Restart the server: `cd server && npm start`
2. Refresh the client: The style gallery should show your new images
3. Check the browser console for any loading errors

## 🔍 Example Searches

### For Retro Styles:

- "1950s fashion advertisement"
- "vintage fashion plate illustration"
- "retro pixel art pattern"
- "8-bit texture sprite"
- "vintage textile pattern"

### For Modern Styles:

- "abstract geometric pattern"
- "modern minimalist texture"
- "contemporary design pattern"
- "digital art texture"
- "modern abstract art"

## 💡 Pro Tips

1. **Start Small**: Add 5-10 images to test, then expand
2. **Mix It Up**: Combine different types (ads, patterns, textures)
3. **Test Results**: Try each style to see which works best
4. **High Contrast**: Images with clear patterns produce better results
5. **Square Images**: Crop images to square format for best display

## 🚨 Legal Reminder

- Always check image licenses before use
- Public domain images are safest for hackathon/demo projects
- For production, ensure proper licensing
- When in doubt, use images from:
  - Library of Congress (public domain)
  - Wikimedia Commons (check license)
  - Unsplash/Pexels (free licenses)

Happy styling! 🎨
