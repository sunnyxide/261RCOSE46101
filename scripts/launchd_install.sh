#!/usr/bin/env bash
# Install the orchestrator as a launchd service on Mac Mini.
# Survives reboots and keeps the lab running 24/7.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.orbt.research-lab.plist"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.orbt.research-lab</string>
    <key>ProgramArguments</key>
    <array>
        <string>${REPO_DIR}/.venv/bin/python</string>
        <string>-m</string>
        <string>orchestrator.scheduler</string>
        <string>run</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${REPO_DIR}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>${REPO_DIR}/.venv/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>${REPO_DIR}/logs/scheduler.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>${REPO_DIR}/logs/scheduler.stderr.log</string>
</dict>
</plist>
EOF

mkdir -p "${REPO_DIR}/logs"
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load -w "$PLIST"
echo "Installed launchd service. Logs: ${REPO_DIR}/logs/"
echo "Stop: launchctl unload $PLIST"
echo "Start: launchctl load -w $PLIST"
