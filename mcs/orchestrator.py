import os
import subprocess
import fnmatch
import argparse
import threading
import sys

def find_latest_paper_jar(directory):
    """
    Search for the latest PaperMC JAR file in the specified directory.
    Assumes JAR files are named in the format 'paper-<version>-<build>.jar'.
    """
    jar_files = fnmatch.filter(os.listdir(directory), 'paper-*.jar')
    if not jar_files:
        raise FileNotFoundError("No PaperMC JAR files found in the specified directory.")

    # Sort JAR files to find the latest one
    jar_files.sort(reverse=True)
    latest_jar = jar_files[0]
    return os.path.join(directory, latest_jar)

def read_commands_from_file(file_path):
    """
    Read commands from the specified file and return them as a list.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Command file '{file_path}' not found.")
    
    with open(file_path, 'r') as file:
        commands = [line.strip() for line in file if line.strip()]
    return commands

def run_java_server(jar_path, interactive=True, command_file=None):
    """
    Start the PaperMC server, with optional interactive shell and automated commands.
    """
    java_command = [
        'java',
        '-Xms4096M',
        '-Xmx4096M',
        '--add-modules=jdk.incubator.vector',
        '-XX:+UseG1GC',
        '-XX:+ParallelRefProcEnabled',
        '-XX:MaxGCPauseMillis=200',
        '-XX:+UnlockExperimentalVMOptions',
        '-XX:+DisableExplicitGC',
        '-XX:+AlwaysPreTouch',
        '-XX:G1HeapWastePercent=5',
        '-XX:G1MixedGCCountTarget=4',
        '-XX:InitiatingHeapOccupancyPercent=15',
        '-XX:G1MixedGCLiveThresholdPercent=90',
        '-XX:G1RSetUpdatingPauseTimePercent=5',
        '-XX:SurvivorRatio=32',
        '-XX:+PerfDisableSharedMem',
        '-XX:MaxTenuringThreshold=1',
        '-Dusing.aikars.flags=https://mcflags.emc.gs',
        '-Daikars.new.flags=true',
        '-XX:G1NewSizePercent=30',
        '-XX:G1MaxNewSizePercent=40',
        '-XX:G1HeapRegionSize=8M',
        '-XX:G1ReservePercent=20',
        '-jar',
        jar_path,
        '--nogui'
    ]

    automated_commands = []
    if command_file:
        automated_commands = read_commands_from_file(command_file)

    try:
        # Start the server process
        server_process = subprocess.Popen(
            java_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        def read_server_output():
            """
            Continuously read and print server output to the console.
            """
            try:
                while True:
                    output = server_process.stdout.readline()
                    if output == "" and server_process.poll() is not None:
                        break
                    if output:
                        print(output, end="")
            except Exception as e:
                print(f"Error reading server output: {e}", file=sys.stderr)

        # Start a thread to read server output
        output_thread = threading.Thread(target=read_server_output, daemon=True)
        output_thread.start()

        if automated_commands:
            print("Running automated commands...")
            for command in automated_commands:
                print(f"Executing: {command}")
                server_process.stdin.write(command + "\n")
                server_process.stdin.flush()

        if interactive:
            print("Minecraft server started. Type commands to interact with the server.")
            while True:
                try:
                    command = input("> ")
                    if command.strip().lower() in {"exit", "quit", "stop"}:
                        print("Stopping the server...")
                        server_process.stdin.write("stop\n")
                        server_process.stdin.flush()
                        break
                    server_process.stdin.write(command + "\n")
                    server_process.stdin.flush()
                except (KeyboardInterrupt, EOFError):
                    print("\nStopping the server...")
                    server_process.stdin.write("stop\n")
                    server_process.stdin.flush()
                    break
        else:
            print("Minecraft server is running in non-interactive mode. Check logs for server output.")
            server_process.wait()
            print("Server stopped.")
    except FileNotFoundError:
        print("Java executable not found. Please ensure Java is installed and in your system's PATH.")
        os.abort()
    except Exception as e:
        print(f"An error occurred: {e}")
        os.abort()

def main():
    parser = argparse.ArgumentParser(description="Run the latest PaperMC server.")
    parser.add_argument(
        'server_directory',
        type=str,
        help='Path to the server directory containing PaperMC JAR files.'
    )
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run the server in non-interactive mode.'
    )
    parser.add_argument(
        '--commands',
        type=str,
        help='Path to a file containing automated commands to run on the server.'
    )
    args = parser.parse_args()

    if not os.path.isdir(args.server_directory):
        print(f"Error: The directory '{args.server_directory}' does not exist or is not accessible.")
        return

    try:
        latest_jar_path = find_latest_paper_jar(args.server_directory)
        print(f"Found latest PaperMC JAR: {latest_jar_path}")
        run_java_server(latest_jar_path, interactive=not args.non_interactive, command_file=args.commands)
    except Exception as e:
        print(f"Error: {e}")
        os.abort()

if __name__ == "__main__":
    main()
