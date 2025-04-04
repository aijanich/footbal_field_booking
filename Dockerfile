# Use an official Python image
FROM python:3.11-slim

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    cmake \
    python3-pip \
    python3-dev \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libsqlite3-dev \
    libtiff-dev \
    libcurl4-openssl-dev \
    autoconf \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL and GEOS
ENV GDAL_LIBRARY_PATH=/lib/x86_64-linux-gnu/libgdal.so
ENV GEOS_LIBRARY_PATH=/lib/x86_64-linux-gnu/libgeos_c.so 
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Copy only requirements first to leverage Docker's caching mechanism
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application files
COPY . /app/

# Expose the application port
EXPOSE 8000

COPY entrypoint.sh .

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]