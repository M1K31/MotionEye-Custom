# How to Launch motionEye

Before launching motionEye, please ensure you have followed the installation instructions in [`README.md`](./README.md).

There are two primary ways to launch motionEye: for development and in production.

## Development Launch

For development or debugging, you can run motionEye directly from the command line. This will start the server in the foreground and print logs to your terminal.

1.  **Navigate to the repository root:**
    ```sh
    cd /path/to/motioneye
    ```

2.  **Update to the latest code:** Before launching, it's a good practice to ensure you have the latest version of the code to avoid issues that have already been fixed.
    ```sh
    git pull
    ```

3.  **Run the startserver command:**
    ```sh
    python3 -m motioneye.meyectl startserver
    ```
    > **Note:** This command runs motionEye as a Python module, which is a reliable method that does not depend on your system's `PATH` configuration.

The web interface will typically be available at `http://localhost:8765`.

To stop the server, press `Ctrl+C` in the terminal.

## Production Launch (as a service)

For a production environment, it is recommended to run motionEye as a system service. The behavior depends on your installation method:

### Linux Systems
The `motioneye_init` script sets up a `systemd` service:

*   **To start the motionEye service:**
    ```sh
    sudo systemctl start motioneye
    ```

*   **To check the status of the service:**
    ```sh
    sudo systemctl status motioneye
    ```

*   **To stop the service:**
    ```sh
    sudo systemctl stop motioneye
    ```

*   **To enable the service to start on boot:**
    ```sh
    sudo systemctl enable motioneye
    ```

### macOS Systems

**For motionEye Lite installations** (high-performance embedded build):
*   **To start the motion daemon:**
    ```sh
    motioneye-lite start
    ```

*   **To check the daemon status:**
    ```sh
    motioneye-lite status
    ```

*   **To stop the daemon:**
    ```sh
    motioneye-lite stop
    ```

*   **To monitor daemon activity:**
    ```sh
    motioneye-lite monitor
    ```

**For standard macOS installations:**
The `install_macos.sh` script sets up a `launchd` service:

*   **To start the motionEye service:**
    ```sh
    sudo launchctl load /Library/LaunchDaemons/com.motioneye-project.motioneye.plist
    ```

*   **To stop the service:**
    ```sh
    sudo launchctl unload /Library/LaunchDaemons/com.motioneye-project.motioneye.plist
    ```

*   **To check if the service is running:**
    ```sh
    sudo launchctl list | grep motioneye
    ```
