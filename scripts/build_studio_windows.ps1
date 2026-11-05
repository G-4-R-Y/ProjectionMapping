# Run on Windows, locally. No Actions workflows or network build service.
# Requires Python 3.12, PyInstaller, and a working desktop browser with WebGL2.
$ErrorActionPreference = 'Stop'
python -m pip install -e '.[desktop]'
python -m PyInstaller --noconfirm --clean --onedir --windowed `
  --name ProjectionStudio --paths src `
  --add-data 'src/projection_mapping/studio_static;projection_mapping/studio_static' `
  src/projection_mapping/studio_desktop.py
Write-Host 'Output: dist/ProjectionStudio/ProjectionStudio.exe'
