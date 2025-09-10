# Docker Instructions for motionEye (Development Version)

The instructions below are for building and running a Docker image from the source code in this repository. This is the recommended method for developers or users who want to test the new features included here.

## Building the Docker Image

From the root directory of this repository, run the following command:

```bash
docker build -t motioneye-local -f docker/Dockerfile .
```

This will build a new Docker image tagged `motioneye-local` using the local source code.

## Running the Container

You can run the container you just built using `docker-compose`. The provided `docker-compose.yml` is already configured to build from the local source.

1.  **Navigate to the docker directory:**
    ```bash
    cd docker
    ```

2.  **Start the container in the background:**
    ```bash
    docker-compose up -d
    ```

This will start the motionEye container. Your configuration will be stored in a Docker volume named `etc_motioneye`, and your media files will be in `var_lib_motioneye`.

### Accessing Device Cameras

To give the Docker container access to your host machine's USB cameras, you can use the `docker-compose.override.yml` file, which is automatically loaded by Docker Compose. This file is pre-configured to pass through `/dev/video0` and `/dev/video1`. You can edit it to add more devices if needed.
