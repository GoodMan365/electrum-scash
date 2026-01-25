# Electrum-Scash - Lightweight Scash client

Licence: MIT Licence

Author: GoodMan365 (forked for Scash)

Language: Python (>= 3.10)

Homepage: https://github.com/GoodMan365/electrum-scash  


Electrum-Scash is forked from Electrum and added support for Scash (a bitcoin fork) while removed bitcoin support.


## Getting started

_(If you're looking to simply run Electrum-Scash, download it from the [Releases page](https://github.com/GoodMan365/electrum-scash/releases).)_

Electrum-Scash is a fork of Electrum, modified to work with the **Scash blockchain**. It removes Lightning Network and TrustedCoin/2FA support, and includes Scash-specific chain parameters.


### TL;DR - Quick Install
```bash
$ sudo apt-get install libsecp256k1-dev python3-pyqt6 python3-cryptography
$ ELECTRUM_ECC_DONT_COMPILE=1 python3 -m pip install --user ".[gui,crypto]"
```
### Dependencies
#### Qt GUI
```bash
For the desktop interface:
$ sudo apt-get install python3-pyqt6
```

####libsecp256k1
Required for elliptic curve operations:

```bash
$ sudo apt-get install libsecp256k1-dev
```

#### cryptography
For fast symmetric ciphers:

```bash
$ sudo apt-get install python3-cryptography
```

### Running from source
#### From tar.gz

If you downloaded the official package:
```bash
$ ./run_electrum-scash
```
### From Git Development
```bash$ git clone https://github.com/GoodMan365/electrum-scash.git
$ cd electrum-scash
$ git submodule update --init
$ python3 -m pip install --user -e .
$ ./run_electrum-scash
```

## Creating Binaries

- [Linux (tarball)](contrib/build-linux/sdist/README.md)
- [Linux (AppImage)](contrib/build-linux/appimage/README.md)
- [macOS](contrib/osx/README.md)
- [Windows](contrib/build-wine/README.md)
- [Android](contrib/android/Readme.md)

### Key Differences from Electrum

    #### Scash blockchain support (mainnet only)
    #### No Lightning Network (completely removed, support comming soon)
    #### No TrustedCoin/2FA (completely removed)
    🎨 Scash branding (icons, app name, URI scheme)
    📱 Android intent filter for scash: URIs
	
## Contributing

Bug reports, testing, and documentation improvements are welcome! Since this is a specialized fork, major feature additions should be discussed first.

Most communication happens via GitHub Issues and discord: https://discord.gg/jsfwttTd

## Security & Verification

####Releases are signed by:
```bash
514E 2707 7335 D13C EB12  35AF 7EC4 35BF 9FCD F13C
Electrum-Scash GoodMan365
```

### To verify releases:
```bash
gpg --import contrib/pubkeys/electrum-scash.asc
gpg --verify Electrum-Scash-*.AppImage.asc
```

Electrum-Scash is not affiliated with the original Electrum project. Use at your own risk.
This README clearly communicates that this is a **Scash-specific fork** while maintaining Electrum's professional tone.