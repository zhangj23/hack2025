# Quick Setup Guide

## Prerequisites
- Node.js (v14 or higher)
- npm or yarn

## Installation Steps

1. **Navigate to the project directory:**
   ```bash
   cd doctor_note
   ```

2. **Install all dependencies:**
   ```bash
   npm run install-all
   ```
   This will install dependencies for:
   - Root package (concurrently for running both servers)
   - Backend server (Express)
   - Frontend client (React + Tailwind + TensorFlow.js)

3. **Start the development servers:**
   ```bash
   npm run dev
   ```
   This starts both:
   - Backend API server on `http://localhost:5000`
   - Vite frontend on `http://localhost:3000`
   
   **Note:** The project now uses Vite instead of Create React App for faster development and builds.

4. **Open your browser:**
   Navigate to `http://localhost:3000` to see the app!

## Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Install root dependencies
npm install

# Install backend dependencies
cd server
npm install
cd ..

# Install frontend dependencies
cd client
npm install
cd ..
```

Then run servers separately:
```bash
# Terminal 1 - Backend
cd server
npm run dev

# Terminal 2 - Frontend (Vite)
cd client
npm run dev
```

## Troubleshooting

### PowerShell Execution Policy Error (Windows)

If you see an error like "running scripts is disabled on this system", you have two options:

**Option 1: Change Execution Policy (Recommended)**
Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try the npm commands again.

**Option 2: Bypass for Current Session**
Run this command in your current PowerShell session:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```
Then run your npm commands.

**Option 3: Use Command Prompt Instead**
Open Command Prompt (cmd.exe) instead of PowerShell and run the npm commands there.

**Option 4: Use Manual Installation**
Follow the "Manual Setup (Alternative)" section below, which uses individual commands that may work better.

### Other Issues

- **Port already in use**: Change the port in `server/index.js` or set `PORT` environment variable
- **TensorFlow.js not loading**: Check browser console, ensure you have internet connection for CDN
- **Tailwind styles not applying**: Make sure PostCSS is configured correctly in `client/postcss.config.js`

## Production Build

To create a production build:

```bash
cd client
npm run build
```

The built files will be in `client/build/` and can be served by the Express server in production mode.

