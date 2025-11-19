FROM python:3.11-slim

# Install dependencies for nsjail
RUN apt-get update && apt-get install -y \
    autoconf \
    bison \
    flex \
    gcc \
    g++ \
    git \
    libprotobuf-dev \
    libnl-route-3-dev \
    libtool \
    make \
    pkg-config \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Build and install nsjail
RUN git clone --depth 1 https://github.com/google/nsjail.git /nsjail && \
    cd /nsjail && \
    make && \
    cp /nsjail/nsjail /usr/sbin/nsjail && \
    cd / && \
    rm -rf /nsjail

# Install Python dependencies
RUN pip install --no-cache-dir flask gunicorn pandas numpy

# Create app directory
WORKDIR /app

# Copy application files
COPY app.py /app/
COPY nsjail.cfg /app/

# Create temp directory with proper permissions
RUN mkdir -p /tmp && chmod 1777 /tmp

# Expose port
EXPOSE 8080

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "app:app"]