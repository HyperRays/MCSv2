import argparse
import requests
import sys
import os
from packaging import version as packaging_version

BASE_URL = "https://api.papermc.io/v2/projects/paper/"

def versions_endpoint():
    return BASE_URL

def builds_endpoint(version):
    return f"{BASE_URL}versions/{version}/builds/"

def downloads_endpoint(version, build, file_name):
    return f"{builds_endpoint(version)}{build}/downloads/{file_name}"

builds_cache = {}

def get_versions_available():
    """Retrieve all available versions."""
    try:
        r = requests.get(versions_endpoint())
        r.raise_for_status()
        properties = r.json()
        return properties["versions"]
    except requests.RequestException as e:
        print(f"Failed to retrieve versions: {e}")
        sys.exit(1)

def get_builds(version):
    """Get builds for a given version, with caching."""
    if version in builds_cache:
        return builds_cache[version]
    try:
        r = requests.get(builds_endpoint(version))
        r.raise_for_status()
        properties = r.json()
        builds_cache[version] = properties["builds"]
        return builds_cache[version]
    except requests.RequestException as e:
        print(f"Failed to retrieve builds for version {version}: {e}")
        sys.exit(1)

def only_experimental(version):
    """Check if all builds of a version are experimental."""
    builds = get_builds(version)
    return all(build["channel"] == "experimental" for build in builds)

def get_non_experimental_builds(version):
    """Get non-experimental builds for a given version."""
    builds = get_builds(version)
    return [build for build in builds if build["channel"] != "experimental"]

def check_for_stable():
    """Check for stable versions."""
    versions = get_versions_available()
    stable_versions = {}
    for version in versions:
        is_stable = not only_experimental(version)
        stable_versions[version] = is_stable
    return stable_versions

def download_file(url, download_folder):
    """Download a file from a URL to a specified folder."""
    local_filename = os.path.basename(url)
    download_path = os.path.join(download_folder, local_filename)
    
    try:
        os.makedirs(download_folder, exist_ok=True)  # Ensure the folder exists
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(download_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"Downloaded {local_filename} to {download_path}")
        return local_filename
    except requests.RequestException as e:
        print(f"Failed to download file from {url}: {e}")
        sys.exit(1)

def batched_it(iterable, n):
    """Batch data into lists of length n. The last batch may be shorter."""
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]

def query_version_infos():
    """Generate a formatted list of stable versions."""
    stable_versions = [version for version, is_stable in check_for_stable().items() if is_stable]
    stable_versions_sorted = sorted(stable_versions, key=packaging_version.parse, reverse=True)
    log_str = "[Stable Versions]\n"
    for batch in batched_it(stable_versions_sorted, 7):
        log_str += ", ".join(batch) + "\n"
    print(log_str)

def main(version, folder):
    """Main function to check for latest version, get build, and download."""
    stable_versions = [v for v, is_stable in check_for_stable().items() if is_stable]
    if version not in stable_versions:
        print(f"Error: Version {version} is not stable or does not exist.")
        sys.exit(1)
    
    builds = get_non_experimental_builds(version)
    if not builds:
        print(f"Error: No non-experimental builds found for version {version}.")
        sys.exit(1)
    
    selected_build = builds[-1]  # Assuming the last build is the latest
    build_no = selected_build["build"]
    build_file = selected_build["downloads"]["application"]["name"]
    download_url = downloads_endpoint(version, build_no, build_file)
    return download_file(download_url, folder)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PaperMC CLI Utility")
    parser.add_argument("command", choices=["list-stable", "download"], help="Command to execute")
    parser.add_argument("--version", help="Specify the PaperMC version to download (required for 'download')")
    parser.add_argument("--folder", help="Specify the folder to download to", default=".")

    args = parser.parse_args()

    if args.command == "list-stable":
        query_version_infos()
    elif args.command == "download":
        if not args.version:
            print("Error: The --version argument is required for the 'download' command.")
            sys.exit(1)
        main(args.version, args.folder)
