# GO-UPDATER

- As you all golang fans know that there isn't a proper updater for go in linux, so this project aims to automate the process of updating go in Linux.

- Currently supports all linux installation varieties and architectures.
- You can also use this script to downgrade your current installation(unless it's installed with package managers)
- How to use:
```
→ python3 update-go.py --help
usage: update-go.py [-h] [-v VERSION] [-a {amd64,arm64,386,armv6l,ppc64le,s390x}] [-o {linux,darwin,windows,freebsd,aix}]
                    [--download-only] [--unpack-only] [--file FILE] [--remove-only] [--available-versions] [-c]

Update go version

options:
  -h, --help            show this help message and exit
  -v VERSION, --version VERSION
                        Update to version
  -a {amd64,arm64,386,armv6l,ppc64le,s390x}, --arch {amd64,arm64,386,armv6l,ppc64le,s390x}
                        Update for arch [Default AMD64]
  -o {linux,darwin,windows,freebsd,aix}, --os {linux,darwin,windows,freebsd,aix}
                        Update for os [Default Linux]
  --download-only       Download archive only
  --unpack-only         Unpack downloaded archive only
  --file FILE           Path to downloaded archive
  --remove-only         Remove old installation only
  --available-versions  Show available versions
  --check               Check for new updates
  -c, --current         Get current version status
```

- Installation:
  ```bash
  git clone https://github.com/The-Debarghya/go-updater
  pip3 install -r requirements.txt
  ```

- You can use it to only download the archive, or unpack already downloaded archive, or even remove the old installation only.(If you're skeptical about what is happening internally!)

