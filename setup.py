import os
import platform
import requests
import py7zr
import tarfile
import lzma
import sys
import subprocess
import zipfile
from bs4 import BeautifulSoup
import re
import ctypes
import shutil
from typing import Optional
from enum import Enum
from dataclasses import dataclass

class Color(Enum):
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_color(text: str, color: Color) -> None:
    print(f"{color.value}{text}{Color.ENDC.value}")

def is_admin() -> bool:
    return ctypes.windll.shell32.IsUserAnAdmin() != 0 if sys.platform == 'win32' else os.geteuid() == 0

def elevate_privileges() -> None:
    if not is_admin():
        print_color("Requesting admin privileges...", Color.YELLOW)
        if sys.platform == 'win32':
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1)
        else:
            args = ['sudo', sys.executable] + sys.argv + [os.environ]
            os.execlpe('sudo', *args)
        sys.exit(0)

def get_os() -> str:
    system = platform.system()
    if system == "Windows":
        print_color("Detected Windows OS", Color.BLUE)
        return "Windows"
    elif system == "Linux":
        distros = ["Ubuntu", "Debian"]
        while True:
            print_color("Select your Linux distribution:", Color.BLUE)
            for i, distro in enumerate(distros, 1):
                print_color(f"{i}. {distro}", Color.YELLOW)
            choice = input(f"{Color.BLUE.value}Enter the number of your distribution: {Color.ENDC.value}")
            if choice.isdigit() and 1 <= int(choice) <= len(distros):
                distro = distros[int(choice) - 1]
                print_color(f"Detected {distro}", Color.GREEN)
                return distro
            print_color("Invalid choice. Please try again.", Color.RED)
    else:
        print_color(f"Unsupported OS: {system}", Color.RED)
        sys.exit(1)

def get_latest_artifact(os_type: str) -> Optional[str]:
    base_url = "https://runtime.fivem.net/artifacts/fivem/build_server_windows/master/" if os_type == 'Windows' else "https://runtime.fivem.net/artifacts/fivem/build_proot_linux/master/"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    versions = [link.get('href').strip('/') for link in soup.find_all('a') if 'server' in link.get('href') or 'fx.tar' in link.get('href')]
    versions.sort(key=lambda v: int(re.search(r'(\d+)', v).group(1) if re.search(r'(\d+)', v) else -1), reverse=True)
    return f"{base_url}{versions[0]}" if versions else None

def download_file(url: str, file_name: str) -> None:
    print_color(f"Downloading {file_name} from {url}", Color.BLUE)
    with requests.get(url, stream=True) as response, open(file_name, 'wb') as file:
        shutil.copyfileobj(response.raw, file)

def unzip_file(file_name: str) -> None:
    print_color(f"Extracting {file_name}", Color.BLUE)
    extract_path = '.'
    if file_name.endswith('.7z'):
        with py7zr.SevenZipFile(file_name, mode='r') as archive:
            members = archive.getnames()
            archive.extract(path=extract_path, targets=[m for m in members if m != '.gitignore'])
    elif file_name.endswith('.tar.xz'):
        with lzma.open(file_name) as xz_file, tarfile.open(fileobj=xz_file) as tar_file:
            for item in tar_file.getmembers():
                if item.name != '.gitignore' or not os.path.exists(os.path.join(extract_path, '.gitignore')):
                    tar_file.extract(item, path=extract_path)
    elif file_name.endswith('.zip'):
        with zipfile.ZipFile(file_name, 'r') as zip_file:
            for item in zip_file.infolist():
                if item.filename != '.gitignore' or not os.path.exists(os.path.join(extract_path, '.gitignore')):
                    zip_file.extract(item, path=extract_path)
    else:
        print_color(f"Unsupported file format: {file_name}", Color.RED)
        sys.exit(1)
    print_color(f"Extraction of {file_name} complete", Color.GREEN)
    os.remove(file_name)
    print_color(f"Deleted {file_name}", Color.GREEN)

@dataclass
class DatabaseConfig:
    name: str
    user: str
    password: str

def setup_mysql(os_type: str) -> DatabaseConfig:
    if input(f"{Color.YELLOW.value}Would you like a MySQL database for your FiveM server? (y/n): {Color.ENDC.value}").lower() != 'y':
        print_color("MySQL setup skipped.", Color.YELLOW)
        return DatabaseConfig("CHANGEME", "CHANGEME", "CHANGEME")

    if os_type == "Windows":
        print_color("Please install MySQL manually from https://www.apachefriends.org/en/index.html or https://dev.mysql.com/downloads/installer/", Color.YELLOW)
        input(f"{Color.YELLOW.value}Press Enter when you have completed the MySQL installation manually...{Color.ENDC.value}")
    elif os_type in ["Ubuntu", "Debian"]:
        try:
            subprocess.run(["mysql", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_color("MySQL is already installed.", Color.GREEN)
        except (subprocess.CalledProcessError, FileNotFoundError):
            subprocess.run(["sudo", "apt", "update"])
            subprocess.run(["sudo", "apt", "install", "-y", "mysql-server"])
            subprocess.run(["sudo", "systemctl", "start", "mysql"])
            subprocess.run(["sudo", "systemctl", "enable", "mysql"])
            print_color("MySQL has been installed and started.", Color.GREEN)

    if input(f"{Color.YELLOW.value}Would you like to create a new database for your FiveM server? (y/n): {Color.ENDC.value}").lower() != 'y':
        print_color("MySQL setup completed.", Color.GREEN)
        return DatabaseConfig("CHANGEME", "CHANGEME", "CHANGEME")

    db_config = DatabaseConfig(
        input(f"{Color.BLUE.value}Enter the name for your FiveM database: {Color.ENDC.value}"),
        input(f"{Color.BLUE.value}Enter the username for your FiveM database: {Color.ENDC.value}"),
        input(f"{Color.BLUE.value}Enter the password for your FiveM database: {Color.ENDC.value}")
    )

    if os_type != "Windows":
        create_db_command = f"CREATE DATABASE {db_config.name}; CREATE USER '{db_config.user}'@'localhost' IDENTIFIED BY '{db_config.password}'; GRANT ALL PRIVILEGES ON {db_config.name}.* TO '{db_config.user}'@'localhost'; FLUSH PRIVILEGES;"
        subprocess.run(["sudo", "mysql", "-e", create_db_command])
    else:
        print_color("Please run the following commands in your MySQL client:", Color.BLUE)
        print_color(f"CREATE DATABASE {db_config.name};", Color.YELLOW)
        print_color(f"CREATE USER '{db_config.user}'@'localhost' IDENTIFIED BY '{db_config.password}';", Color.YELLOW)
        print_color(f"GRANT ALL PRIVILEGES ON {db_config.name}.* TO '{db_config.user}'@'localhost';", Color.YELLOW)
        print_color("FLUSH PRIVILEGES;", Color.YELLOW)
        input(f"{Color.YELLOW.value}Press Enter when you have completed these steps...{Color.ENDC.value}")

    print_color("MySQL setup completed.", Color.GREEN)
    return db_config

def generate_mysql_connection_string(db_config: DatabaseConfig) -> str:
    if "CHANGEME" in [db_config.user, db_config.name, db_config.password]:
        return "# set mysql_connection_string \"host=localhost;user={db_config.user};database={db_config.name};password={db_config.password};charset=utf8mb4\""
    else:
        return f"set mysql_connection_string \"host=localhost;user={db_config.user};database={db_config.name};password={db_config.password};charset=utf8mb4\""

def setup_fivem_server(server_name: str, server_port: str, sv_license_key: str, db_config: DatabaseConfig) -> None:
    print_color("Setting up FiveM server...", Color.BLUE)

    print_color("Cloning cfx-server-data...", Color.BLUE)
    download_file('https://github.com/citizenfx/cfx-server-data/archive/refs/heads/master.zip', 'cfx-server-data.zip')
    unzip_file('cfx-server-data.zip')

    if os.path.exists('./resources'):
        print_color("Existing resources folder found. Merging new resources...", Color.YELLOW)
        os.makedirs('./resources/[FiveM]', exist_ok=True)
        for item in os.listdir('./cfx-server-data-master/resources'):
            shutil.move(os.path.join('./cfx-server-data-master/resources', item),
                        os.path.join('./resources/[FiveM]', item))
    else:
        print_color("Creating new resources folder...", Color.BLUE)
        os.makedirs('./resources/[FiveM]')
        for item in os.listdir('./cfx-server-data-master/resources'):
            shutil.move(os.path.join('./cfx-server-data-master/resources', item),
                        os.path.join('./resources/[FiveM]', item))
    shutil.rmtree('./cfx-server-data-master')

    print_color("Creating server.cfg...", Color.BLUE)
    with open('server.cfg', "w") as cfg_file:
        cfg_file.write(f"""# Server Configuration
endpoint_add_tcp "0.0.0.0:{server_port}"
endpoint_add_udp "0.0.0.0:{server_port}"

# Server info
sv_hostname "{server_name}"
sets sv_projectName "My FiveM Server"
sets sv_projectDesc "A FiveM Server"

# Server properties
sv_enforceGamebuild 3095
sv_maxclients 10
sv_scriptHookAllowed 0
sv_endpointprivacy true

# RCON password
# rcon_password CHANGEME

# License key
sv_licenseKey "{sv_license_key}"

{generate_mysql_connection_string(db_config)}

# Steam Web API key
set steam_webApiKey none

exec ./resources.cfg
""")
    print_color("server.cfg created.", Color.GREEN)

    print_color("Setting up resources.cfg...", Color.BLUE)
    if not os.path.exists('resources.cfg'):
        with open('resources.cfg', "w") as cfg_file:
            cfg_file.write("""# Resources
ensure mapmanager
ensure chat
ensure spawnmanager
ensure sessionmanager
ensure basic-gamemode
ensure hardcap
ensure rconlog""")
        print_color("resources.cfg created.", Color.GREEN)
    else:
        print_color("resources.cfg already exists.", Color.YELLOW)

def open_ports(os_type: str) -> None:
    print_color("Opening necessary ports...", Color.BLUE)
    try:
        if os_type == "Windows":
            subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                            "name=FiveM Server (TCP)", "dir=in", "action=allow",
                            "protocol=TCP", "localport=30120"], check=True)
            subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                            "name=FiveM Server (UDP)", "dir=in", "action=allow",
                            "protocol=UDP", "localport=30120"], check=True)
            print_color("Ports opened successfully on Windows.", Color.GREEN)
        elif os_type in ["Ubuntu", "Debian"]:
            subprocess.run(["sudo", "ufw", "allow", "30120/tcp"], check=True)
            subprocess.run(["sudo", "ufw", "allow", "30120/udp"], check=True)
            print_color("Ports opened successfully with ufw.", Color.GREEN)
    except subprocess.CalledProcessError:
        print_color("Failed to open ports. Please ensure you have the necessary permissions.", Color.RED)
        print_color("You may need to open TCP and UDP port 30120 manually in your firewall.", Color.YELLOW)

def main() -> None:
    elevate_privileges()
    print_color("Detecting operating system...", Color.BLUE)
    os_type = get_os()
    print_color("Fetching latest artifact URL...", Color.BLUE)
    artifact_url = get_latest_artifact(os_type)
    file_name = 'server.7z' if os_type == 'Windows' else 'fx.tar.xz'

    download_file(artifact_url, file_name)
    unzip_file(file_name)
    db_config = setup_mysql(os_type)

    server_port = input(f"{Color.BLUE.value}Enter your server port (default 30120): {Color.ENDC.value}") or "30120"

    tx_installation = input(f"{Color.YELLOW.value}Would you like to install your server with txAdmin? (y/n): {Color.ENDC.value}").lower() == 'y'
    if not tx_installation:
        print_color("Server configuration...", Color.GREEN)
        server_name = input(f"{Color.BLUE.value}Enter your server name: {Color.ENDC.value}") or "My development server"
        sv_license_key = input(f"{Color.BLUE.value}Enter your license key: {Color.ENDC.value}") or "changeme"
        setup_fivem_server(server_name, server_port, sv_license_key, db_config)

    open_ports(os_type)
    print_color("Setup complete!", Color.GREEN)
    print_color("Server data files are located in: resources/", Color.YELLOW)
    print_color("To start the server, run:", Color.YELLOW)
    print_color("FXServer.exe +exec server.cfg" if os_type == "Windows" else "./run.sh +exec server.cfg", Color.CYAN)

if __name__ == "__main__":
    main()