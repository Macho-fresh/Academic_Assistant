# Use Python 3.12 because the project depends on
# faster-whisper, ctranslate2 and PyAV.
FROM python:3.12-slim


# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Send Python output directly to the terminal
ENV PYTHONUNBUFFERED=1


# Application directory
WORKDIR /app


# Install system packages required by some Python dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*


# Copy requirements first so Docker can cache dependency installation
COPY requirements.txt /app/requirements.txt


# Upgrade pip and install project dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Copy the Django project into the container
COPY . /app/


# Create directories for uploaded media and static files
RUN mkdir -p /app/media /app/staticfiles


# Django will run on port 8000
EXPOSE 8000


# Collect static files and start Django
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"]