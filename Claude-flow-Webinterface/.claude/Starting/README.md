# Claude-Flow Starting Scripts

This directory contains all startup scripts for Claude-Flow services.

## 🚀 Quick Start

### macOS Users
Double-click `quick-start.command` in Finder to launch the GUI automatically.

### Command Line Users
Run any of the following scripts:

## Available Scripts

### 🌐 GUI Scripts

#### `start-gui.sh`
- Starts the complete GUI with WebSocket server
- Opens browser automatically
- Installs dependencies if needed
- **Usage**: `bash start-gui.sh`

#### `start-gui-server-only.sh`
- Starts only the WebSocket server
- No browser auto-open
- Good for headless/remote setups
- **Usage**: `bash start-gui-server-only.sh`

#### `start-gui-dev.sh`
- Development mode with auto-reload
- Watches for file changes
- Requires nodemon
- **Usage**: `bash start-gui-dev.sh`

### 🎯 Service Scripts

#### `start-all-services.sh`
- Starts GUI server
- Initializes swarm
- Opens control center
- Complete setup in one command
- **Usage**: `bash start-all-services.sh`

## 📍 Service Endpoints

After starting, services are available at:

- **GUI**: http://localhost:8080
- **WebSocket**: ws://localhost:8081
- **Health Check**: http://localhost:8080/health
- **API**: http://localhost:8080/api/

## 🛠️ Troubleshooting

### Port Already in Use
If you see "Port 8080 already in use":
```bash
# Find process using port
lsof -i :8080

# Kill process (replace PID with actual process ID)
kill -9 PID
```

### Dependencies Not Installed
If npm packages are missing:
```bash
cd ../../gui
npm install
```

### Permission Denied
Make scripts executable:
```bash
chmod +x *.sh
chmod +x *.command
```

## 🔧 Configuration

### Change Ports
Edit server.js to change default ports:
```javascript
const PORT = process.env.PORT || 8080;
const WS_PORT = process.env.WS_PORT || 8081;
```

### Environment Variables
Set custom ports:
```bash
PORT=3000 WS_PORT=3001 bash start-gui-server-only.sh
```

## 📝 Notes

- All scripts navigate to the correct directory automatically
- Dependencies are checked and installed if needed
- Scripts provide clear status messages
- Use Ctrl+C to stop services gracefully

## 🆘 Help

For issues or questions:
- Check main README: `../../gui/README.md`
- GitHub Issues: https://github.com/ruvnet/claude-flow/issues
- Documentation: https://github.com/ruvnet/claude-flow

---

*These scripts are part of the Claude-Flow Control Center v2.0.0-alpha.73*