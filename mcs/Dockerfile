FROM alpine:latest

# Add Amazon Corretto GPG keys and repository
RUN wget -O /etc/apk/keys/amazoncorretto.rsa.pub https://apk.corretto.aws/amazoncorretto.rsa.pub
RUN echo "https://apk.corretto.aws/" >> /etc/apk/repositories

# Update package list and install dependencies
RUN apk update
RUN apk add amazon-corretto-21
RUN apk add python3
RUN apk add py3-requests
RUN apk add py3-packaging
RUN apk add bash  # Ensure bash is installed

# Define build arguments
ARG version
ARG server_dir

# Set working directory and copy project files
WORKDIR /app
COPY . .

# Execute setup script with secret mounting
RUN --mount=type=secret,id=rcon_password,required=true \
    python3 setup_server.py ${version} ${server_dir} $(cat /run/secrets/rcon_password)

# Clean up cache to reduce image size
RUN rm -rf /var/cache/apk/*

# Define an ENTRYPOINT to allow CLI interaction
WORKDIR /app/${server_dir}
ENTRYPOINT ["python", "orchestrator.py", "." ,"--non-interactive"]
# ENTRYPOINT [ "/bin/bash" ]
