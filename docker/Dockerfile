FROM python:3.11-slim

# Python slim doesn't have git installed
RUN apt-get update && apt-get install -y --no-install-recommends git && apt-get purge -y --auto-remove && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy the file with the requirements to the /code directory.
# Copy only the file with the requirements first, not the rest of the code.
# As this file doesn't change often, Docker will detect it and use the cache for this step,
# enabling the cache for the next step too.
COPY ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Create Logs dir
SHELL ["/bin/sh", "-c"]
RUN mkdir /app/logs

# As this has all the code which is what changes most frequently the Docker cache won't be used for this or any
# following steps easily. So, it's important to put this near the end of the Dockerfile, to optimize the container
# image build times.
COPY . /app

## Define build arguments for environment variables
ARG ENV

## Set environment variables using build arguments
ENV ENV=$ENV

# Run app.py when the container launches
CMD ["python", "/app/run_stoscbot.py"]