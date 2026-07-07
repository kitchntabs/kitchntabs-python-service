# kt_service System Tray — Integration with Existing Architecture

> **Date**: 2026-07-07  
> **Context**: Integrating with existing kt_service (WebSocket), print_service, tts_service  
> **Status**: Refined Plan with Integration Points  
> **Approach**: Simplified (enhance kt_service + new GUI) vs separate daemon

---

## Current Architecture Analysis

### Existing kt_service Setup

**Three Services** (PyInstaller bundles):
- `kt_service` — WebSocket client (Laravel Reverb) → main background service
- `print_service` — Thermal printer (ESC/POS) → on-demand
- `tts_service` — Text-to-speech → on-demand

**Lifecycle** (from Electron main process):
1. Electron app starts
2. Loads `config.yaml`
3. Spawns `kt_service` as child process
4. Spawns `print_service` / `tts_service` on demand
5. Streams stdout/stderr back to renderer via IPC

**Build & Packaging**:
- Built with PyInstaller (one-file executables)
- Cross-compiled in Docker for Linux (arm64, armv7l, x64)
- Bound into Electron app via `afterPack` hook
- Located: `resources/python-service/{kt_service, print_service, tts_service}`

**Config**:
- YAML file in `resources/config.yaml`
- Sets WebSocket URL, auth endpoint, printer IDs, log paths

---

## Recommended Integration Strategy

### ✅ Leverage Existing Structure (SIMPLIFIED APPROACH)

**Instead of creating a separate daemon**, integrate the tray service directly into the **existing kt_service as an optional component**:

```
Current:                          With Tray Integration:
┌─────────────────────────┐       ┌──────────────────────────────┐
│ kt_service (WebSocket)  │       │ kt_service (WebSocket)       │
│                         │       │                              │
│ • Connects to backend   │       │ • Connects to backend        │
│ • Receives messages     │  ==>  │ • Receives messages          │
│ • Queues print/TTS jobs │       │ • Queues print/TTS jobs      │
│ • Spawns child services │       │ • Spawns child services      │
└─────────────────────────┘       │ • Emits status via file      │
                                  │ • Persists settings          │
                                  └──────────────────────────────┘
                                            ▲
                                            │ Monitors
                                            │
                                  ┌─────────────────────┐
                                  │ kt_status_tray      │
                                  │ (PyQt6 + pystray)   │
                                  │                     │
                                  │ • Shows tray icon   │
                                  │ • Overlay status    │
                                  │ • Settings dialog   │
                                  │ • Toggles features  │
                                  └─────────────────────┘
```

### Key Integration Points

1. **Communication Channel**: kt_service → kt_status_tray
   - Status file (JSON) updated by kt_service every 5 seconds
   - Tray reads file every 1 second (lightweight polling)
   - Simple, no threading issues, works on headless systems

2. **Settings Storage**: Persistent configuration
   - Settings in `config.yaml` (extended schema)
   - Tray writes to file when user changes settings
   - kt_service reads settings on startup and watches for changes

3. **Lifecycle**: Both services spawned by Electron
   - `kt_service` starts immediately (background, always)
   - `kt_status_tray` starts if X11/display available (optional)

4. **Build Integration**: Add tray service to existing build system
   - One additional PyInstaller config: `src/kt_status_tray.py`
   - Bound via existing `afterPack` hook
   - Located: `resources/python-service/kt_status_tray`

---

## Comparison: Why This Approach Wins

### Separate Daemon Approach (Previous)
```
Complexity: HIGH
Problems:
  ❌ Extra daemon process to manage
  ❌ Complex REST API + threading
  ❌ Settings sync between 2+ processes
  ❌ Build system: 2 new services
  ❌ kt_service doesn't know about tray
  ❌ Headless Pi: both daemon + GUI needed (waste)
```

### Enhanced kt_service + Lightweight GUI (Recommended)
```
Complexity: MEDIUM-LOW (much simpler!)
Benefits:
  ✅ Minor kt_service changes only (add status export)
  ✅ Simple file-based communication
  ✅ No threading/REST complexity
  ✅ Build: Just one new PyInstaller config
  ✅ kt_service is the source of truth
  ✅ Headless Pi: daemon works fine without GUI
  ✅ Crash isolation: Tray crash ≠ daemon death
  ✅ Settings managed in config.yaml
  ✅ Reuses existing build pipeline
```

---

## Implementation Plan

### Phase 1: kt_service Status Export (1-2 days)

**File**: `src/kt_service.py`

**Minimal Changes**:
1. Add status tracking fields
2. Add `export_status()` method to write JSON file
3. Call from main loop every 5 seconds
4. Include: connected state, message count, uptime, settings

```python
class KtService:
    def __init__(self):
        self.state = {
            'connected': False,
            'uptime_seconds': 0,
            'messages_received': 0,
            'last_message_at': None,
            'print_jobs_processed': 0,
            'tts_jobs_processed': 0,
        }
        self.settings = {
            'tts_enabled': True,
            'print_enabled': True,
            'notifications_enabled': True,
        }
    
    def export_status(self):
        """Export status to JSON file for tray app"""
        status_file = Path.home() / '.kt_service' / 'status.json'
        status_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(status_file, 'w') as f:
            json.dump({
                'state': self.state,
                'settings': self.settings,
                'pid': os.getpid(),
                'timestamp': datetime.now().isoformat(),
            }, f)
    
    async def main_loop(self):
        while True:
            # ... existing logic ...
            self.export_status()  # Update status file every 5 seconds
            await asyncio.sleep(5)
```

### Phase 2: kt_status_tray GUI (2-3 weeks)

**New File**: `src/kt_status_tray.py`

**Features**:
- System tray icon (green=connected, red=disconnected)
- Status overlay window (optional, toggleable)
- Settings dialog (enable/disable TTS, print, notifications)
- Notifications on connection changes
- Read from `~/.kt_service/status.json`
- Write changes to config file

**Dependencies**:
```
pystray==0.17.4
Pillow>=9.0.0
PyQt6>=6.0.0
pyyaml>=6.0
```

### Phase 3: Shared Tray Coordination (Reference Counting)

**Critical**: Multiple Electron apps (kitchntabs-app + kitchntabs-mall) need to share ONE system tray.

**Solution**: Reference-counted tray ownership (similar to kt_service coordination)

**State File**: `~/.kt_service/tray_apps.json`

```json
{
  "tray_owner_pid": 12345,
  "tray_owner_app": "kitchntabs-app",
  "registered_apps": [
    {
      "app_name": "kitchntabs-app",
      "app_pid": 12345,
      "registered_at": "2026-07-07T10:00:00Z",
      "kt_service_status": { /* ... */ }
    },
    {
      "app_name": "kitchntabs-mall",
      "app_pid": 12346,
      "registered_at": "2026-07-07T10:00:15Z",
      "kt_service_status": { /* ... */ }
    }
  ]
}
```

**Algorithm** (reference-counted like existing kt_service):

1. **First app to start**:
   - Acquires lock on tray_apps.json
   - Spawns `kt_status_tray` process
   - Records itself in registered_apps
   - Sets `tray_owner_pid` to its PID
   - Releases lock

2. **Second app to start** (kitchntabs-mall):
   - Acquires lock
   - Sees tray already owned (check if owner PID alive)
   - Adds itself to registered_apps
   - Does NOT spawn tray (already running)
   - Releases lock

3. **App closes**:
   - Acquires lock
   - Removes itself from registered_apps
   - If it was the owner AND registered_apps empty:
     - Kills `kt_status_tray` process
   - Releases lock

**Benefits**:
- ✅ Only ONE tray icon (no duplicates)
- ✅ Tray reflects aggregated status (all apps' kt_service states)
- ✅ Any app can register/deregister freely
- ✅ Tray survives if one app crashes
- ✅ Clean shutdown when last app closes

### Phase 4: Build System Integration (3-5 days)

**Updates**:

1. **New PyInstaller config**: `PyInstaller/kt_status_tray.spec`

2. **Update `build-docker.js`**:
   - Add `kt_status_tray` to services list
   - Docker builds all 4 services (existing 3 + new tray)

3. **Update `afterPack` hook** (electron-builder.config.js):
   - Existing loop already handles all services
   - Just verify tray binary gets bound

### Phase 5: Electron Integration - Shared Tray Coordination (3-5 days)

**File**: `kitchntabs-frontend-refactored/apps/kitchntabs-app/electron/main/index.ts` (and kitchntabs-mall)

**Implementation**:

```typescript
import { mkdir, readFile, writeFile, unlink } from 'fs/promises';
import * as path from 'path';

class TrayCoordinator {
  private stateFile: string;
  private lockDir: string;
  private appName: string;
  private appPid: number;
  private trayProcess: ChildProcess | null = null;

  constructor(appName: string) {
    this.appName = appName;
    this.appPid = process.pid;
    this.stateFile = path.join(app.getPath('appData'), 'kitchntabs-shared', 'tray_apps.json');
    this.lockDir = path.join(app.getPath('appData'), 'kitchntabs-shared', 'tray.lock.d');
  }

  private async acquireLock() {
    // Mkdir-based lock (same pattern as kt_service coordination)
    for (let i = 0; i < 10; i++) {
      try {
        await mkdir(this.lockDir, { recursive: false });
        return;
      } catch (e) {
        await new Promise(r => setTimeout(r, 100)); // Retry after 100ms
      }
    }
    throw new Error('Failed to acquire tray lock');
  }

  private async releaseLock() {
    try {
      await unlink(this.lockDir);
    } catch (e) {
      // Lock already released
    }
  }

  async registerApp() {
    await this.acquireLock();
    try {
      // Read current state
      let state: any = { registered_apps: [], tray_owner_pid: null };
      try {
        const data = await readFile(this.stateFile, 'utf-8');
        state = JSON.parse(data);
      } catch (e) {
        // File doesn't exist yet, use defaults
      }

      // Check if tray is already running
      const trayRunning = state.tray_owner_pid && 
                         this.isProcessAlive(state.tray_owner_pid);

      // Add this app to registered list
      state.registered_apps = state.registered_apps.filter(
        app => this.isProcessAlive(app.app_pid)
      );
      state.registered_apps.push({
        app_name: this.appName,
        app_pid: this.appPid,
        registered_at: new Date().toISOString(),
      });

      // If no one owns the tray, this app takes it
      if (!trayRunning) {
        state.tray_owner_pid = this.appPid;
        await this.startTray();
      }

      // Save updated state
      await writeFile(this.stateFile, JSON.stringify(state, null, 2));
    } finally {
      await this.releaseLock();
    }
  }

  async deregisterApp() {
    await this.acquireLock();
    try {
      // Read current state
      let state: any = { registered_apps: [], tray_owner_pid: null };
      try {
        const data = await readFile(this.stateFile, 'utf-8');
        state = JSON.parse(data);
      } catch (e) {
        return; // State file gone, nothing to clean up
      }

      // Remove this app
      state.registered_apps = state.registered_apps.filter(
        app => app.app_pid !== this.appPid
      );

      // If this app owned the tray and no apps left, stop tray
      if (state.tray_owner_pid === this.appPid && state.registered_apps.length === 0) {
        await this.stopTray();
        state.tray_owner_pid = null;
      }

      // Save updated state
      if (state.registered_apps.length > 0) {
        await writeFile(this.stateFile, JSON.stringify(state, null, 2));
      } else {
        await unlink(this.stateFile);
      }
    } finally {
      await this.releaseLock();
    }
  }

  private isProcessAlive(pid: number): boolean {
    try {
      return process.kill(pid, 0); // Signal 0 checks if process exists
    } catch {
      return false;
    }
  }

  private async startTray() {
    const trayPath = path.join(
      app.getAppPath(),
      'resources',
      'python-service',
      process.platform === 'win32' ? 'kt_status_tray.exe' : 'kt_status_tray'
    );

    this.trayProcess = spawn(trayPath, [], {
      detached: true,
      stdio: ['ignore', 'ignore', 'ignore']
    });
    
    this.trayProcess.unref(); // Let it live independently
    console.log(`✓ Tray started (PID: ${this.appPid})`);
  }

  private async stopTray() {
    if (this.trayProcess) {
      this.trayProcess.kill();
      this.trayProcess = null;
    }
    console.log(`✓ Tray stopped`);
  }
}

// In your app initialization:
const trayCoordinator = new TrayCoordinator('kitchntabs-app');

// On app ready
app.on('ready', async () => {
  await trayCoordinator.registerApp();
  // ... rest of initialization
});

// On app quit
app.on('quit', async () => {
  await trayCoordinator.deregisterApp();
});
```

**Files to modify**:
- `apps/kitchntabs-app/electron/main/index.ts`
- `apps/kitchntabs-mall/electron/main/index.ts` (identical logic)
- `apps/kitchntabs/electron/main/index.ts` (add tray support)

### Phase 5: Testing (1-2 weeks)

**Platforms**:
- ✅ Windows 10/11: NSSM daemon + tray icon
- ✅ macOS: daemon + menu bar icon
- ✅ Debian: systemd daemon + tray
- ✅ Raspberry Pi 64-bit: systemd daemon + tray
- ✅ Raspberry Pi 32-bit: systemd daemon + tray
- ✅ Headless Pi: daemon only (tray skipped)

---

## File Structure

```
dash-python-service/
├── src/
│   ├── kt_service.py              (modify: add status export)
│   ├── print_service.py           (no changes)
│   ├── tts_service.py             (no changes)
│   └── kt_status_tray.py          (NEW)
│
├── PyInstaller/
│   ├── kt_service.spec
│   ├── print_service.spec
│   ├── tts_service.spec
│   └── kt_status_tray.spec        (NEW)
│
├── build-docker.js                (update: add kt_status_tray)
├── docker/
│   └── Dockerfile.linux-*         (no changes)
│
├── kt_service/                    (host-native binaries + tray)
└── kt_service_builds/
    ├── x64/
    ├── arm64/
    └── armv7l/
    (each now contains all 4 services)
```

---

## Status File Schema

**Location**: `~/.kt_service/status.json`

**Updated every 5 seconds by kt_service**:

```json
{
  "pid": 12345,
  "timestamp": "2026-07-07T10:00:00Z",
  "state": {
    "connected": true,
    "uptime_seconds": 3600,
    "websocket_url": "wss://api-dev.kitchntabs.com/ws",
    "last_message_at": "2026-07-07T10:05:00Z",
    "connection_attempts": 5,
    "last_error": null
  },
  "metrics": {
    "messages_received": 142,
    "print_jobs_processed": 23,
    "tts_jobs_processed": 5,
    "errors": 0
  },
  "settings": {
    "tts_enabled": true,
    "print_enabled": true,
    "notifications_enabled": true,
    "log_level": "INFO"
  }
}
```

---

## Configuration Extension

**Extended `config.yaml`**:

```yaml
# ... existing config ...

tray:
  enabled: true
  show_overlay: true
  overlay_position: "top-right"
  notifications_enabled: true
  update_interval: 5000  # milliseconds
  
  # Keyboard shortcuts
  shortcuts:
    show_overlay: "Ctrl+Alt+K"
    settings: "Ctrl+Alt+S"
    quit: "Ctrl+Alt+Q"
  
  # Theme
  theme:
    icon_color: "#8f00cb"        # KitchnTabs purple
    text_color: "#ffffff"
    background_color: "rgba(0, 0, 0, 150)"
```

---

## Advantages

| Aspect | Rating | Why |
|--------|--------|-----|
| **Complexity** | ⭐⭐ (low) | Reuses existing architecture |
| **Integration** | ⭐⭐⭐⭐⭐ | Seamless with existing build |
| **Headless support** | ⭐⭐⭐⭐⭐ | kt_service works alone |
| **Crash isolation** | ⭐⭐⭐⭐ | Tray crashes don't kill daemon |
| **Testing** | ⭐⭐⭐⭐ | Test separately |
| **Performance** | ⭐⭐⭐⭐⭐ | Minimal overhead |
| **Maintainability** | ⭐⭐⭐⭐ | Few code changes |
| **Cross-platform** | ⭐⭐⭐⭐⭐ | Windows/Linux/macOS |

---

## Success Criteria

✅ kt_service exports status to JSON file  
✅ kt_status_tray reads and displays status  
✅ Settings changes persist in config.yaml  
✅ Headless Raspberry Pi works (daemon only, no crash)  
✅ Windows, macOS, Linux all show tray icon  
✅ Tray app crashes don't kill kt_service  
✅ All services build in Docker pipeline  
✅ .deb/.exe/.dmg packages include all 4 binaries  
✅ < 1% CPU overhead on modern hardware  

---

## Estimated Effort

| Phase | Duration | Notes |
|-------|----------|-------|
| 1: Status export | 1-2 days | Minimal kt_service changes |
| 2: GUI development | 2 weeks | PyQt6 + pystray implementation |
| 3: Shared tray coordination | 2-3 days | Reference counting + mutex logic |
| 4: Build integration | 3-5 days | Docker + PyInstaller configs |
| 5: Electron integration | 4-5 days | Spawn logic + tray coordinator + multi-app |
| 6: Testing | 1-2 weeks | Single app + multi-app scenarios |
| **Total** | **~5-6 weeks** | **1 person** |

---

---

## Multi-App Tray Sharing Architecture

### Problem Statement

With multiple Electron apps (kitchntabs-app, kitchntabs-mall, kitchntabs), we need:
- ✅ ONE system tray icon (not multiple)
- ✅ Shared status display for all apps
- ✅ Reference-counted lifecycle management
- ✅ Any app can start/stop, tray survives independent of any single app
- ✅ Works across Windows, macOS, Linux

### Solution: Shared Reference-Counted Tray Process

**Architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│ Machine-Wide Shared State: ~/.kt_service/tray_apps.json        │
│                                                                 │
│ {                                                               │
│   "tray_owner_pid": 12345,         ← PID of app that owns tray │
│   "tray_owner_app": "kitchntabs-app",                          │
│   "registered_apps": [                                          │
│     {                                                           │
│       "app_name": "kitchntabs-app",                            │
│       "app_pid": 12345,            ← App 1                     │
│       "registered_at": "2026-07-07T10:00:00Z"                  │
│     },                                                          │
│     {                                                           │
│       "app_name": "kitchntabs-mall",                           │
│       "app_pid": 12346,            ← App 2                     │
│       "registered_at": "2026-07-07T10:00:15Z"                  │
│     }                                                           │
│   ]                                                             │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
                           ▲
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼───────┐    ┌───▼───────┐    ┌───▼──────────┐
    │ App 1     │    │ App 2     │    │ Single Tray  │
    │ PID:12345 │    │ PID:12346 │    │ PID: varies  │
    │           │    │           │    │              │
    │ (reads)   │    │ (reads)   │    │ (reads)      │
    │ Acquires  │    │ Acquires  │    │ Monitors     │
    │ lock      │    │ lock      │    │ registered_  │
    │ Registers │    │ Registers │    │ apps         │
    │ to JSON   │    │ to JSON   │    │              │
    └─────────────────────────────────────────────────┘
```

### Tray Lifecycle: Step-by-Step

**Scenario 1: kitchntabs-app starts first**

```
1. kitchntabs-app (PID 12345) initializes
2. Tries to acquire lock on tray_apps.json
3. ✅ Lock acquired (first app)
4. Reads tray_apps.json (doesn't exist yet or empty)
5. Checks: is tray already running? NO
6. Spawns kt_status_tray process (detached, PID 12350)
7. Writes to tray_apps.json:
   {
     "tray_owner_pid": 12345,
     "tray_owner_app": "kitchntabs-app",
     "registered_apps": [
       { "app_name": "kitchntabs-app", "app_pid": 12345, ... }
     ]
   }
8. Releases lock
9. Tray icon appears on taskbar ✓
```

**Scenario 2: kitchntabs-mall starts (app already running)**

```
1. kitchntabs-mall (PID 12346) initializes
2. Tries to acquire lock on tray_apps.json
3. ✅ Lock acquired (waits for App 1 to release)
4. Reads tray_apps.json
5. Checks: is tray already running? YES (owner_pid=12345, alive)
6. Does NOT spawn tray (already running!)
7. Adds itself to registered_apps:
   {
     "tray_owner_pid": 12345,
     "tray_owner_app": "kitchntabs-app",
     "registered_apps": [
       { "app_name": "kitchntabs-app", "app_pid": 12345, ... },
       { "app_name": "kitchntabs-mall", "app_pid": 12346, ... }  ← Added
     ]
   }
8. Releases lock
9. Tray icon still shows ONE icon (shared) ✓
```

**Scenario 3: kitchntabs-app closes**

```
1. kitchntabs-app is closing
2. Tries to acquire lock on tray_apps.json
3. ✅ Lock acquired
4. Reads tray_apps.json
5. Removes "app_pid": 12345 from registered_apps
6. Checks: am I the tray owner? YES (owner_pid=12345)
7. Checks: are there other registered apps? YES (kitchntabs-mall=12346)
8. Does NOT kill tray (other apps still need it)
9. Assigns ownership to next alive app:
   {
     "tray_owner_pid": 12346,  ← Ownership transferred
     "tray_owner_app": "kitchntabs-mall",
     "registered_apps": [
       { "app_name": "kitchntabs-mall", "app_pid": 12346, ... }
     ]
   }
10. Releases lock
11. Tray icon continues showing ✓
```

**Scenario 4: kitchntabs-mall closes (last app)**

```
1. kitchntabs-mall is closing
2. Tries to acquire lock
3. ✅ Lock acquired
4. Reads tray_apps.json
5. Removes itself from registered_apps
6. Checks: am I the tray owner? YES
7. Checks: are there other apps? NO (empty list)
8. ✅ KILLS kt_status_tray process
9. Deletes tray_apps.json (cleanup)
10. Releases lock
11. Tray icon disappears from taskbar ✓
```

### Crash Scenarios Handled

**App 1 crashes (tray owner)**:
```
1. App 2 is running, reads tray_apps.json
2. Tries to refresh (periodic check or on event)
3. Checks: is owner (App 1, PID 12345) still alive?
4. NO - process dead, acquire lock and update
5. Assigns ownership to App 2
6. Tray continues running (never killed) ✓
```

**App crashes while holding lock**:
```
1. Process dies, lock directory still exists
2. Next app to start acquires lock (retries after 100ms, max 1 second)
3. On success, checks stale PIDs and cleans up
4. Resumes normally ✓
```

**Tray process crashes**:
```
1. kt_status_tray dies unexpectedly
2. On next app heartbeat or check, detects owner_pid not alive
3. Any app can acquire lock and respawn tray
4. Status monitoring resumes ✓
```

### Data Consistency

**Mutex**: mkdir-based lock (atomic on all platforms)
```typescript
// Acquire
mkdir(~/.kt_service/tray.lock.d)  // Atomic, fails if exists

// Release
rmdir(~/.kt_service/tray.lock.d)  // Clean up
```

**Reads/Writes**: Always within lock to prevent corruption
```typescript
acquireLock()
  try {
    readFile()
    modify()
    writeFile()
  } finally {
    releaseLock()
  }
```

**Cleanup**: Remove stale app entries from registered_apps
```typescript
// Before any operation, filter dead PIDs
registered_apps = registered_apps.filter(app => isProcessAlive(app.app_pid))
```

---

## Next Steps

1. ✅ Approve simplified + shared-tray integration approach
2. 📝 Create kt_status_tray.py skeleton
3. 🔧 Modify kt_service.py to export status.json
4. 🔧 Implement TrayCoordinator in Electron main
5. 🏗️ Add PyInstaller config for tray
6. 🧪 Test scenarios: single app, multi-app, app crashes, tray crashes
7. 📦 Integrate into Electron build pipeline

---

**This integrated approach with reference-counted tray sharing**:
- ✅ Reuses existing kt_service architecture
- ✅ Handles multiple Electron apps elegantly
- ✅ ONE system tray icon (not multiple)
- ✅ Crash-resilient (any component can fail independently)
- ✅ Clean lifecycle management with proper cleanup
- ✅ Cross-platform (Windows mutex via mkdir works same way)



