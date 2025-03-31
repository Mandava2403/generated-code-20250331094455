# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variables (optional, can be set at runtime)
# Replace 'your_app_module:app' with your actual Flask app entry point if different
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run app.py when the container launches
# Use gunicorn for production or flask run for development
# Example using flask run:
CMD ["flask", "run"]

# Example using gunicorn (recommended for production):
# Ensure gunicorn is in requirements.txt
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "your_app_module:app"]