# Install recommended VS Code extensions for this project
# Usage (PowerShell):
#   .\install-extensions.ps1

$extensions = @(
  "ms-python.python",
  "ms-python.vscode-pylance",
  "ms-toolsai.jupyter",
  "charliermarsh.ruff",
  "ms-python.black-formatter",
  "dbaeumer.vscode-eslint",
  "esbenp.prettier-vscode",
  "bradlc.vscode-tailwindcss",
  "qwtel.sqlite-viewer",
  "github.vscode-pull-request-github",
  "github.copilot",
  "github.copilot-chat"
)

if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
  Write-Host "VS Code 'code' CLI not found in PATH." -ForegroundColor Yellow
  Write-Host "Open VS Code, run 'Command Palette' → 'Shell Command: Install 'code' command in PATH' or add Code to your PATH, then re-run this script." -ForegroundColor Yellow
  exit 1
}

foreach ($ext in $extensions) {
  Write-Host "Installing extension: $ext" -ForegroundColor Cyan
  try {
    & code --install-extension $ext --force | Out-Null
    Write-Host "Installed: $ext" -ForegroundColor Green
  } catch {
    Write-Host ("Failed to install {0}: {1}" -f $ext, $_) -ForegroundColor Red
  }
}

Write-Host "All done. Restart VS Code if any extensions were installed." -ForegroundColor Green
