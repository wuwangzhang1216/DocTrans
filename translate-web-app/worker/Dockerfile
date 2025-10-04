FROM python:3.9-slim

WORKDIR /app

# Install Node.js
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    google-genai>=0.2.0 \
    pymupdf>=1.23.0 \
    python-pptx>=0.6.21 \
    python-docx>=1.0.0 \
    pdfplumber>=0.10.0 \
    reportlab>=4.0.0 \
    python-dotenv>=1.0.0 \
    chardet>=5.0.0 \
    Pillow>=10.0.0 \
    rich>=13.7.0

# Copy package files for Node.js
COPY package*.json ./

# Install Node.js dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Start the worker
CMD ["node", "worker.js"]