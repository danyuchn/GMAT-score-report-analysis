# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# We use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire gmat_diagnosis_app directory into the container at /app/gmat_diagnosis_app
COPY ./gmat_diagnosis_app ./gmat_diagnosis_app

# Copy any other necessary files or directories from the project root
# For example, if you have data files or other modules at the root level that app.py depends on.
# COPY ./some_other_directory_or_file ./some_other_directory_or_file

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable for Streamlit
# This helps ensure Streamlit runs in a headless mode suitable for servers
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_PORT=8501

# Run app.py when the container launches
# We use gmat_diagnosis_app.app as Streamlit looks for module.name or path/to/script.py
# If app.py is directly in WORKDIR, it would be ['streamlit', 'run', 'app.py']
CMD ["streamlit", "run", "gmat_diagnosis_app/app.py"] 