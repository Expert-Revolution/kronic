# Use the Microsoft devcontainer Python base image
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        postgresql-client \
        redis-tools \
        curl \
        wget \
        vim \
        git \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y && apt-get clean -y

RUN npm install -g @google/gemini-cli

# Install kubectl, helm, and kind
RUN ARCH=$(dpkg --print-architecture) \
    # Install kubectl
    && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/${ARCH}/kubectl" \
    && chmod +x kubectl && mv kubectl /usr/local/bin/ \
    # Install helm
    && curl https://get.helm.sh/helm-v3.12.3-linux-${ARCH}.tar.gz | tar -xzO linux-${ARCH}/helm > /usr/local/bin/helm \
    && chmod +x /usr/local/bin/helm \
    # Install kind
    && curl -Lo /usr/local/bin/kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-${ARCH} \
    && chmod +x /usr/local/bin/kind

# Set working directory
WORKDIR /workspace

# Copy and install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt \
    && pip install black flake8 isort pylint pytest-cov

# Switch to vscode user and setup environment
USER vscode
RUN echo 'alias k=kubectl' >> ~/.bashrc

CMD ["sleep", "infinity"]
