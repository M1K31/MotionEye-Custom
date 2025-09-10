# Uninstallation Guide

This guide provides instructions on how to uninstall motionEye and its dependencies from your system.

**Warning:** These scripts will remove configuration files. Some steps will also offer to remove all media files (your recordings and pictures). Please back up any important data before proceeding.

## Linux (Debian/Ubuntu)

An `uninstall_linux.sh` script is provided in the `build` directory to automate the uninstallation process.

### To Uninstall:
1.  Navigate to the root of this repository.
2.  Run the uninstallation script with `sudo`:
    ```sh
    sudo ./build/uninstall_linux.sh
    ```
3.  The script will guide you through the process.

## macOS

An `uninstall_macos.sh` script is provided in the `build` directory to automate the uninstallation process.

### To Uninstall:
1.  Navigate to the root of this repository.
2.  Run the uninstallation script with `sudo`:
    ```sh
    sudo ./build/uninstall_macos.sh
    ```
3.  The script will remove the background service and system-level files.
4.  You will also need to manually drag the `motionEye.app` file from your `/Applications` folder to the Trash.
5.  The script will offer to remove your media files separately.
