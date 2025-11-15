# PowerShell script to download sample style images
# Run this from the upcycler directory: .\download-styles.ps1

$stylesDir = "server\public\styles"

# Create directory if it doesn't exist
if (-not (Test-Path $stylesDir)) {
    New-Item -ItemType Directory -Path $stylesDir -Force
}

Write-Host "Style Image Downloader" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script helps you download style images." -ForegroundColor Yellow
Write-Host ""
Write-Host "Option 1: Manual Download (Recommended)" -ForegroundColor Green
Write-Host "1. Visit: https://commons.wikimedia.org/wiki/Category:1950s_fashion" -ForegroundColor White
Write-Host "2. Click on images you like" -ForegroundColor White
Write-Host "3. Click 'Download' button" -ForegroundColor White
Write-Host "4. Save to: $stylesDir" -ForegroundColor White
Write-Host ""
Write-Host "Option 2: Use this script with image URLs" -ForegroundColor Green
Write-Host "Edit this script and add image URLs, then run it again." -ForegroundColor White
Write-Host ""

# Example URLs (replace with actual public domain image URLs)
$exampleUrls = @(
    # Add your image URLs here
    # Example format:
    # "https://upload.wikimedia.org/wikipedia/commons/thumb/.../image.jpg"
)

if ($exampleUrls.Count -eq 0) {
    Write-Host "No URLs configured. Here are some resources:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Retro Images:" -ForegroundColor Cyan
    Write-Host "  - https://commons.wikimedia.org/wiki/Category:1950s_fashion" -ForegroundColor White
    Write-Host "  - https://www.loc.gov/pictures/search/?q=1950s+fashion" -ForegroundColor White
    Write-Host "  - https://archive.org/details/vintagefashion" -ForegroundColor White
    Write-Host ""
    Write-Host "Modern Images:" -ForegroundColor Cyan
    Write-Host "  - https://unsplash.com/s/photos/abstract-pattern" -ForegroundColor White
    Write-Host "  - https://www.pexels.com/search/geometric%20pattern/" -ForegroundColor White
    Write-Host ""
    Write-Host "To download images:" -ForegroundColor Yellow
    Write-Host "1. Visit the URLs above" -ForegroundColor White
    Write-Host "2. Download images manually" -ForegroundColor White
    Write-Host "3. Save them to: $stylesDir" -ForegroundColor White
} else {
    Write-Host "Downloading $($exampleUrls.Count) images..." -ForegroundColor Green
    
    $counter = 1
    foreach ($url in $exampleUrls) {
        try {
            $filename = "style-$counter.jpg"
            $filepath = Join-Path $stylesDir $filename
            Write-Host "Downloading: $filename" -ForegroundColor Yellow
            Invoke-WebRequest -Uri $url -OutFile $filepath -ErrorAction Stop
            Write-Host "  ✓ Saved to $filepath" -ForegroundColor Green
            $counter++
        } catch {
            Write-Host "  ✗ Failed to download: $url" -ForegroundColor Red
            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "Done! Images saved to: $stylesDir" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Add more images to: $stylesDir" -ForegroundColor White
Write-Host "2. Restart the server to see them in the gallery" -ForegroundColor White
Write-Host "3. Use descriptive names like retro-1950s-ad.png" -ForegroundColor White

