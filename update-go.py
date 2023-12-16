#!/usr/bin/env python3
import os
import argparse
import hashlib
import requests
import subprocess
import tarfile

from rich.console import Console
from rich.progress import Progress
import time


BASE_URL = "https://go.dev/dl/"
DEFAULT_INSTALLATION_DIR = "/usr/local/go"

def get_current_version() -> str:
    version = subprocess.run(['go', 'version'], capture_output=True).stdout.decode('utf-8').split(' ')[2]
    return version

def compare_versions(version1: str, version2: str) -> int:
    version1 = version1.replace('go', '').split('.')
    version2 = version2.replace('go', '').split('.')
    for i in range(len(version1)):
        if int(version1[i]) > int(version2[i]):
            return 1
        elif int(version1[i]) < int(version2[i]):
            return -1
    return 0

def verify_version(version: str) -> bool:
    go_exists = subprocess.run(['go', 'version'], capture_output=True).returncode == 0
    if go_exists:
        return version != get_current_version()
    return True

def get_available_versions() -> list:
    console = Console()
    with console.status("[bold green]Fetching available versions...") as status:
        try:
            status.start()
            archives_data = requests.get(BASE_URL + "?mode=json&include=all").json()
            versions = [(archive['version'], archive['stable']) for archive in archives_data]
            time.sleep(0.3)
            status.update()
            return versions
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None
        finally:
            status.stop()

def check_for_updates(current_version: str) -> tuple:
    console = Console()
    with console.status("[bold green]Fetching available versions...") as status:
        try:
            status.start()
            archives_data = requests.get(BASE_URL + "?mode=json").json()
            versions = ()
            for archive in archives_data:
                if archive['stable']:
                    comp = compare_versions(current_version, archive['version'])
                    if comp == -1:
                        versions = (archive['version'], archive['stable'])
                        break
            time.sleep(0.3)
            status.update()
            return versions
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None
        finally:
            status.stop()

def download_new_archive(version: str, arch: str, os: str) -> str:
    console = Console()
    with console.status("[bold green]Checking for specified version...") as status:
        status.start()
        archives_data = requests.get(BASE_URL + "?mode=json&include=all").json()
        for archive in archives_data:
            if archive['version'] == version:
                files = archive['files']
                break
        for file in files:
            if file['os'] == os and file['arch'] == arch and file['version'] == version:
                filename = file['filename']
                filehash = file['sha256']
                file_size = file['size']
                break
        status.update()
        time.sleep(0.1)
        status.stop()    
    
    with requests.get(BASE_URL + filename, stream=True) as r:
        r.raise_for_status()
        progress = Progress()
        with Progress() as progress:
            task = progress.add_task(f"[cyan]Downloading {filename}...", total=file_size, start=True)
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))
            progress.stop()

    with console.status("[bold green]Verifying file hash...") as status:
        status.start()
        with open(filename, 'rb') as f:
            filehash_calculated = hashlib.sha256(f.read()).hexdigest()
        status.update()
        time.sleep(0.1)
        if filehash != filehash_calculated:
            raise Exception('File was tampered while downloading!')
        status.stop()
        
    return filename        
    
def remove_old_version() -> str:
    dir_to_remove = DEFAULT_INSTALLATION_DIR
    prompt = input(f'Is your old installation at {DEFAULT_INSTALLATION_DIR}? [y/N]: ')
    if not prompt.lower() in ['y', 'yes']:
        dir_to_remove = input('Enter path to old installation: ')
    print(f'WARNING: The following directory and contents will be removed: {dir_to_remove}...')
    prompt = input('Proceed further? [y/N]: ')
    if not os.path.exists(dir_to_remove):
        raise Exception(f'Specified directory({dir_to_remove}) does not exist!')
    if not prompt.lower() in ['y', 'yes']:
        return
    if os.geteuid() != 0:
        process = subprocess.run(['bash', '-c', f'sudo rm -rf {dir_to_remove}'], capture_output=True, check=True)          
        if process.returncode != 0:
            raise Exception('Unable to remove old installation')
    else:
        process = subprocess.run(['bash', '-c', f'rm -rf {dir_to_remove}'], capture_output=True, check=True)
        if process.returncode != 0:
            raise Exception('Unable to remove old installation')
    print('Old installation removed!!!')
    return dir_to_remove
    
def unpack_archive(archive_path: str):
    with Progress() as progress:
        with tarfile.open(archive_path, "r:gz") as tar:
            total_files = len(tar.getmembers())
            for member in progress.track(tar.getmembers(), total=total_files, description=f"[cyan]Unpacking {archive_path}..."):
                tar.extractall(path=os.getcwd(), members=[member])
    print(f'Archive unpacked to {os.getcwd() + "/go/"}')

def update_symlinks(installation_dir: str):
    # remove old symlinks
    print('Removing old symlinks...')
    if os.geteuid() != 0:
        process = subprocess.run(['bash', '-c', 'sudo rm /usr/bin/go /usr/bin/gofmt'], capture_output=True, check=True)          
        if process.returncode != 0:
            raise Exception('Unable to remove old symlink')
    else:
        process = subprocess.run(['bash', '-c', 'rm /usr/bin/go /usr/bin/gofmt'], capture_output=True, check=True)
        if process.returncode != 0:
            raise Exception('Unable to remove old symlink')
    # copy unpacked files to installation dir
    print('Copying unpacked files to installation directory...')
    if os.geteuid() != 0:
        subprocess.run(['bash', '-c', f'sudo mkdir -p {installation_dir}'], capture_output=True, check=True)
        process = subprocess.run(['bash', '-c', f'sudo cp -r go/* {installation_dir}'], capture_output=True, check=True)          
        if process.returncode != 0:
            raise Exception('Unable to copy unpacked files to installation directory')
    else:
        subprocess.run(['bash', '-c', f'mkdir -p {installation_dir}'], capture_output=True, check=True)
        process = subprocess.run(['bash', '-c', f'cp -r go/* {installation_dir}'], capture_output=True, check=True)
        if process.returncode != 0:
            raise Exception('Unable to copy unpacked files to installation directory')
    # create new symlinks
    print('Creating new symlinks...')
    if os.geteuid() != 0:
        process1 = subprocess.run(['bash', '-c', f'sudo ln -s {installation_dir}/bin/go /usr/bin/go'], capture_output=True, check=True)          
        process2 = subprocess.run(['bash', '-c', f'sudo ln -s {installation_dir}/bin/gofmt /usr/bin/gofmt'], capture_output=True, check=True)          
        if process1.returncode != 0 or process2.returncode != 0:
            raise Exception('Unable to create new symlink')
    else:
        process1 = subprocess.run(['bash', '-c', f'ln -s {installation_dir}/bin/go /usr/bin/go'], capture_output=True, check=True)
        process2 = subprocess.run(['bash', '-c', f'ln -s {installation_dir}/bin/gofmt /usr/bin/gofmt'], capture_output=True, check=True)
        if process1.returncode != 0 or process2.returncode != 0:
            raise Exception('Unable to create new symlink')

def cleanup(downloaded_archive: str):
    # remove downloaded archive
    print('Removing downloaded archive...')
    subprocess.run(['bash', '-c', f'rm {downloaded_archive}'], shell=True, capture_output=True, check=True)
    # remove unpacked files
    print('Removing unpacked files...')
    subprocess.run(['bash', '-c', 'rm -rf go/'], shell=True, capture_output=True, check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update go version')
    parser.add_argument('-v', '--version', help='Update to version')
    parser.add_argument('-a', '--arch', help='Update for arch [Default AMD64]', default='amd64', choices=['amd64', 'arm64', '386', 'armv6l', 'ppc64le', 's390x'])
    parser.add_argument('-o', '--os', help='Update for os [Default Linux]', default='linux', choices=['linux', 'darwin', 'windows', 'freebsd', 'aix'])
    parser.add_argument('--download-only', help='Download archive only', action='store_true')
    parser.add_argument('--unpack-only', help='Unpack downloaded archive only', action='store_true')
    parser.add_argument('--file', help='Path to downloaded archive')
    parser.add_argument('--remove-only', help='Remove old installation only', action='store_true')
    parser.add_argument('--available-versions', help='Show available versions', action='store_true')
    parser.add_argument('--check', help='Check for new updates', action='store_true')
    #parser.add_argument('-d', '--debug', help='Debug mode', action='store_true')
    version = get_current_version()
    parser.add_argument('-c', '--current', help='Get current version status', action='version', version=version)

    args = parser.parse_args()
    if not verify_version(args.version):
        print(f'Already on version {args.version}')
        exit(0)

    if args.available_versions:
        print('VERSION\t\tSTABLE')
        available_versions = get_available_versions()
        max_len = max([len(version) for version, _ in available_versions])
        for version, stable in available_versions:
            print(f'{version.ljust(max_len)}\t{"YES" if stable else "NO"}')
        exit(0)

    if args.check:
        versions = check_for_updates(version)
        if versions is None or len(versions) == 0:
            print('No updates available!')
            exit(1)
        print("Updates available!!!")
        print(f'Version: {versions[0]} | Stable Release: {versions[1]}')
        exit(0)

    if args.download_only:
        try:
            downloaded_archive = download_new_archive(args.version, args.arch, args.os)
            print(f'Archive downloaded to {os.getcwd() + "/" + downloaded_archive}')
            exit(0)
        except Exception as e:
            print(f'Error: {e.__str__()}')
            exit(1)

    if args.unpack_only:
        if not args.file:
            parser.error('--unpack-only requires --file [ARCHIVE]')
        unpack_archive(args.file)
        exit(0)

    if args.remove_only:
        try:
            remove_old_version()
        except:
            print('Unable to remove old version')
            exit(1)
        finally:
            subprocess.run(['bash', '-c', 'sudo -k'], shell=True, capture_output=True, check=True)
            exit(0)
        
    try:
        downloaded_archive = download_new_archive(args.version, args.arch, args.os)
        print(f'Archive downloaded to {os.getcwd() + "/" + downloaded_archive}')
        installation_dir = remove_old_version()
        unpack_archive(downloaded_archive)
        update_symlinks(installation_dir)
        subprocess.run(['bash', '-c', 'sudo -k'], shell=True, capture_output=True, check=True)
        print("Cleaning up...")
        cleanup(downloaded_archive)
    except Exception as e:
        print(f'Error: {e.__str__()}')
        exit(1)
    