FROM mcr.microsoft.com/devcontainers/python:3-3.14-trixie

# Keep output line-buffered for Python.
ENV PYTHONUNBUFFERED=1

# Set the default workspace location.
WORKDIR /workspace

# Install additional system dependencies here if needed.
# Example: RUN apt-get update && apt-get install -y --no-install-recommends <package>

# Use the non-root developer user from the base image.
USER vscode
