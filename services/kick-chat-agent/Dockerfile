# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container to /app
WORKDIR /app

# Add current directory files to /app in container
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir aiohttp argparse cloudscraper orjson rich

# Define environment variable
ENV NAME KickChatListener
ENV CHANNEL=default

# Run the python script when the container launches
CMD ["sh", "-c", "python main.py --channel $CHANNEL"]