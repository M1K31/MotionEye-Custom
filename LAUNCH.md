# How to Launch motionEye

Before launching motionEye, please ensure you have followed the installation instructions in [`README.md`](./README.md).

There are two primary ways to launch motionEye: for development and in production.

## Development Launch

For development or debugging, you can run motionEye directly from the command line. This will start the server in the foreground and print logs to your terminal.

1.  **Navigate to the repository root:**
    ```sh
    cd /path/to/motioneye
    ```

2.  **Run the startserver command:**
    ```sh
    python3 -m motioneye.meyectl startserver
    ```
    > **Note:** This command runs motionEye as a Python module, which is a reliable method that does not depend on your system's `PATH` configuration.

The web interface will typically be available at `http://localhost:8765`.

To stop the server, press `Ctrl+C` in the terminal.

## Production Launch (as a service)

For a production environment, it is recommended to run motionEye as a system service. The `motioneye_init` script, which is run during installation, sets up a `systemd` service for this purpose.

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
