# Frontend Todo: Steam External Electron App

A comprehensive guide to building a Windows desktop application using Electron.js that connects to the Steam External Backend API.

## 🎯 Project Overview

**Goal**: Create a modern Windows desktop application that displays Steam game data from our FastAPI backend.

**Tech Stack**:
- Electron.js (Desktop framework)
- React (UI framework)
- Axios (HTTP client)
- Styled-components (Styling)
- Electron-builder (Packaging)

---

## 📁 Project Structure

```
steam-external-frontend/
├── src/
│   ├── main/
│   │   ├── main.js              # Electron main process
│   │   ├── preload.js           # Preload script for security
│   │   └── menu.js              # Application menu
│   ├── renderer/
│   │   ├── components/
│   │   │   ├── AppCard.jsx      # Individual app display
│   │   │   ├── AppList.jsx      # Grid/list of apps
│   │   │   ├── AppDetail.jsx    # Detailed app view
│   │   │   ├── SearchBar.jsx    # Search and filter
│   │   │   ├── Header.jsx       # Navigation header
│   │   │   ├── Loading.jsx      # Loading states
│   │   │   └── ErrorBoundary.jsx # Error handling
│   │   ├── services/
│   │   │   ├── api.js           # API service layer
│   │   │   └── cache.js         # Data caching
│   │   ├── styles/
│   │   │   ├── GlobalStyles.js  # Global CSS
│   │   │   └── theme.js         # Steam-like theme
│   │   ├── utils/
│   │   │   ├── constants.js     # App constants
│   │   │   └── helpers.js       # Utility functions
│   │   ├── App.jsx              # Main React component
│   │   ├── index.js             # React entry point
│   │   └── index.html           # HTML template
│   └── assets/
│       ├── icons/
│       │   ├── icon.ico         # Windows icon
│       │   ├── icon.png         # App icon
│       │   └── tray.png         # System tray icon
│       └── images/
│           └── placeholder.png   # Placeholder images
├── build/
│   ├── icon.ico                 # Build icon
│   └── installer.nsh            # NSIS installer script
├── dist/                        # Built application
├── package.json
├── electron-builder.json        # Build configuration
├── .env.example                 # Environment variables
└── README.md
```

---

## 🚀 Phase 1: Basic Setup & Core Features

### 1.1 Project Initialization

```bash
# Create project directory
mkdir steam-external-frontend
cd steam-external-frontend

# Initialize npm project
npm init -y

# Install core dependencies
npm install electron react react-dom axios styled-components

# Install development dependencies
npm install --save-dev electron-builder electron-reload @babel/core @babel/preset-react webpack webpack-cli webpack-dev-server babel-loader css-loader style-loader html-webpack-plugin
```

### 1.2 Package.json Configuration

```json
{
  "name": "steam-external-app",
  "version": "1.0.0",
  "description": "Steam External Data Viewer",
  "main": "src/main/main.js",
  "homepage": "./",
  "scripts": {
    "start": "electron .",
    "dev": "webpack serve --mode development",
    "build": "webpack --mode production",
    "electron-dev": "ELECTRON_IS_DEV=true electron .",
    "pack": "electron-builder --dir",
    "dist": "electron-builder",
    "dist-win": "electron-builder --win"
  },
  "build": {
    "appId": "com.steamexternal.app",
    "productName": "Steam External Viewer",
    "directories": {
      "output": "dist"
    },
    "files": [
      "src/**/*",
      "node_modules/**/*"
    ],
    "win": {
      "target": "nsis",
      "icon": "build/icon.ico"
    }
  }
}
```

### 1.3 Electron Main Process (src/main/main.js)

```javascript
const { app, BrowserWindow, Menu, Tray, nativeImage } = require('electron');
const path = require('path');
const isDev = process.env.ELECTRON_IS_DEV === 'true';

let mainWindow;
let tray;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../assets/icons/icon.png'),
    show: false
  });

  // Load the app
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createTray() {
  const trayIcon = nativeImage.createFromPath(
    path.join(__dirname, '../assets/icons/tray.png')
  );
  tray = new Tray(trayIcon);
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show App',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
        } else {
          createWindow();
        }
      }
    },
    {
      label: 'Quit',
      click: () => {
        app.quit();
      }
    }
  ]);
  
  tray.setContextMenu(contextMenu);
  tray.setToolTip('Steam External Viewer');
}

app.whenReady().then(() => {
  createWindow();
  createTray();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
```

### 1.4 Preload Script (src/main/preload.js)

```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Add secure API methods here
  platform: process.platform,
  versions: process.versions
});
```

### 1.5 API Service (src/renderer/services/api.js)

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://steam-external-backend.onrender.com';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Get all apps
  async getAllApps() {
    try {
      const response = await this.client.get('/apps');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch apps: ${error.message}`);
    }
  }

  // Get specific app by ID
  async getAppById(appId) {
    try {
      const response = await this.client.get(`/apps/${appId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch app ${appId}: ${error.message}`);
    }
  }

  // Health check
  async ping() {
    try {
      const response = await this.client.get('/ping');
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }
}

export default new ApiService();
```

---

## 🎨 Phase 2: UI Components & Styling

### 2.1 Theme Configuration (src/renderer/styles/theme.js)

```javascript
export const theme = {
  colors: {
    primary: '#1b2838',      // Steam dark blue
    secondary: '#2a475e',    // Steam medium blue
    accent: '#66c0f4',       // Steam light blue
    success: '#5cb85c',
    warning: '#f0ad4e',
    error: '#d9534f',
    text: {
      primary: '#c7d5e0',
      secondary: '#8f98a0',
      muted: '#556772'
    },
    background: {
      primary: '#1b2838',
      secondary: '#171a21',
      card: '#2a475e'
    },
    border: '#3d4450'
  },
  fonts: {
    primary: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
    mono: '"Courier New", Courier, monospace'
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px'
  },
  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px'
  },
  shadows: {
    sm: '0 2px 4px rgba(0, 0, 0, 0.1)',
    md: '0 4px 8px rgba(0, 0, 0, 0.2)',
    lg: '0 8px 16px rgba(0, 0, 0, 0.3)'
  }
};
```

### 2.2 App Card Component (src/renderer/components/AppCard.jsx)

```jsx
import React from 'react';
import styled from 'styled-components';

const Card = styled.div`
  background: ${props => props.theme.colors.background.card};
  border-radius: ${props => props.theme.borderRadius.md};
  padding: ${props => props.theme.spacing.md};
  margin: ${props => props.theme.spacing.sm};
  box-shadow: ${props => props.theme.shadows.md};
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: ${props => props.theme.shadows.lg};
  }
`;

const AppImage = styled.img`
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: ${props => props.theme.borderRadius.sm};
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const AppTitle = styled.h3`
  color: ${props => props.theme.colors.text.primary};
  font-size: 16px;
  margin: 0 0 ${props => props.theme.spacing.xs} 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const AppPrice = styled.span`
  color: ${props => props.theme.colors.accent};
  font-weight: bold;
  font-size: 14px;
`;

const AppCard = ({ app, onClick }) => {
  const handleClick = () => {
    if (onClick) onClick(app);
  };

  return (
    <Card onClick={handleClick}>
      <AppImage 
        src={app.header_image || '/assets/images/placeholder.png'} 
        alt={app.name}
        onError={(e) => {
          e.target.src = '/assets/images/placeholder.png';
        }}
      />
      <AppTitle>{app.name}</AppTitle>
      <AppPrice>
        {app.is_free ? 'Free' : app.price_overview?.final_formatted || 'N/A'}
      </AppPrice>
    </Card>
  );
};

export default AppCard;
```

### 2.3 App List Component (src/renderer/components/AppList.jsx)

```jsx
import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import AppCard from './AppCard';
import Loading from './Loading';
import apiService from '../services/api';

const Container = styled.div`
  padding: ${props => props.theme.spacing.lg};
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: ${props => props.theme.spacing.md};
  margin-top: ${props => props.theme.spacing.lg};
`;

const ErrorMessage = styled.div`
  color: ${props => props.theme.colors.error};
  text-align: center;
  padding: ${props => props.theme.spacing.xl};
  font-size: 18px;
`;

const AppList = ({ searchTerm, onAppSelect }) => {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadApps();
  }, []);

  const loadApps = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getAllApps();
      setApps(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredApps = apps.filter(app => 
    app.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return <Loading />;
  if (error) return <ErrorMessage>Error: {error}</ErrorMessage>;

  return (
    <Container>
      <Grid>
        {filteredApps.map(app => (
          <AppCard 
            key={app.app_id} 
            app={app} 
            onClick={onAppSelect}
          />
        ))}
      </Grid>
    </Container>
  );
};

export default AppList;
```

---

## 🔍 Phase 3: Advanced Features

### 3.1 Search Bar Component (src/renderer/components/SearchBar.jsx)

```jsx
import React from 'react';
import styled from 'styled-components';

const SearchContainer = styled.div`
  display: flex;
  align-items: center;
  background: ${props => props.theme.colors.background.secondary};
  border-radius: ${props => props.theme.borderRadius.md};
  padding: ${props => props.theme.spacing.sm};
  margin: ${props => props.theme.spacing.md} 0;
`;

const SearchInput = styled.input`
  flex: 1;
  background: transparent;
  border: none;
  color: ${props => props.theme.colors.text.primary};
  font-size: 16px;
  padding: ${props => props.theme.spacing.sm};
  outline: none;
  
  &::placeholder {
    color: ${props => props.theme.colors.text.muted};
  }
`;

const SearchBar = ({ value, onChange, placeholder = "Search games..." }) => {
  return (
    <SearchContainer>
      <SearchInput
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </SearchContainer>
  );
};

export default SearchBar;
```

### 3.2 App Detail Modal (src/renderer/components/AppDetail.jsx)

```jsx
import React from 'react';
import styled from 'styled-components';

const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`;

const Modal = styled.div`
  background: ${props => props.theme.colors.background.primary};
  border-radius: ${props => props.theme.borderRadius.lg};
  padding: ${props => props.theme.spacing.xl};
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
`;

const CloseButton = styled.button`
  position: absolute;
  top: ${props => props.theme.spacing.md};
  right: ${props => props.theme.spacing.md};
  background: none;
  border: none;
  color: ${props => props.theme.colors.text.primary};
  font-size: 24px;
  cursor: pointer;
`;

const AppDetail = ({ app, onClose }) => {
  if (!app) return null;

  return (
    <Overlay onClick={onClose}>
      <Modal onClick={(e) => e.stopPropagation()}>
        <CloseButton onClick={onClose}>&times;</CloseButton>
        <h2>{app.name}</h2>
        <img src={app.header_image} alt={app.name} style={{width: '100%', marginBottom: '16px'}} />
        <p>{app.short_description}</p>
        <div>
          <strong>Price:</strong> {app.is_free ? 'Free' : app.price_overview?.final_formatted || 'N/A'}
        </div>
        <div>
          <strong>Release Date:</strong> {app.release_date?.date || 'N/A'}
        </div>
        <div>
          <strong>Developer:</strong> {app.developers?.join(', ') || 'N/A'}
        </div>
        <div>
          <strong>Publisher:</strong> {app.publishers?.join(', ') || 'N/A'}
        </div>
      </Modal>
    </Overlay>
  );
};

export default AppDetail;
```

---

## 🪟 Phase 4: Windows-Specific Features

### 4.1 Auto-Updater Setup

```javascript
// In main.js, add:
const { autoUpdater } = require('electron-updater');

// Configure auto-updater
if (!isDev) {
  autoUpdater.checkForUpdatesAndNotify();
  
  autoUpdater.on('update-available', () => {
    console.log('Update available');
  });
  
  autoUpdater.on('update-downloaded', () => {
    console.log('Update downloaded');
    autoUpdater.quitAndInstall();
  });
}
```

### 4.2 System Notifications

```javascript
// Add to main.js
const { Notification } = require('electron');

function showNotification(title, body) {
  if (Notification.isSupported()) {
    new Notification({
      title,
      body,
      icon: path.join(__dirname, '../assets/icons/icon.png')
    }).show();
  }
}
```

### 4.3 Electron Builder Configuration

```json
// electron-builder.json
{
  "appId": "com.steamexternal.app",
  "productName": "Steam External Viewer",
  "directories": {
    "output": "dist"
  },
  "files": [
    "src/**/*",
    "node_modules/**/*",
    "package.json"
  ],
  "win": {
    "target": {
      "target": "nsis",
      "arch": ["x64"]
    },
    "icon": "build/icon.ico",
    "publisherName": "Your Name",
    "verifyUpdateCodeSignature": false
  },
  "nsis": {
    "oneClick": false,
    "allowToChangeInstallationDirectory": true,
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true
  },
  "publish": {
    "provider": "github",
    "owner": "your-username",
    "repo": "steam-external-frontend"
  }
}
```

---

## 🧪 Phase 5: Testing & Quality

### 5.1 Testing Setup

```bash
# Install testing dependencies
npm install --save-dev jest @testing-library/react @testing-library/jest-dom spectron
```

### 5.2 Unit Test Example (src/renderer/components/__tests__/AppCard.test.js)

```javascript
import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from 'styled-components';
import AppCard from '../AppCard';
import { theme } from '../../styles/theme';

const mockApp = {
  app_id: '123',
  name: 'Test Game',
  header_image: 'test.jpg',
  is_free: false,
  price_overview: { final_formatted: '$19.99' }
};

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

test('renders app card with correct information', () => {
  renderWithTheme(<AppCard app={mockApp} />);
  
  expect(screen.getByText('Test Game')).toBeInTheDocument();
  expect(screen.getByText('$19.99')).toBeInTheDocument();
});
```

---

## 📦 Phase 6: Build & Distribution

### 6.1 Build Scripts

```json
// Add to package.json scripts
{
  "scripts": {
    "build:renderer": "webpack --mode production",
    "build:main": "electron-builder",
    "build": "npm run build:renderer && npm run build:main",
    "pack": "electron-builder --dir",
    "dist": "electron-builder",
    "dist:win": "electron-builder --win",
    "release": "npm run build && electron-builder --publish=always"
  }
}
```

### 6.2 Environment Configuration

```bash
# .env.example
# For local development
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development

# For production (using deployed backend)
# REACT_APP_API_URL=https://steam-external-backend.onrender.com
# REACT_APP_ENV=production
```

---

## ✅ Implementation Checklist

### Phase 1: Foundation ✅
- [ ] Project setup and dependencies
- [ ] Electron main process configuration
- [ ] Basic React app structure
- [ ] API service implementation
- [ ] Basic styling and theme

### Phase 2: Core Features ✅
- [ ] App list component
- [ ] App card component
- [ ] Search functionality
- [ ] Loading states
- [ ] Error handling

### Phase 3: Enhanced UI ✅
- [ ] App detail modal
- [ ] Responsive design
- [ ] Steam-like styling
- [ ] Image handling and placeholders
- [ ] Pagination (if needed)

### Phase 4: Windows Features ✅
- [ ] System tray integration
- [ ] Auto-updater setup
- [ ] Windows notifications
- [ ] Native installer (NSIS)
- [ ] Desktop shortcuts

### Phase 5: Polish & Testing ✅
- [ ] Unit tests
- [ ] E2E tests
- [ ] Error boundary implementation
- [ ] Performance optimization
- [ ] Code linting and formatting

### Phase 6: Distribution ✅
- [ ] Build configuration
- [ ] Code signing (optional)
- [ ] GitHub releases setup
- [ ] Documentation
- [ ] User guide

---

## 🚀 Getting Started

1. **Clone and Setup**:
   ```bash
   git clone <your-repo>
   cd steam-external-frontend
   npm install
   ```

2. **Development**:
   ```bash
   # Start the backend API first
   cd ../steam-external-backend
   python main.py
   
   # In another terminal, start the frontend
   cd ../steam-external-frontend
   npm run electron-dev
   ```

3. **Build for Production**:
   ```bash
   npm run dist:win
   ```

---

## 📚 Additional Resources

- [Electron Documentation](https://www.electronjs.org/docs)
- [React Documentation](https://reactjs.org/docs)
- [Styled Components](https://styled-components.com/docs)
- [Electron Builder](https://www.electron.build/)
- [Steam Web API](https://steamcommunity.com/dev)

---

**Note**: This is a comprehensive guide. Start with Phase 1 and gradually implement features. Each phase builds upon the previous one, ensuring a solid foundation for your Steam External Electron application.

---

## 📥 Download API Integration

### API Endpoints Overview

The backend provides three download-related endpoints:

#### 1. List Files for App
```
GET /files/{app_id}
```
- **Purpose**: Get metadata for all files associated with an app
- **Rate Limit**: None
- **Response**: JSON with file list
- **Example**: `GET /files/1245623`

#### 2. Download Individual File
```
GET /download/file/{file_id}?file_type={type}
```
- **Purpose**: Download a specific file by ID
- **Rate Limit**: 1 request per 2 minutes
- **Response**: File stream with proper headers
- **Example**: `GET /download/file/f71540c8-dd9f-4401-9ab9-15ba6a9eda8f?file_type=json`

#### 3. Download All App Files as ZIP
```
GET /download/app/{app_id}
```
- **Purpose**: Download all files for an app as a ZIP archive
- **Rate Limit**: 1 request per 2 minutes
- **Response**: ZIP file stream
- **Example**: `GET /download/app/1245623`

### Frontend Implementation Guide

#### 7.1 Download Service (src/renderer/services/downloadService.js)

```javascript
import apiService from './api';

class DownloadService {
  constructor() {
    this.downloadQueue = new Map();
    this.rateLimitCooldown = new Map();
  }

  // Get file list for an app
  async getAppFiles(appId) {
    try {
      const response = await apiService.client.get(`/files/${appId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get files for app ${appId}: ${error.message}`);
    }
  }

  // Download individual file
  async downloadFile(fileId, fileType, filename) {
    const cooldownKey = 'file_download';
    
    if (this.isRateLimited(cooldownKey)) {
      throw new Error('Rate limit active. Please wait before downloading again.');
    }

    try {
      const response = await apiService.client.get(
        `/download/file/${fileId}?file_type=${fileType}`,
        {
          responseType: 'blob',
          timeout: 30000 // 30 seconds for file downloads
        }
      );

      this.setRateLimitCooldown(cooldownKey, 2 * 60 * 1000); // 2 minutes
      this.triggerDownload(response.data, filename);
      return { success: true, message: 'File downloaded successfully' };
    } catch (error) {
      if (error.response?.status === 429) {
        this.setRateLimitCooldown(cooldownKey, 2 * 60 * 1000);
        throw new Error('Rate limit exceeded. Please wait 2 minutes before downloading again.');
      }
      throw new Error(`Download failed: ${error.message}`);
    }
  }

  // Download all app files as ZIP
  async downloadAppFiles(appId) {
    const cooldownKey = 'app_download';
    
    if (this.isRateLimited(cooldownKey)) {
      throw new Error('Rate limit active. Please wait before downloading again.');
    }

    try {
      const response = await apiService.client.get(
        `/download/app/${appId}`,
        {
          responseType: 'blob',
          timeout: 60000 // 60 seconds for ZIP downloads
        }
      );

      this.setRateLimitCooldown(cooldownKey, 2 * 60 * 1000); // 2 minutes
      this.triggerDownload(response.data, `app_${appId}_files.zip`);
      return { success: true, message: 'App files downloaded successfully' };
    } catch (error) {
      if (error.response?.status === 429) {
        this.setRateLimitCooldown(cooldownKey, 2 * 60 * 1000);
        throw new Error('Rate limit exceeded. Please wait 2 minutes before downloading again.');
      }
      throw new Error(`Download failed: ${error.message}`);
    }
  }

  // Trigger browser download
  triggerDownload(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // Rate limiting helpers
  isRateLimited(key) {
    const cooldown = this.rateLimitCooldown.get(key);
    return cooldown && Date.now() < cooldown;
  }

  setRateLimitCooldown(key, duration) {
    this.rateLimitCooldown.set(key, Date.now() + duration);
  }

  getRemainingCooldown(key) {
    const cooldown = this.rateLimitCooldown.get(key);
    if (!cooldown || Date.now() >= cooldown) return 0;
    return Math.ceil((cooldown - Date.now()) / 1000);
  }
}

export default new DownloadService();
```

#### 7.2 File List Component (src/renderer/components/FileList.jsx)

```jsx
import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import downloadService from '../services/downloadService';

const FileContainer = styled.div`
  background: ${props => props.theme.colors.background.card};
  border-radius: ${props => props.theme.borderRadius.md};
  padding: ${props => props.theme.spacing.md};
  margin: ${props => props.theme.spacing.sm} 0;
`;

const FileItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: ${props => props.theme.spacing.sm};
  border-bottom: 1px solid ${props => props.theme.colors.border};
  
  &:last-child {
    border-bottom: none;
  }
`;

const FileInfo = styled.div`
  flex: 1;
`;

const FileName = styled.div`
  color: ${props => props.theme.colors.text.primary};
  font-weight: 500;
`;

const FileDetails = styled.div`
  color: ${props => props.theme.colors.text.secondary};
  font-size: 12px;
  margin-top: 4px;
`;

const DownloadButton = styled.button`
  background: ${props => props.disabled ? props.theme.colors.text.muted : props.theme.colors.accent};
  color: white;
  border: none;
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius.sm};
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  font-size: 12px;
  
  &:hover:not(:disabled) {
    opacity: 0.8;
  }
`;

const BulkDownloadButton = styled.button`
  background: ${props => props.disabled ? props.theme.colors.text.muted : props.theme.colors.success};
  color: white;
  border: none;
  padding: ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius.md};
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  margin-bottom: ${props => props.theme.spacing.md};
  width: 100%;
  
  &:hover:not(:disabled) {
    opacity: 0.8;
  }
`;

const FileList = ({ appId }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloading, setDownloading] = useState(new Set());
  const [cooldowns, setCooldowns] = useState({ file: 0, app: 0 });

  useEffect(() => {
    if (appId) {
      loadFiles();
    }
  }, [appId]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCooldowns({
        file: downloadService.getRemainingCooldown('file_download'),
        app: downloadService.getRemainingCooldown('app_download')
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const loadFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await downloadService.getAppFiles(appId);
      setFiles(response.data?.files || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileDownload = async (file) => {
    const downloadId = file.id;
    setDownloading(prev => new Set([...prev, downloadId]));
    
    try {
      await downloadService.downloadFile(
        file.id,
        file.file_type,
        file.filename
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setDownloading(prev => {
        const newSet = new Set(prev);
        newSet.delete(downloadId);
        return newSet;
      });
    }
  };

  const handleBulkDownload = async () => {
    setDownloading(prev => new Set([...prev, 'bulk']));
    
    try {
      await downloadService.downloadAppFiles(appId);
    } catch (err) {
      setError(err.message);
    } finally {
      setDownloading(prev => {
        const newSet = new Set(prev);
        newSet.delete('bulk');
        return newSet;
      });
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  if (loading) return <div>Loading files...</div>;
  if (error) return <div style={{color: 'red'}}>Error: {error}</div>;
  if (!files.length) return <div>No files found for this app.</div>;

  return (
    <FileContainer>
      <h3>App Files ({files.length})</h3>
      
      <BulkDownloadButton
        onClick={handleBulkDownload}
        disabled={downloading.has('bulk') || cooldowns.app > 0}
      >
        {downloading.has('bulk') 
          ? 'Downloading ZIP...' 
          : cooldowns.app > 0 
            ? `Download All Files (${cooldowns.app}s)` 
            : 'Download All Files as ZIP'
        }
      </BulkDownloadButton>

      {files.map(file => (
        <FileItem key={file.id}>
          <FileInfo>
            <FileName>{file.filename}</FileName>
            <FileDetails>
              Type: {file.file_type.toUpperCase()} | 
              Size: {formatFileSize(file.size)} | 
              Uploaded: {new Date(file.uploaded_at).toLocaleDateString()}
            </FileDetails>
          </FileInfo>
          <DownloadButton
            onClick={() => handleFileDownload(file)}
            disabled={downloading.has(file.id) || cooldowns.file > 0}
          >
            {downloading.has(file.id) 
              ? 'Downloading...' 
              : cooldowns.file > 0 
                ? `Download (${cooldowns.file}s)` 
                : 'Download'
            }
          </DownloadButton>
        </FileItem>
      ))}
    </FileContainer>
  );
};

export default FileList;
```

#### 7.3 Integration with App Detail Component

```jsx
// Update AppDetail.jsx to include FileList
import FileList from './FileList';

const AppDetail = ({ app, onClose }) => {
  if (!app) return null;

  return (
    <Overlay onClick={onClose}>
      <Modal onClick={(e) => e.stopPropagation()}>
        <CloseButton onClick={onClose}>&times;</CloseButton>
        <h2>{app.name}</h2>
        <img src={app.header_image} alt={app.name} style={{width: '100%', marginBottom: '16px'}} />
        <p>{app.short_description}</p>
        
        {/* Existing app details */}
        <div>
          <strong>Price:</strong> {app.is_free ? 'Free' : app.price_overview?.final_formatted || 'N/A'}
        </div>
        <div>
          <strong>Release Date:</strong> {app.release_date?.date || 'N/A'}
        </div>
        
        {/* Add file list component */}
        <FileList appId={app.app_id} />
      </Modal>
    </Overlay>
  );
};
```

### Implementation Notes

#### Rate Limiting Considerations
- Download endpoints have a 2-minute cooldown
- UI shows remaining cooldown time
- Graceful handling of rate limit errors
- Separate cooldowns for file and app downloads

#### File Type Support
- JSON files (.json)
- Lua scripts (.lua) 
- Manifest files (.manifest)
- VDF files (.vdf)

#### Error Handling
- Network timeouts (30s for files, 60s for ZIP)
- Rate limit exceeded messages
- File not found errors
- Invalid app ID handling

#### Security Considerations
- Files downloaded through blob URLs
- Automatic cleanup of object URLs
- No direct file system access
- Rate limiting prevents abuse

### Testing the Download Feature

1. **Test File Listing**:
   ```javascript
   // In browser console
   downloadService.getAppFiles('1245623').then(console.log);
   ```

2. **Test Individual Download**:
   ```javascript
   // Download a specific file
   downloadService.downloadFile('file-id', 'json', 'test.json');
   ```

3. **Test Bulk Download**:
   ```javascript
   // Download all app files
   downloadService.downloadAppFiles('1245623');
   ```

### Future Enhancements

- **Download Progress**: Add progress bars for large files
- **Download History**: Track downloaded files
- **Batch Operations**: Select multiple files for download
- **Download Location**: Allow users to choose download directory
- **Resume Downloads**: Support for interrupted downloads
- **File Preview**: Preview small files before downloading