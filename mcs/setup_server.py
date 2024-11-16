import os
import subprocess
import argparse
import download_server_file

def create_eula_file(server_dir): 
    eula_path = os.path.join(server_dir, "eula.txt")
    with open(eula_path, "w") as f:
        f.write("eula=true\n")  # Write acceptance of EULA to the file

def create_properties_file(server_dir, password): 
    # Read the template
    with open("server.properties.template", "r") as f:
        file = f.read()
    
    # Replace placeholder with the actual password
    file = file.replace("$$$pass$$$", password)

    # Write the modified content to the server directory
    properties_path = os.path.join(server_dir, "server.properties")
    with open(properties_path, "w") as f:
        f.write(file)

def main(version, server_dir, password):
    # Download server file
    os.makedirs(server_dir, exist_ok=True)
    server_file_name = download_server_file.main(version, server_dir)
    
    # Generate server files
    create_eula_file(server_dir)
    create_properties_file(server_dir, password)
    
    # Launch the server
    subprocess.call(["java", "-Xms4G", "-Xmx4G", "-jar", server_file_name, "--nogui"])

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Setup and run a Minecraft server.")
    parser.add_argument("version", type=str, help="Minecraft server version to download.")
    parser.add_argument("server_dir", type=str, help="Directory where server files will be created.")
    parser.add_argument("password", type=str, help="Password for server properties.")

    # Parse the arguments
    args = parser.parse_args()

    # Run the main function with parsed arguments
    main(args.version, args.server_dir, args.password)
