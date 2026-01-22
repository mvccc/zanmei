# Dockerfile for zanmei - YOLO mode sandbox for Claude Code
# A development environment that can run Claude Code

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For pytesseract OCR
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    # For pillow/image processing
    libjpeg-dev \
    libpng-dev \
    # For lxml
    libxml2-dev \
    libxslt-dev \
    # Chinese fonts for rendering
    fonts-noto-cjk \
    # Build tools and utilities
    curl \
    git \
    make \
    # Node.js for Claude Code CLI
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Create non-root user (Claude Code won't run --dangerously-skip-permissions as root)
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID yolo && \
    useradd -m -u $UID -g $GID -s /bin/bash yolo

# Create working directory and config dirs
RUN mkdir -p /opt/zanmei && chown yolo:yolo /opt/zanmei
RUN mkdir -p /home/yolo/.claude /home/yolo/.config/claude-code /home/yolo/.config/opencode && \
    chown -R yolo:yolo /home/yolo

# Switch to non-root user
USER yolo
WORKDIR /opt/zanmei

# Set up environment
ENV PYTHONPATH=/opt/zanmei
ENV HOME=/home/yolo

# Entry point - just drop into a shell
CMD ["/bin/bash"]
