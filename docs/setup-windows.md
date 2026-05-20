# Windows Setup Guide: Local Personal Communication Agent

## 1. Target Device and Goal
- OS: Windows laptop
- CPU: AMD Ryzen 5 2500U
- RAM: 20GB
- Storage: 1TB
- Goal: laptop acts as always-on local host, accessed from phone/tablet through Tailscale.

## 2. Pre-Setup Checklist
1. Log in with a Windows account that has Administrator rights.
2. Plug in charger during setup.
3. Ensure at least 80GB free storage before installing all tools and Docker images.
4. Prepare one browser for normal daily use and one separate browser profile for automation.

## 3. Power and System Settings (Do This First)

### 3.1 Sleep Behavior When Plugged In
1. Open `Settings` -> `System` -> `Power & battery`.
2. Open `Screen and sleep`.
3. Set `When plugged in, put my device to sleep after` to `Never`.
4. Keep screen timeout separate (for example 10-15 minutes) if you want the screen off but system still running.

### 3.2 Recommended Power Mode for This Hardware
1. In `Power & battery`, set `Power mode` to `Balanced`.
2. Use `Best performance` only while building containers/models, then return to `Balanced` for thermals on Ryzen 5 2500U.

### 3.3 Windows Update Active Hours
1. Open `Settings` -> `Windows Update`.
2. Set `Active hours` to your work window (example: `08:00-23:00`).
3. Enable update installation outside active hours to reduce interruption.

## 4. Install Git
1. Download Git for Windows from the official site.
2. Run installer with defaults, but ensure these options:
- `Git from the command line and also from 3rd-party software`.
- `Use bundled OpenSSH`.
- `Checkout Windows-style, commit Unix-style line endings` (recommended default).
3. Open PowerShell and verify:
```powershell
git --version
```

## 5. Install VS Code
1. Download Visual Studio Code (User Installer x64).
2. During install, enable:
- `Add to PATH`.
- `Register Code as editor for supported file types`.
- `Add Open with Code` context menu options.
3. Verify:
```powershell
code --version
```
4. Install extensions after first launch:
- Python
- Docker
- ESLint
- Prettier
- GitLens (optional but helpful)

## 6. Install Node.js LTS
1. Download Node.js `LTS` for Windows x64.
2. Install with defaults (includes npm).
3. Verify:
```powershell
node -v
npm -v
```
4. Optional quality-of-life:
```powershell
npm config set fund false
npm config set audit false
```

## 7. Install Python 3.12
1. Download Python `3.12.x` (Windows x86-64 installer).
2. On first installer screen, check `Add python.exe to PATH`.
3. Choose `Customize installation` -> keep `pip` and `venv` enabled.
4. Verify:
```powershell
python --version
pip --version
```
5. Create a quick test venv:
```powershell
python -m venv %USERPROFILE%\venvs\test312
%USERPROFILE%\venvs\test312\Scripts\activate
python --version
deactivate
```

## 8. Install Docker Desktop
1. Enable virtualization in BIOS/UEFI if not already enabled (`SVM Mode` on AMD).
2. In Windows Features, enable:
- `Virtual Machine Platform`
- `Windows Subsystem for Linux`
3. Reboot.
4. Install Docker Desktop for Windows.
5. In Docker settings:
- Use `WSL 2` backend.
- Limit resources for this laptop class (recommended start):
  - CPUs: `4`
  - Memory: `8GB`
  - Swap: `2GB`
  - Disk image limit: `120GB`
6. Verify:
```powershell
docker --version
docker compose version
docker run hello-world
```

## 9. Install Tailscale
1. Install Tailscale for Windows.
2. Sign in and join your tailnet.
3. Keep `Run unattended` enabled so service reconnects after reboot.
4. Verify in PowerShell:
```powershell
tailscale status
tailscale ip -4
```
5. From phone/tablet (also logged into same tailnet), open the laptop tailnet IP in browser with your app port later (example `http://100.x.y.z:3000`).

## 10. Install Ollama
1. Install Ollama for Windows.
2. Ensure Ollama service starts successfully.
3. Verify:
```powershell
ollama --version
ollama list
```
4. Pull one lightweight model first for Ryzen 5 2500U testing:
```powershell
ollama pull qwen2.5:3b
```
5. Run a smoke test:
```powershell
ollama run qwen2.5:3b "Say hello"
```

## 11. Install Codex
Use one of these paths depending on your workflow.

### 11.1 Codex in ChatGPT App/Web Workflow
1. Install/open the ChatGPT desktop app or web app.
2. Sign in with your OpenAI account.
3. Confirm Codex is available in your workspace.
4. Keep this account separate from shared/public machine profiles.

### 11.2 Codex CLI Workflow
1. Install the Codex CLI package using the official OpenAI instructions for your environment.
2. Authenticate with your OpenAI account/API key as required by your setup.
3. Verify CLI can run a basic command.

## 12. Browser Profile Separation for Automation (Required)
Create separate browser profiles to avoid session/token mix-ups.

1. Use Chromium-based browser profile manager (Edge/Chrome/Brave).
2. Create at least 2 profiles:
- `Personal`: normal daily browsing.
- `PCA-Automation`: only for Slack/WhatsApp Web/LINE web sessions related to the agent.
3. In `PCA-Automation` profile:
- Disable unnecessary extensions.
- Turn off password autofill for unrelated accounts.
- Pin only required tabs (Slack, WhatsApp Web, LINE).
- Disable tab sleeping for those pinned tabs if needed.
4. Never use personal social/email sessions in `PCA-Automation`.
5. If session confusion happens, clear only the automation profile data, not your personal profile.

## 13. Post-Install Verification Matrix
Run and confirm all commands below pass:

```powershell
git --version
code --version
node -v
npm -v
python --version
pip --version
docker --version
docker compose version
tailscale status
ollama --version
```

Checklist:
- Laptop does not sleep when plugged in.
- Windows Update active hours are configured.
- Docker starts without error.
- Tailscale connected and reachable from phone/tablet.
- Ollama can run a test prompt.
- Automation browser profile is separated and ready.

## 14. Recommended Maintenance Routine
- Weekly: `Windows Update` + reboot at a controlled time.
- Weekly: `docker system df` and clean unused images if storage grows.
- Monthly: rotate important tokens/sessions used in automation profile.
- Before major coding session: ensure Tailscale connected and charger plugged in.
