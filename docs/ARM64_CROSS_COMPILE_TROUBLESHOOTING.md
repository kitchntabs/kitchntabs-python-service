# ARM64 cross-compile: bug fix + Docker Desktop corruption (2026-07-02)

## Background

`kt_service`, `print_service`, and `tts_service` are PyInstaller-bundled native
executables. They must be built *on the target OS* — a binary built on macOS is
Mach-O format, which a Linux Raspberry Pi cannot execute. `npm run
build:docker:<arch>:<config>` (`build-docker.js`) exists to produce real Linux
ELF binaries from a Mac, using Docker (`docker buildx build --platform
linux/arm64 ...`) to get a genuine Linux environment.

Note: on an Apple Silicon Mac targeting `linux/arm64`, this is **not** CPU
emulation (host and target CPU arch already match) — Docker is only needed for
the Linux OS/ABI, not for QEMU instruction translation. The "Setting up QEMU"
step in the build script is generic across all its supported targets
(`x64`, `arm64`, `armv7l`) and is a no-op in the arm64-on-M1 case.

## Symptom that started this

A Raspberry Pi (arm64, Debian) deployment failed at runtime:
```
[error] > /opt/kitchntabs/resources/python-service/kt_service: 1: Syntax error: "(" unexpected
```
The `electron-builder.config.js` `afterPack` hook (which copies the
per-architecture Python binaries into the packaged app) logged the cause
directly: `tts_service` used a **Docker-built binary for arm64**, but
`kt_service`/`print_service` fell back to a **native build** (the Mac's own
Mach-O binary) because no Docker-built arm64 binary existed yet at
`kt_service_builds/arm64/`. The Pi's shell tried to exec the Mach-O file,
the kernel rejected it, the shell fell back to interpreting the raw bytes as
a script, and hit a `(` early in the binary — hence "Syntax error".

## Bug found and fixed: `build-docker.js` `CONFIG_MAP`

Running `npm run build:docker:arm64:prod` failed immediately:
```
❌ Config file not found: config.kitchntabs.prod.yaml
```
`CONFIG_MAP.prod` / `CONFIG_MAP.production` pointed at
`config.kitchntabs.prod.yaml`, which has never existed in this repo. The real
file is `config.kitchntabs.production.yaml` (confirmed against what
`build-python-service.js`, the Electron pre-build step, actually copies).

**Fix** (`build-docker.js`, `CONFIG_MAP`):
```js
const CONFIG_MAP = {
  ngrok: 'config.kitchntabs.ngrok.yaml',
  prod: 'config.kitchntabs.production.yaml',        // was: config.kitchntabs.prod.yaml
  production: 'config.kitchntabs.production.yaml',  // was: config.kitchntabs.prod.yaml
  dev: 'config.dev.yaml'
};
```

## Docker Desktop VM corruption (environment issue, not a code bug)

After the config fix, the build still failed — this time in Docker itself,
and it took several rounds to isolate from an actual script bug:

1. **`kt-builder`'s endpoint was stale**: `docker buildx ls` showed the
   buildx builder the script uses (`kt-builder`, a `docker-container` driver)
   pointing at `unix:///var/run/docker.sock`, which doesn't exist on this
   machine — Docker Desktop's real socket is
   `~/.docker/run/docker.sock` (context `desktop-linux`). `docker buildx use
   desktop-linux` didn't stick because `build-docker.js` (line ~135) always
   re-selects a builder literally named `kt-builder` if one exists.
2. **Removing and recreating `kt-builder` didn't fix it**: even a freshly
   pulled `moby/buildkit:buildx-stable-1` container failed to start:
   ```
   ERROR: Error response from daemon: failed to create task for container:
   failed to start shim: start failed: : fork/exec /usr/bin/containerd-shim-runc-v2: exec format error
   ```
3. **A full Docker Desktop restart** (`osascript -e 'quit app "Docker"'` then
   `open -a Docker`) fixed the stale socket/context issue (`kt-builder`'s
   endpoint corrected itself to `desktop-linux`), but the *same* `exec format
   error` reappeared on a truly fresh container.
4. **Isolated to Docker Desktop itself, not buildx**: a plain
   `docker run --rm --platform linux/arm64 hello-world` failed the same way,
   on a *different* binary (`/usr/bin/unpigz`, the layer-decompression tool):
   ```
   docker: could not get decompression stream: fork/exec /usr/bin/unpigz: exec format error
   ```
   This proves the corruption is in Docker Desktop's Linux VM itself (core
   system binaries are broken/wrong-architecture), not in buildx or this
   repo's build script. A restart doesn't fix VM-level corruption.

**Resolution**: needs a Docker Desktop-level repair (Settings → Troubleshoot →
"Clean / Purge data", or a full reinstall) — intentionally left to be done
manually, since it wipes cached images/volumes and affects every other
container on the machine, not just this build.

## How to verify Docker Desktop is healthy before retrying

```bash
docker run --rm --platform linux/arm64 hello-world   # must actually print the hello-world banner
docker buildx ls                                      # kt-builder (if present) should show "running", not "error"/"stopped"
```
If `hello-world` fails with `exec format error` on any binary, Docker
Desktop's VM is still corrupted — do the repair above before retrying the
service build.

## Command to re-run once Docker Desktop is healthy

```bash
cd dash-python-service
npm run build:docker:arm64:prod
# or both Pi architectures in one pass:
npm run build:docker:debian   # armv7l + arm64
```
This populates `kt_service_builds/arm64/{kt_service,print_service}` (and
`armv7l/...` for the `debian` variant). Re-run the frontend's release script
afterward (`pnpm release:electron:kitchntabs-app:debian:arm64:production` in
`kitchntabs-frontend-refactored`) — `electron-builder.config.js`'s
`afterPack` hook will then find and use the Docker-built binaries for all
three services instead of falling back to the native (Mac) build.

## Alternative: skip Docker entirely, build on the Pi

Since the target is Linux ARM64 and the Pi *is* Linux ARM64, building
natively on-device sidesteps cross-compilation (and Docker Desktop) entirely:
```bash
ssh kitchntabs@10.50.48.204
# install Python + PyInstaller if not already present, then build
# kt_service/print_service from dash-python-service's source there.
```
Guarantees ABI/libc compatibility with zero cross-compile risk; slower CPU
than the Mac, but the service binaries are small.
