# rgrab
rgrab is a Python script that digs through Roblox's servers looking for available versions and sends whatever files it can get its hands on to an aria2c daemon.

## Setup
To get the script up and running, you first need to do a few steps:
1. [Set up an aria2c daemon.](https://stackoverflow.com/questions/62101819/how-to-use-aria2c-rpc-server-as-a-daemon) If you don't already have aria2c installed, [you can download it here](https://github.com/aria2/aria2/releases).
2. Install the `aria2p` module using pip:<br>
Windows: `py -m pip install aria2p`<br>
Linux: `pip install aria2p`
3. Run the script.

## Usage
```none
usage: rgrab.py [-h] [-d DOMAIN] [-m] [-di] [-ai ARIA2C_IP] [-ap ARIA2C_PORT]

Scrape Roblox's setup servers for client versions.

options:
  -h, --help            show this help message and exit
  -d DOMAIN, --domain DOMAIN
                        Sets the the domain that the script will grab versions from.
  -m, --mac             Scrape versions in a way that properly grabs Mac clients.
  -di, --dont_ignore_versions_after_parsed
                        Don't ignore versions found during the parsing process in future sessions.
  -ai ARIA2C_IP, --aria2c_ip ARIA2C_IP
                        The IP address of the aria2c daemon to connect to.
  -ap ARIA2C_PORT, --aria2c_port ARIA2C_PORT
                        The port of the aria2c daemon to connect to.
```
