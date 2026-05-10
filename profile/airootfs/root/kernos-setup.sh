#!/usr/bin/env bash
echo "Setting up KernOS installer..."

# Remove stock archinstall
pip uninstall --break-system-packages -y archinstall

# Install KernOS fork
pip install --break-system-packages git+https://github.com/palazik/archinstall.git

echo "Done. Run 'archinstall' to install KernOS."
