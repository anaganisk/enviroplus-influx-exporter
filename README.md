 ## Getting Started

To get the influx enviroplus-influx-exporter up and running I'm assuming you already have influx running somewhere. 
***Note***: I wouldn't recommend running influx on a Raspberry Pi (using a local SD card) as this could drastically reduce the lifetime of the SD card as samples are written quite often to disk.

### Prerequisites

- Python3
- To run the enviroplus-influx-exporter you need to have the enviroplus-python library by Pimoroni installed:
 
### One-line (Installs enviroplus-python library from GitHub)

```sh
curl -sSL https://get.pimoroni.com/enviroplus | bash
```

**Note** Raspbian Lite users may first need to install git: `sudo apt install git`

### Installation
We're going to run the enviroplus-influx-exporter as the user ```pi``` in the directory ```/usr/src/```. Adjust this as you wish.
 
1.Clone the enviroplus-influx-exporter repository
```sh
cd
git clone https://github.com/anaganisk/enviroplus_influx_exporter.git
sudo cp -r enviroplus_influx_exporter /usr/src/
sudo chown -R pi:pi /usr/src/enviroplus_influx_exporter
```

2.Install dependencies for enviroplus-influx-exporter
```sh
pip3 install -r requirements.txt
```

3.Install as a Systemd service
```sh
# edit the systemd file to set required env variables
cd /usr/src/enviroplus_influx_exporter
sudo cp contrib/enviroplus-influx-exporter.service /etc/systemd/system/enviroplus-influx-exporter.service
sudo chmod 644 /etc/systemd/system/enviroplus-influx-exporter.service
sudo systemctl daemon-reload
```
4.Start the enviroplus-influx-exporter service
```sh
sudo systemctl start enviroplus-influx-exporter
```
5.Check the status of the service
```sh
sudo systemctl status enviroplus-influx-exporter
```

6.Enable at boot time
```sh
sudo systemctl enable enviroplus-influx-exporter
```

## Acknowledgements
Inspired by [enviroplus_exporter](https://github.com/sighmon/enviroplus_exporter)


<!-- LICENSE -->
## License
### MIT
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


