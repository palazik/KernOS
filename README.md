
<div align="center">

# KernOS

**An Arch-based Linux distribution built for performance and simplicity.**  
No bloat. No compromises. Just a fast, clean system.

[![KernOS License: GPL-2.0](https://img.shields.io/badge/License-KernOS%20GPL%20v2-blue.svg)](LICENSE)
[![archiso License: GPL-3.0](https://img.shields.io/badge/License-archiso%20GPL%20v3-blue.svg)](LICENSE)
[![Based on Arch](https://img.shields.io/badge/Based%20on-Arch%20Linux-1793d1?logo=arch-linux)](https://archlinux.org)
[![Built with archiso](https://img.shields.io/badge/Built%20with-archiso-grey)](https://gitlab.archlinux.org/archlinux/archiso)

</div>

---

## What is KernOS?

KernOS is a minimal, performance-focused Linux distribution based on Arch Linux. It strips away everything unnecessary and ships only what you actually need — giving you a fast, responsive system from the first boot.

Built by a kernel developer, for people who care about what runs under the hood.

---

## Philosophy

- **No bloat** — if it's not needed, it's not included
- **Performance first** — optimized defaults out of the box
- **Transparent** — you know exactly what's running on your system
- **Arch foundation** — rolling release, access to the full AUR, pacman

---

## Features

- Minimal package selection — nothing preinstalled you didn't ask for
- Optimized kernel configuration
- Fast boot times
- Clean archiso-based build system
- Fully reproducible ISO builds via GitHub Actions

---

## Building the ISO

### Requirements

```bash
sudo pacman -S archiso
```

### Build

```bash
git clone https://github.com/KernOS/core.git
cd core
sudo mkarchiso -v -w /tmp/kernos-work -o out/ profile/
```

The ISO will be output to `out/`.

### Test in QEMU

```bash
run_archiso -i out/kernos-*.iso
```

---

## Project Structure

```
core/
├── profile/                # archiso profile
│   ├── packages.x86_64     # package list
│   ├── airootfs/           # files overlaid onto the live system
│   ├── pacman.conf         # pacman config for the build
│   └── profiledef.sh       # ISO metadata
├── .github/workflows/      # GitHub Actions ISO build
├── .gitignore
├── LICENSE
└── README.md
```

---

## Roadmap

- [ ] Custom installer
- [ ] Optimized default kernel config
- [ ] KernOS package repository
- [ ] Website — kernos.sh

---

## License

KernOS distro configs and build scripts are licensed under the [GNU General Public License v3.0](LICENSE).  
The Linux kernel is licensed under GPL-2.0-only and is not relicensed here.

---

<div align="center">
  <sub>Built with 🔧 by <a href="https://github.com/palazik">palazik</a></sub>
</div>
