# Download Vintage Images Script

This script helps you download vintage and modern style images directly to `server/public/styles/`.

## 🚀 Quick Start

### Method 1: Download from URLs

```bash
cd upcycler
node download-vintage-images.js "https://example.com/image1.jpg" "https://example.com/image2.png"
```

### Method 2: Use a text file with URLs

1. Create or edit `example-urls.txt` and add image URLs (one per line)
2. Run:
   ```bash
   node download-vintage-images.js --urls example-urls.txt
   ```

### Method 3: Specify prefix (retro or modern)

```bash
node download-vintage-images.js --prefix modern "https://example.com/modern-pattern.jpg"
```

## 📋 How to Get Image URLs

### Wikimedia Commons (Best for Retro)

1. Visit: https://commons.wikimedia.org/wiki/Category:1950s_fashion
2. Click on an image you like
3. Right-click the full-size image → "Copy image address"
4. Use that URL in the script

**Example search terms:**

- "1950s fashion"
- "vintage fashion plate"
- "retro advertisement"
- "mid-century design"

### Library of Congress

1. Visit: https://www.loc.gov/pictures/
2. Search for "vintage fashion" or "1950s fashion"
3. Click on an image
4. Click "Download" → "Original file"
5. Right-click the image → "Copy image address"

### Internet Archive

1. Visit: https://archive.org/details/vintagefashion
2. Browse collections
3. Download images and note their URLs

## 📝 Creating a URL File

Create a text file (e.g., `vintage-urls.txt`):

```
https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Example1.jpg/800px-Example1.jpg
https://upload.wikimedia.org/wikipedia/commons/thumb/b/cd/Example2.png/800px-Example2.png
# This is a comment - lines starting with # are ignored
https://example.com/image3.jpg
```

Then run:

```bash
node download-vintage-images.js --urls vintage-urls.txt
```

## 🎨 Features

- ✅ Automatically names files with "retro-" or "modern-" prefix
- ✅ Skips files that already exist
- ✅ Validates image types
- ✅ Handles errors gracefully
- ✅ Shows download progress
- ✅ Creates directory if it doesn't exist

## 📁 Output

Images are saved to: `server/public/styles/`

File naming format:

- `retro-{name}.jpg` (default)
- `modern-{name}.png` (with --prefix modern)

## 🔧 Options

- `--prefix <name>`: Set filename prefix (default: "retro")
- `--urls <file>`: Read URLs from a text file
- Direct URLs: Just pass URLs as arguments

## 💡 Tips

1. **Start Small**: Test with 2-3 images first
2. **Check Licenses**: Make sure images are public domain or free to use
3. **Use Direct URLs**: Use direct image URLs (ending in .jpg, .png, etc.)
4. **Wikimedia Commons**: Best source for public domain vintage images
5. **File Size**: Script limits downloads to 10MB per image

## 🐛 Troubleshooting

**"Failed to download" errors:**

- Check that the URL is a direct image link (not a webpage)
- Verify the image is publicly accessible
- Some sites block direct downloads - try a different source

**"Not an image" errors:**

- The URL might point to a webpage, not an image
- Try right-clicking the image and selecting "Copy image address"

**Files not appearing:**

- Check `server/public/styles/` directory
- Restart the server to see new images

## 📚 Example Workflow

1. Visit Wikimedia Commons: https://commons.wikimedia.org/wiki/Category:1950s_fashion
2. Find 5-10 images you like
3. Copy their image addresses
4. Create `vintage-urls.txt` with the URLs
5. Run: `node download-vintage-images.js --urls vintage-urls.txt`
6. Restart your server
7. Images appear in the Style Gallery!

Happy downloading! 🎨
