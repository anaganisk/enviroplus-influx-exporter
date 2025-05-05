 ## Getting Started

To get the prometheus enviroplus-influx-exporter up and running I'm assuming you already have Prometheus and Grafana running somewhere. 
***Note***: I wouldn't recommend running Prometheus on a Raspberry Pi (using a local SD card) as this could drastically reduce the lifetime of the SD card as samples are written quite often to disk.

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



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.
