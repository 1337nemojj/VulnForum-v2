# Use the official Python image as a base
FROM python:3.9-slim-buster


# Set the working directory inside the container
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt || cat /app/requirements.txt

# Expose the application port
EXPOSE 80

# Command to run the application
CMD ["python", "app.py"]