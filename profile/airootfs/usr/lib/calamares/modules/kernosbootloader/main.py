# SPDX-FileCopyrightText: 2026 palazik
# SPDX-License-Identifier: GPL-3.0-or-later
import glob
import os
import pathlib
import re
import subprocess

import libcalamares


def _run(command, check=True):
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if check and proc.returncode != 0:
        raise RuntimeError("%s\n%s" % (" ".join(command), proc.stdout))
    return proc.stdout.strip()


def _chroot(root, *command):
    return _run(["arch-chroot", root, *command])


def _gs(name, default=None):
    value = libcalamares.globalstorage.value(name)
    return value if value not in (None, "") else default


def _target_source(root):
    return _run(["findmnt", "-nr", "-o", "SOURCE", "--target", root])


def _parent_disk(device):
    pkname = _run(["lsblk", "-ndo", "PKNAME", device], check=False).strip()
    if pkname:
        return "/dev/" + pkname
    return re.sub(r"p?[0-9]+$", "", device)


def _partition_number(device):
    partnum = _run(["lsblk", "-ndo", "PARTN", device], check=False).strip()
    if partnum:
        return partnum
    match = re.search(r"([0-9]+)$", device)
    return match.group(1) if match else ""


def _root_uuid(device):
    uuid = _run(["blkid", "-s", "UUID", "-o", "value", device], check=False).strip()
    if not uuid:
        raise RuntimeError("Could not determine target root UUID for %s" % device)
    return uuid


def _first(patterns, root):
    for pattern in patterns:
        found = sorted(glob.glob(os.path.join(root, pattern.lstrip("/"))))
        if found:
            return "/" + os.path.relpath(found[0], root)
    raise RuntimeError("Could not find any of: %s" % ", ".join(patterns))


def _efi_dir(root):
    if os.path.isdir(os.path.join(root, "boot/efi/EFI")):
        return "/boot/efi"
    return "/boot"


def _is_uefi():
    return os.path.isdir("/sys/firmware/efi")


def _write(path, text):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(path).write_text(text)


def _kernel_bits(root):
    kernel = _first(["/boot/vmlinuz-linux", "/boot/vmlinuz-*"], root)
    initramfs = _first(["/boot/initramfs-linux.img", "/boot/initramfs-*.img"], root)
    fallback = sorted(glob.glob(os.path.join(root, "boot/initramfs-*-fallback.img")))
    fallback_path = "/" + os.path.relpath(fallback[0], root) if fallback else initramfs
    return kernel, initramfs, fallback_path


def _ensure_packages(root, choice):
    candidates = {
        "grub": ["grub", "efibootmgr", "os-prober"],
        "systemd-boot": ["efibootmgr"],
        "efistub": ["efibootmgr"],
        "refind": ["refind", "efibootmgr"],
        "limine": ["limine", "efibootmgr"],
    }.get(choice, [])
    missing = [pkg for pkg in candidates if subprocess.run(["arch-chroot", root, "pacman", "-Q", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0]
    if missing:
        _chroot(root, "pacman", "-Sy", "--noconfirm", "--needed", *missing)


def _install_grub(root, disk):
    if _is_uefi():
        _chroot(root, "grub-install", "--target=x86_64-efi", "--efi-directory=%s" % _efi_dir(root), "--bootloader-id=KernOS", "--recheck")
    else:
        _chroot(root, "grub-install", "--target=i386-pc", disk, "--recheck")
    _chroot(root, "grub-mkconfig", "-o", "/boot/grub/grub.cfg")


def _install_systemd_boot(root, root_uuid):
    if not _is_uefi():
        raise RuntimeError("systemd-boot requires UEFI")
    kernel, initramfs, fallback = _kernel_bits(root)
    _chroot(root, "bootctl", "install", "--esp-path=%s" % _efi_dir(root))
    _write(os.path.join(root, "boot/loader/loader.conf"), "default kernos.conf\ntimeout 5\nconsole-mode keep\n")
    _write(
        os.path.join(root, "boot/loader/entries/kernos.conf"),
        "title KernOS\nlinux %s\ninitrd %s\noptions root=UUID=%s rw quiet\n" % (kernel, initramfs, root_uuid),
    )
    _write(
        os.path.join(root, "boot/loader/entries/kernos-fallback.conf"),
        "title KernOS fallback\nlinux %s\ninitrd %s\noptions root=UUID=%s rw\n" % (kernel, fallback, root_uuid),
    )


def _install_efistub(root, disk, partnum, root_uuid):
    if not _is_uefi():
        raise RuntimeError("EFISTUB requires UEFI")
    kernel, initramfs, _ = _kernel_bits(root)
    loader = "\\" + kernel.strip("/").replace("/", "\\")
    initrd = "\\" + initramfs.strip("/").replace("/", "\\")
    _chroot(
        root,
        "efibootmgr",
        "--create",
        "--disk",
        disk,
        "--part",
        partnum,
        "--label",
        "KernOS",
        "--loader",
        loader,
        "--unicode",
        "root=UUID=%s rw quiet initrd=%s" % (root_uuid, initrd),
    )


def _install_refind(root, root_uuid):
    if not _is_uefi():
        raise RuntimeError("rEFInd requires UEFI")
    kernel, initramfs, fallback = _kernel_bits(root)
    _chroot(root, "refind-install")
    _write(
        os.path.join(root, "boot/refind_linux.conf"),
        '"Boot with standard options" "root=UUID=%s rw quiet initrd=%s"\n"Boot with fallback initramfs" "root=UUID=%s rw initrd=%s"\n'
        % (root_uuid, initramfs, root_uuid, fallback),
    )


def _install_limine(root, disk, root_uuid):
    kernel, initramfs, fallback = _kernel_bits(root)
    limine_conf = """timeout: 5
default_entry: 1

/KernOS
    protocol: linux
    kernel_path: boot():%s
    cmdline: root=UUID=%s rw quiet
    module_path: boot():%s

/KernOS fallback
    protocol: linux
    kernel_path: boot():%s
    cmdline: root=UUID=%s rw
    module_path: boot():%s
""" % (kernel, root_uuid, initramfs, kernel, root_uuid, fallback)
    _write(os.path.join(root, "boot/limine.conf"), limine_conf)
    if _is_uefi():
        efi_boot = pathlib.Path(root) / _efi_dir(root).lstrip("/") / "EFI/BOOT"
        efi_boot.mkdir(parents=True, exist_ok=True)
        for candidate in ("/usr/share/limine/BOOTX64.EFI", "/usr/share/limine/BOOTIA32.EFI"):
            target_candidate = pathlib.Path(root) / candidate.lstrip("/")
            if target_candidate.exists():
                _run(["cp", str(target_candidate), str(efi_boot / target_candidate.name)])
    else:
        _chroot(root, "limine", "bios-install", disk)


def run():
    root = _gs("rootMountPoint")
    if not root:
        return "No target root mountpoint", "Calamares did not provide rootMountPoint."

    choice = _gs("packagechooser_bootloader", "grub")
    if isinstance(choice, list):
        choice = choice[0] if choice else "grub"
    choice = str(choice).split(",")[0].strip() or "grub"

    root_device = _target_source(root)
    disk = _parent_disk(root_device)
    partnum = _partition_number(root_device)
    root_uuid = _root_uuid(root_device)

    try:
        _ensure_packages(root, choice)
        _chroot(root, "mkinitcpio", "-P")
        if choice == "grub":
            _install_grub(root, disk)
        elif choice == "systemd-boot":
            _install_systemd_boot(root, root_uuid)
        elif choice == "efistub":
            _install_efistub(root, disk, partnum, root_uuid)
        elif choice == "refind":
            _install_refind(root, root_uuid)
        elif choice == "limine":
            _install_limine(root, disk, root_uuid)
        else:
            raise RuntimeError("Unsupported bootloader selection: %s" % choice)
    except Exception as exc:
        return "Bootloader installation failed", str(exc)

    return None
