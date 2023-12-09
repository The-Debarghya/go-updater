#!/usr/bin/env python3
import argparse
import subprocess

ENDPOINT = "https://go.dev/dl/?mode=json&include=all"

def get_current_version() -> str:
    version = subprocess.run(['go', 'version'], capture_output=True).stdout.decode('utf-8').split(' ')[2]
    return version

def verify_version(version: str) -> bool:
    go_exists = subprocess.run(['go', 'version'], capture_output=True).returncode == 0
    if go_exists:
        return version != get_current_version()
    return True

def download_new_archive(version: str, arch: str, os: str):
    pass
    
def remove_old_version():
    pass

def unpack_archive(version: str, arch: str, os: str):
    pass

def update_symlinks(version: str):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update go version')
    parser.add_argument('-v', '--version', help='Update to version', required=True)
    parser.add_argument('-a', '--arch', help='Update for arch [Default AMD64]', default='amd64', choices=['amd64', 'arm64', '386', 'armv6l', 'ppc64le', 's390x'])
    parser.add_argument('-o', '--os', help='Update for os [Default Linux]', default='linux', choices=['linux', 'darwin', 'windows', 'freebsd'])
    version = get_current_version()
    parser.add_argument('-c', '--current', help='Get current version status', action='version', version=version)

    args = parser.parse_args()
    if not verify_version(args.version):
        print(f'Already on version {args.version}')
        exit(0)

    download_new_archive(args.version, args.arch, args.os)
    remove_old_version()
    unpack_archive(args.version, args.arch, args.os)
    update_symlinks(args.version)
    