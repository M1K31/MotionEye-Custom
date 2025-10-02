# New Features Guide

This document outlines the new features that have been added to motionEye and how to use them.

## 1. macOS Compatibility

motionEye can now be installed and run on macOS. The process involves building the `motion` dependency from source and then installing `motionEye` as a background service.

### Building `motion` on macOS

A script has been provided to automate this process. It requires [Homebrew](https://brew.sh/) to be installed.

1.  Open a Terminal.
2.  Navigate to the `motioneye` source directory.
3.  Run the build script: `sudo ./build/build_motion_macos.sh`

This will install all necessary dependencies and compile the `motion` program, placing it in `/usr/local/bin/motion`.

### Installing motionEye as a Service

Once `motion` and `motioneye` (via pip) are installed, you can set it up to run automatically at boot.

1.  Open a Terminal.
2.  Navigate to the `motioneye` source directory.
3.  Run the installation script: `sudo ./build/install_macos.sh`

This will create the necessary configuration files and register `motionEye` with `launchd`, the macOS service manager.

*   **Configuration:** `/usr/local/etc/motioneye/motioneye.conf`
*   **Logs:** `/var/log/motioneye.log`

### Creating a DMG Installer

A script is provided to package the application into a `.dmg` file for distribution.

1.  Ensure you have completed the `build_motion_macos.sh` step first.
2.  Run the DMG creation script: `./build/create_dmg_macos.sh`
3.  The final `.dmg` file will be created in the current directory.

## 2. OpenCV Analysis & Facial Recognition

motionEye can now use OpenCV to analyze images after motion has been detected. This includes general person detection and specific facial recognition to identify "unfamiliar" people.

### Enabling OpenCV Analysis

1.  In the motionEye web UI, open the settings panel for a camera.
2.  Go to the **Motion Detection** section.
3.  Enable the **"Enable OpenCV Analysis"** checkbox.
4.  Apply the settings.

When enabled, every time a picture is saved due to motion, it will be processed by an OpenCV script.

### Managing Familiar Faces

To teach motionEye who to recognize, you can add pictures of "familiar" people.

1.  In the main settings panel, find the **Familiar Faces** section.
2.  Click the **"Manage Faces"** button. This will open a new page.
3.  On the "Manage Faces" page, you can:
    *   See a list of all known people.
    *   Upload a new face by providing a name and a clear, front-facing JPG or PNG image.
    *   Delete existing faces.

**How it works:**
*   The system learns from the images you upload. The filename you provide (e.g., "Jules") becomes the person's name.
*   When the OpenCV analysis runs, it detects all faces in the new image.
*   It compares these faces to the ones it has learned.
*   If a face is detected that does not match anyone in your "Familiar Faces" list, a message will be logged indicating an **"Unfamiliar Person"** was detected.

## 3. Home Assistant Integration (MQTT)

motionEye can integrate with Home Assistant to expose its cameras and motion sensors. This is done using the MQTT Discovery protocol.

### Configuration

1.  In the motionEye web UI, open the main settings panel.
2.  Find the **"MQTT Integration"** section (you may need to enable "Advanced Settings" to see it).
3.  **Enable** the integration.
4.  Enter the details for your MQTT broker:
    *   Broker Address (e.g., `192.168.1.100`)
    *   Broker Port (usually `1883`)
    *   Username and Password (if required by your broker).
5.  Apply the settings. motionEye will restart and attempt to connect to the broker.

### Discovered Entities

Once connected, motionEye will automatically create the following entity in Home Assistant for each camera:

*   `binary_sensor.motioneye_camera_<id>_motion`: A motion sensor that turns `ON` when motion starts and `OFF` when it ends. This is the primary way to trigger automations.

### Adding the Camera Feed

To view the live video feed in Home Assistant, you should add it manually using the **MJPEG Camera** integration.

1.  In Home Assistant, go to **Settings > Devices & Services > Add Integration**.
2.  Search for and select **"MJPEG Camera"**.
3.  Fill in the details:
    *   **Name:** Give your camera a name (e.g., "Front Door Camera").
    *   **MJPEG URL:** This is the "Streaming URL" from motionEye. You can find this in the motionEye UI in the "Video Streaming" section. It will look like `http://<motioneye_ip_address>:<stream_port>/`.
4.  Click **Submit**. Your camera feed will now be available in Home Assistant.

### Example Automation

You can use the discovered motion sensor to trigger automations for your manually added camera:

```yaml
alias: Notify when front door motion is detected
trigger:
  - platform: state
    entity_id: binary_sensor.motioneye_camera_1_motion
    to: 'on'
action:
  - service: notify.mobile_app_my_phone
    data:
      message: Motion detected at the front door!
mode: single
```

## 4. System Stability and Performance Enhancements

Several new features have been added under the hood to improve the long-term stability and performance of your motionEye server. These features are enabled by default and do not require any configuration.

### Automatic Motion Daemon Recovery

motionEye now actively monitors the core `motion` daemon. If the daemon crashes or becomes unresponsive for any reason, the system will automatically attempt to restart it.
- This feature works on both Linux (using `systemctl`) and macOS (using `launchd`).
- The system will attempt to restart the service up to 5 times in quick succession. If it continues to fail, it will stop trying, and manual intervention will be required. This prevents a continuous loop of failed restarts.

### Robust MJPEG Stream Handling

The client responsible for reading video streams from your cameras has been made more resilient.
- Previously, a temporary network glitch or a camera stream interruption could cause the connection to fail permanently until the service was restarted.
- Now, if a connection is lost, the client will attempt to reconnect automatically using an exponential backoff strategy. This means it will wait a few seconds before the first retry, then longer for the next, and so on. This greatly improves the reliability of cameras on less stable network connections (e.g., Wi-Fi).

### Memory Leak Prevention

The web interface handlers have been optimized to ensure that memory is properly released after each request is handled. This prevents small memory leaks that could, over a long period, cause the server to become slow or unresponsive, requiring a restart.

### Periodic Memory Management

A new background task runs every five minutes to perform two key functions:
1.  **Garbage Collection:** It explicitly runs Python's garbage collector to free up any memory that is no longer in use.
2.  **Memory Monitoring:** It checks the total memory (RAM) being used by the motionEye process. If the usage exceeds 500MB, it will log a warning message. This helps in diagnosing potential issues before they become critical.

## 5. Performance Tuning

Several new parameters have been introduced to allow for fine-tuning the performance of motionEye. These settings should be changed with care and are intended for advanced users. They can be configured by editing the `motion.conf` file located in your configuration directory (e.g., `/etc/motioneye/motion.conf`).

### MJPEG Proxy Buffer Size

-   **Parameter:** `mjpeg_proxy_buffer_size`
-   **Default:** `3`
-   **Description:** This setting controls the number of frames to buffer in the MJPEG proxy. A larger buffer can lead to smoother video streams, especially on unstable networks, but will increase memory consumption per camera. A smaller buffer reduces memory usage but may result in choppier video if frames are not processed quickly.

### Configuration Cache TTL

-   **Parameter:** `config_cache_ttl`
-   **Default:** `30` (seconds)
-   **Description:** This setting determines how long camera configurations are cached in memory. Caching configurations significantly reduces disk I/O and improves the responsiveness of the web UI. However, if you make changes to a camera's configuration file directly (not through the UI), those changes will not be reflected until the cache expires. A lower value means changes are picked up faster, but with a slight performance cost. A higher value improves performance but increases the delay in picking up manual configuration changes.
