import os
import subprocess
import argparse
import sys
import logging
from download_server_file import main as download_server_file_main

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def create_eula_file(server_dir):
    """Creates the EULA file in the server directory."""
    eula_path = os.path.join(server_dir, "eula.txt")
    try:
        with open(eula_path, "w") as f:
            f.write("eula=true\n")
        logging.info(f"EULA file created at {eula_path}")
    except IOError as e:
        logging.error(f"Failed to create EULA file: {e}")
        sys.exit(1)

def create_properties_file(server_dir, password):
    """Creates the server.properties file with the given password."""
    template_path = "server.properties.template"
    properties_path = os.path.join(server_dir, "server.properties")

    if not os.path.isfile(template_path):
        logging.error(f"Template file '{template_path}' does not exist.")
        sys.exit(1)

    try:
        with open(template_path, "r") as f:
            content = f.read()

        # Replace placeholder with the actual password
        content = content.replace("$$$pass$$$", password)

        with open(properties_path, "w") as f:
            f.write(content)
        logging.info(f"Server properties file created at {properties_path}")
    except IOError as e:
        logging.error(f"Failed to create server.properties file: {e}")
        sys.exit(1)

def copy_startup_script(server_dir):
    script_path = "orchestrator.py"
    properties_path = os.path.join(server_dir, "orchestrator.py")

    if not os.path.isfile(script_path):
        logging.error(f"startup script file '{script_path}' does not exist.")
        sys.exit(1)

    try:
        with open(script_path, "r") as f:
            content = f.read()

        with open(properties_path, "w") as f:
            f.write(content)
            
        logging.info(f"Server startup script file copied to {properties_path}")
    except IOError as e:
        logging.error(f"Failed to copy startup script file: {e}")
        sys.exit(1)

def main(version, server_dir, password):
    """Main function to download the server file, set up the server, and launch it."""
    # Ensure the server directory exists
    os.makedirs(server_dir, exist_ok=True)
    copy_startup_script(server_dir)

    # Download server file
    try:
        server_file_name = download_server_file_main(version, server_dir)
        server_file_path = os.path.join(server_dir,server_file_name)
        if not os.path.isfile(server_file_path):
            logging.error(f"Server file '{server_file_path}' does not exist after download.")
            sys.exit(1)
        logging.info(f"Server file downloaded to {server_file_path}")
    except Exception as e:
        logging.error(f"Failed to download server file: {e}")
        sys.exit(1)

    # Generate server files
    create_properties_file(server_dir, password)

    # Launch the server
    try:
        logging.info("Starting the Minecraft server...")
        subprocess.run(
            ["java", "-Xms4G", "-Xmx4G",'-jar', f"{server_file_name}", "--nogui"],
            cwd=server_dir,
            check=True
            )
    except subprocess.CalledProcessError as e:
        logging.error(f"Server process exited with non-zero exit status {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        logging.error("Java executable not found. Please ensure Java is installed and in your PATH.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred while running the server: {e}")
        sys.exit(1)

    create_eula_file(server_dir)


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Setup and run a Minecraft server.")
    parser.add_argument("version", type=str, help="Minecraft server version to download.")
    parser.add_argument("server_dir", type=str, help="Directory where server files will be created.")
    parser.add_argument("password", type=str, help="Password for server properties.")

    # Parse the arguments
    args = parser.parse_args()

    # Run the main function with parsed arguments
    try:
        main(args.version, args.server_dir, args.password)
    except KeyboardInterrupt:
        logging.info("Server setup interrupted by user.")
        sys.exit(0)
