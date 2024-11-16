import argparse
import requests
import itertools
import sys
import os

def batched_it(iterable, n):
    """Batch data into iterators of length n. The last batch may be shorter."""
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el,), chunk_it)

# Endpoints to retrieve versions and builds
versions_endpoint = lambda: "https://api.papermc.io/v2/projects/paper/"
builds_endpoint = lambda version: f"{versions_endpoint()}versions/{version}/builds/"
downloads_endpoint = lambda version, build, file_name: f"{builds_endpoint(version)}{build}/downloads/{file_name}"

def only_experimental(version):
    """Check if all builds of a version are experimental."""
    try:
        r = requests.get(builds_endpoint(version))
        r.raise_for_status()
        properties = r.json()
        return all(map(lambda v: v["channel"] == "experimental", properties["builds"]))
    except requests.RequestException as e:
        print(f"Failed to check experimental status for version {version}: {e}")
        sys.exit(1)

def get_non_experimental_builds(version):
    """Get non-experimental builds for a given version."""
    try:
        r = requests.get(builds_endpoint(version))
        r.raise_for_status()
        properties = r.json()
        return list(filter(lambda v: v["channel"] != "experimental", properties["builds"]))
    except requests.RequestException as e:
        print(f"Failed to retrieve builds for version {version}: {e}")
        sys.exit(1)

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

def check_for_stable():
    """Check for stable versions."""
    versions = get_versions_available()
    return dict(zip(versions, map(only_experimental, versions)))

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
        return download_path
    except requests.RequestException as e:
        print(f"Failed to download file from {url}: {e}")
        sys.exit(1)

def parse_version_format(version):
    """Parse version format into a tuple, handling 'pre' identifiers properly."""
    parsed_version = []
    for part in version.split('.'):
        if '-' in part:
            numeric_part, pre_release_part = part.split('-')
            parsed_version.append(int(numeric_part) if numeric_part.isdigit() else numeric_part)
            text_part = "".join(filter(lambda v: not v.isdigit(), pre_release_part))
            version_part = int("".join(filter(str.isdigit, pre_release_part)))
            parsed_version.append((text_part, version_part))
        else:
            parsed_version.append(int(part) if part.isdigit() else part)
    return tuple(parsed_version)

def parse_version_format_int(version):
    """Parse version format into an integer format."""
    parsed_version = []
    for part in version.split('.'):
        if '-' in part:
            numeric_part, pre_release_part = part.split('-')
            parsed_version.append(int(numeric_part) if numeric_part.isdigit() else numeric_part)
            text_part = "".join(filter(lambda v: not v.isdigit(), pre_release_part))
            version_part = int("".join(filter(str.isdigit, pre_release_part)))
            if text_part == "rc":
                version_part = 2 + 1/version_part
            elif text_part == "pre":
                version_part = 1 + 1/version_part
            else:
                version_part = 3 + 1/version_part
            parsed_version.append(version_part)
        else:
            parsed_version.append(int(part) if part.isdigit() else part)
    
    version_int = 0
    for i, ver in enumerate(reversed(parsed_version)):
        multiple = 10000**i
        version_int += ver * multiple

    return version_int

def query_version_infos():
    """Generate a formatted list of stable versions."""
    log_str = "[Stable Versions]\n"
    latest_stable_versions = sorted(
        [v for v, is_experimental in check_for_stable().items() if not is_experimental],
        key=parse_version_format_int,
        reverse=True
    )
    log_str += ",\n".join(map(lambda v: ", ".join(v), batched_it(latest_stable_versions, 7)))
    print(log_str)

def main(version, folder):
    """Main function to check for latest version, get build, and download."""
    latest_stable_versions = sorted(
        [v for v, is_experimental in check_for_stable().items() if not is_experimental],
        key=parse_version_format_int,
        reverse=True
    )

    if version not in latest_stable_versions:
        print(f"Error: Version {version} is not stable or does not exist.")
        sys.exit(1)

    builds = get_non_experimental_builds(version)
    if not builds:
        print(f"Error: No non-experimental builds found for version {version}.")
        sys.exit(1)

    selected_build = builds[-1]
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
        _ = main(args.version, args.folder)

