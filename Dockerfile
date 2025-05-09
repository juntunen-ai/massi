# Use an official Python runtime as a parent image
# Choose a Python version compatible with your code (e.g., 3.9, 3.10, 3.11)
FROM python:3.10-slim

# Set environment variables
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=True

# Set the GOOGLE_API_KEY environment variable (replace with your actual key or pass it securely at runtime)
ENV GOOGLE_API_KEY=<your-api-key-placeholder>

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size
# --default-timeout=100 increases timeout for pip commands
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy the rest of your application code into the container at /app
COPY . .

# Expose the port Streamlit will run on (Cloud Run sets this via $PORT)
# We default to 8080, but Cloud Run will override this.
EXPOSE 8080

# Command to run the Streamlit application
# It uses the PORT environment variable provided by Cloud Run.
# --server.enableCORS=false is often needed on Cloud Run.
# Replace 'app.py' if your main Streamlit file has a different name.
CMD streamlit run app.py --server.port $PORT --server.enableCORS false