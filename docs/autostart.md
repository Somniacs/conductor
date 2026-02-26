# Auto-Start on Boot

Set up Conductor to start automatically when your machine boots, so the dashboard is always reachable.

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
