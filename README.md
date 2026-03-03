# ♭ conductor → be-conductor

**This project has moved to [be-conductor](https://github.com/somniacs/be-conductor).**

The name "conductor" was too common. Everything — code, releases, issues — now lives at the new repo.

## Migrating

If you have conductor installed, just run the new installer — it handles everything automatically:

```bash
# Linux / macOS
curl -fsSL https://github.com/somniacs/be-conductor/releases/latest/download/install.sh | bash
```

```powershell
# Windows
irm https://github.com/somniacs/be-conductor/releases/latest/download/install.ps1 | iex
```

The installer stops the old server, migrates your data (`~/.conductor/` → `~/.be-conductor/`), and installs the new package.
