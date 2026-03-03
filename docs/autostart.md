# Auto-Start on Boot

Set up Conductor to start automatically when your machine boots, so the dashboard is always reachable.

> **Tip:** The installer (`install.sh` / `install.ps1`) offers to configure autostart for you during installation. The manual steps below are only needed if you skipped that prompt or want to customize the configuration.

## Linux (systemd)

Create a user service:

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/conductor.service << 'EOF'
[Unit]
Description=Conductor Server
After=network.target

[Service]
ExecStart=%h/.local/bin/conductor serve
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
```

Enable and start:

```bash
systemctl --user daemon-reload
systemctl --user enable conductor
systemctl --user start conductor
```

To survive logouts (run once):

```bash
loginctl enable-linger $USER
```

Check status:

```bash
systemctl --user status conductor
```

View logs:

```bash
journalctl --user -u conductor -f
```

> **Note:** If you installed Conductor to a different path, adjust the `ExecStart` line. Find it with `which conductor`.

## Linux (cron @reboot)

For systems without systemd (Alpine, Void, WSL, etc.), use cron as a lightweight alternative. The installer uses this automatically when systemd is not available.

```bash
crontab -e
```

Add this line:

```
@reboot /home/YOUR_USER/.local/bin/conductor serve >> /tmp/conductor.log 2>&1
```

Replace `/home/YOUR_USER/.local/bin/conductor` with the output of `which conductor`.

To remove:

```bash
crontab -l | grep -v 'conductor serve' | crontab -
```

> **Note:** cron `@reboot` does not restart the server if it crashes. For automatic restart, use systemd or a process supervisor.

## Linux (OpenRC)

For Gentoo, Alpine, or Artix with OpenRC. Requires root.

```bash
sudo tee /etc/init.d/conductor << 'EOF'
#!/sbin/openrc-run

name="Conductor Server"
description="Conductor terminal session orchestrator"
command="/home/YOUR_USER/.local/bin/conductor"
command_args="serve"
command_user="YOUR_USER"
command_background=true
pidfile="/run/conductor.pid"
output_log="/var/log/conductor.log"
error_log="/var/log/conductor.err"

depend() {
    need net
}
EOF

sudo chmod +x /etc/init.d/conductor
sudo rc-update add conductor default
sudo rc-service conductor start
```

Replace `YOUR_USER` with your username. To remove:

```bash
sudo rc-service conductor stop
sudo rc-update del conductor default
sudo rm /etc/init.d/conductor
```

## Linux (runit)

For Void Linux or other runit-based systems. Requires root.

```bash
sudo mkdir -p /etc/sv/conductor
sudo tee /etc/sv/conductor/run << 'EOF'
#!/bin/sh
exec chpst -u YOUR_USER /home/YOUR_USER/.local/bin/conductor serve
EOF

sudo chmod +x /etc/sv/conductor/run
sudo ln -s /etc/sv/conductor /var/service/
```

Replace `YOUR_USER` with your username. To remove:

```bash
sudo rm /var/service/conductor
sudo rm -rf /etc/sv/conductor
```

## macOS (launchd)

Create a LaunchAgent:

```bash
cat > ~/Library/LaunchAgents/com.conductor.server.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.conductor.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which conductor)</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/conductor.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/conductor.err</string>
</dict>
</plist>
EOF
```

> **Important:** Replace `$(which conductor)` with the actual path — run `which conductor` and paste the full path into the plist.

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.conductor.server.plist
```

To stop and unload:

```bash
launchctl unload ~/Library/LaunchAgents/com.conductor.server.plist
```

## Windows (Task Scheduler)

Open PowerShell as your user:

```powershell
$conductorPath = (Get-Command conductor).Source

$action = New-ScheduledTaskAction -Execute $conductorPath -Argument "serve"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName "Conductor" -Action $action -Trigger $trigger -Settings $settings -Description "Conductor Server"
```

To remove:

```powershell
Unregister-ScheduledTask -TaskName "Conductor" -Confirm:$false
```

Alternatively, place a shortcut to `conductor serve` in your Startup folder:

```
Win+R → shell:startup → create shortcut → conductor serve
```

## Verify

After reboot, check that Conductor is running:

```bash
conductor status
```

Or open the dashboard in your browser at `http://127.0.0.1:7777`.
