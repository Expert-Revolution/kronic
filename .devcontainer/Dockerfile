# Use the official Python image as base
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        # Essential development tools
        git \
        curl \
        wget \
        vim \
        nano \
        bash-completion \
        # Build tools
        build-essential \
        # PostgreSQL client
        postgresql-client \
        # Redis client
        redis-tools \
        # For health checks and testing
        netcat-traditional \
        # For kind/k8s development
        ca-certificates \
        gnupg \
        lsb-release \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install kind for local Kubernetes development
RUN curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64 \
    && chmod +x ./kind \
    && mv ./kind /usr/local/bin/kind

# Install Helm
RUN curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list \
    && apt-get update \
    && apt-get install helm

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Set up Python environment
WORKDIR /workspace

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt

# Install additional development tools
RUN pip install \
    black \
    flake8 \
    isort \
    pylint \
    pytest-cov \
    pytest-xdist

# Create non-root user
RUN useradd -m -s /bin/bash vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Switch to non-root user
USER vscode

# Set up shell completions and aliases
RUN echo 'alias ll="ls -la"' >> ~/.bashrc \
    && echo 'alias k="kubectl"' >> ~/.bashrc \
    && echo 'complete -F __start_kubectl k' >> ~/.bashrc \
    && echo 'source <(kubectl completion bash)' >> ~/.bashrc \
    && echo 'source <(helm completion bash)' >> ~/.bashrc

# Set the default command
CMD ["sleep", "infinity"]
