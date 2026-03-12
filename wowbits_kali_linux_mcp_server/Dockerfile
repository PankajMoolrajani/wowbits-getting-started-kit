FROM kalilinux/kali-rolling:latest

# Install system tools and Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nmap \
    netexec \
    gobuster \
    nikto \
    sqlmap \
    exploitdb \
    wordlists \
    curl \
    wget \
    net-tools \
    dnsutils \
    whois \
    git \
    libcap2-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Unzip rockyou wordlist for convenience
RUN gunzip /usr/share/wordlists/rockyou.txt.gz 2>/dev/null || true

# Give nmap raw-socket capabilities so it works without full root
RUN setcap cap_net_raw,cap_net_admin+eip /usr/bin/nmap

# Install Flask (API server only needs Flask)
RUN pip3 install --break-system-packages flask

# Create a working directory for file outputs (wget, etc.)
RUN mkdir -p /app/data

WORKDIR /app

# Copy only the API server code into the container
COPY kali_api_server/ /app/kali_api_server/

ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO
ENV PORT=5000
ENV HOST=0.0.0.0
# Set to "true" to restrict execution to the pre-approved command allowlist
ENV ENFORCE_ALLOWLIST=false

EXPOSE 5000

CMD ["python3", "/app/kali_api_server/server.py"]
