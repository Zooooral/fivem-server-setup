# FiveM Server Setup

IMPORTANT : Script must be runned with elevated privileges to open ports
Feel free to leave a star on the repository, it would be motivating :)

## Installation

1. Dowload python:
   Windows : https://www.python.org/downloads/
   Linux :
   ```
   sudo apt install python3
   sudo apt install python3-pip
   ```

2. Install the required Python packages:
   ```
   pip install requests beautifulsoup4 py7zr
   ```

3. Run the script (As Administrator):
   ```
   python setup.py
   ```
   Linux:
   ```
   sudo python setup.py
   ```
## How does it work ?


1. The script will automatically:
   - Download and extract the cfx-server-data
   - Set up the resources folder
   - Create a `server.cfg` file with your configuration
   - Help to setup a database (Windows) or complete setup (Linux)
   - Open your ports

## Troubleshooting

- If you encounter permission issues on Linux, try running the script with sudo:
  ```
  sudo python setup.py
  ```

- On Windows, if you get a "command not found" error, ensure that Python and Git are added to your system's PATH.

- If the script fails to download or extract files, check your internet connection and ensure you have the necessary permissions to write to the directory.

If you still struggle, feel free to message me on discord : __zooo

## Contributing

This is my first python script so contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

For more information on running a FiveM server, please refer to the [official FiveM documentation](https://docs.fivem.net/docs/server-manual/setting-up-a-server/).
