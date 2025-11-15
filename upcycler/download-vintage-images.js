const https = require("https");
const http = require("http");
const fs = require("fs");
const path = require("path");

// Configuration
const STYLES_DIR = path.join(__dirname, "server", "public", "styles");
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// Ensure styles directory exists
if (!fs.existsSync(STYLES_DIR)) {
  fs.mkdirSync(STYLES_DIR, { recursive: true });
  console.log(`Created directory: ${STYLES_DIR}`);
}

/**
 * Download an image from a URL
 */
function downloadImage(url, filename) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith("https") ? https : http;
    const filepath = path.join(STYLES_DIR, filename);

    // Check if file already exists
    if (fs.existsSync(filepath)) {
      console.log(`⏭️  Skipping ${filename} (already exists)`);
      resolve({ success: true, skipped: true, filename });
      return;
    }

    console.log(`📥 Downloading: ${filename}...`);

    const file = fs.createWriteStream(filepath);
    let downloadedBytes = 0;

    const request = protocol.get(url, (response) => {
      // Check if response is successful
      if (response.statusCode !== 200) {
        file.close();
        fs.unlinkSync(filepath);
        reject(
          new Error(
            `Failed to download: ${response.statusCode} ${response.statusMessage}`
          )
        );
        return;
      }

      // Check content type
      const contentType = response.headers["content-type"] || "";
      if (!contentType.startsWith("image/")) {
        file.close();
        fs.unlinkSync(filepath);
        reject(new Error(`Not an image: ${contentType}`));
        return;
      }

      // Check file size
      const contentLength = parseInt(response.headers["content-length"] || "0");
      if (contentLength > MAX_FILE_SIZE) {
        file.close();
        fs.unlinkSync(filepath);
        reject(new Error(`File too large: ${contentLength} bytes`));
        return;
      }

      response.pipe(file);

      response.on("data", (chunk) => {
        downloadedBytes += chunk.length;
        if (downloadedBytes > MAX_FILE_SIZE) {
          file.close();
          fs.unlinkSync(filepath);
          reject(new Error("File too large during download"));
        }
      });

      file.on("finish", () => {
        file.close();
        console.log(`✅ Downloaded: ${filename}`);
        resolve({ success: true, filename });
      });
    });

    request.on("error", (err) => {
      file.close();
      if (fs.existsSync(filepath)) {
        fs.unlinkSync(filepath);
      }
      reject(err);
    });

    file.on("error", (err) => {
      file.close();
      if (fs.existsSync(filepath)) {
        fs.unlinkSync(filepath);
      }
      reject(err);
    });
  });
}

/**
 * Get file extension from URL or content type
 */
function getFileExtension(url, contentType) {
  // Try to get extension from URL
  const urlMatch = url.match(/\.(jpg|jpeg|png|gif|webp|bmp)(\?|$)/i);
  if (urlMatch) {
    return urlMatch[1].toLowerCase();
  }

  // Try to get from content type
  if (contentType) {
    if (contentType.includes("jpeg") || contentType.includes("jpg")) {
      return "jpg";
    }
    if (contentType.includes("png")) return "png";
    if (contentType.includes("gif")) return "gif";
    if (contentType.includes("webp")) return "webp";
  }

  return "jpg"; // Default
}

/**
 * Generate filename from URL
 */
function generateFilename(url, index, prefix = "retro") {
  try {
    const urlObj = new URL(url);
    const pathname = urlObj.pathname;
    const basename = path.basename(pathname).replace(/\.[^/.]+$/, "");

    // Clean up the basename
    let cleanName = basename
      .replace(/[^a-z0-9]/gi, "-")
      .toLowerCase()
      .substring(0, 50);

    if (!cleanName || cleanName.length < 3) {
      cleanName = `${prefix}-image-${index}`;
    }

    const ext = getFileExtension(url);
    return `${prefix}-${cleanName}.${ext}`;
  } catch (e) {
    const ext = getFileExtension(url);
    return `${prefix}-image-${index}.${ext}`;
  }
}

/**
 * Download multiple images
 */
async function downloadImages(urls, prefix = "retro") {
  console.log(`\n🎨 Starting download of ${urls.length} images...\n`);

  const results = {
    success: [],
    failed: [],
    skipped: [],
  };

  for (let i = 0; i < urls.length; i++) {
    const url = urls[i];
    const filename = generateFilename(url, i + 1, prefix);

    try {
      const result = await downloadImage(url, filename);
      if (result.skipped) {
        results.skipped.push({ url, filename });
      } else {
        results.success.push({ url, filename });
      }
    } catch (error) {
      console.error(`❌ Failed to download ${url}:`, error.message);
      results.failed.push({ url, filename, error: error.message });
    }

    // Small delay to be respectful
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  // Print summary
  console.log(`\n📊 Download Summary:`);
  console.log(`   ✅ Success: ${results.success.length}`);
  console.log(`   ⏭️  Skipped: ${results.skipped.length}`);
  console.log(`   ❌ Failed: ${results.failed.length}`);

  if (results.failed.length > 0) {
    console.log(`\n❌ Failed downloads:`);
    results.failed.forEach(({ url, error }) => {
      console.log(`   - ${url}`);
      console.log(`     Error: ${error}`);
    });
  }

  return results;
}

// Example vintage image URLs (public domain sources)
// These are example URLs - replace with actual image URLs
const EXAMPLE_VINTAGE_URLS = [
  // Add your image URLs here
  // Example format:
  // "https://upload.wikimedia.org/wikipedia/commons/thumb/.../image.jpg",
];

// Main execution
async function main() {
  console.log("🎨 Vintage Image Downloader");
  console.log("=".repeat(50));
  console.log(`📁 Target directory: ${STYLES_DIR}\n`);

  // Get URLs from command line arguments or use examples
  const args = process.argv.slice(2);
  let urls = [];
  let prefix = "retro";

  // Parse arguments
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--prefix" && args[i + 1]) {
      prefix = args[i + 1];
      i++;
    } else if (args[i] === "--urls" && args[i + 1]) {
      // URLs from file
      try {
        const fileContent = fs.readFileSync(args[i + 1], "utf8");
        urls = fileContent
          .split("\n")
          .map((line) => line.trim())
          .filter((line) => line && !line.startsWith("#"));
        i++;
      } catch (error) {
        console.error(`Error reading file: ${error.message}`);
        process.exit(1);
      }
    } else if (args[i].startsWith("http")) {
      urls.push(args[i]);
    }
  }

  // If no URLs provided, show help
  if (urls.length === 0) {
    console.log("Usage:");
    console.log("  node download-vintage-images.js <url1> <url2> ...");
    console.log(
      "  node download-vintage-images.js --prefix modern <url1> <url2> ..."
    );
    console.log("  node download-vintage-images.js --urls urls.txt");
    console.log("\nExample:");
    console.log(
      '  node download-vintage-images.js "https://example.com/image1.jpg" "https://example.com/image2.png"'
    );
    console.log("\n💡 Tip: Get image URLs from:");
    console.log(
      "   - Wikimedia Commons (right-click image → Copy image address)"
    );
    console.log("   - Library of Congress");
    console.log("   - Internet Archive");
    console.log(
      "\n📝 To use a file with URLs, create a text file with one URL per line:"
    );
    console.log("   node download-vintage-images.js --urls image-urls.txt");
    process.exit(0);
  }

  await downloadImages(urls, prefix);
  console.log(`\n✨ Done! Images saved to: ${STYLES_DIR}\n`);
}

// Run if executed directly
if (require.main === module) {
  main().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
  });
}

module.exports = { downloadImage, downloadImages };
