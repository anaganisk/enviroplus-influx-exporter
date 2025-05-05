import time
import argparse
import traceback
from threading import Thread
import colorsys
import sys
import argparse

import ST7735
try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from bme280 import BME280
from pms5003 import PMS5003, ReadTimeoutError as pmsReadTimeoutError, SerialTimeoutError
from enviroplus import gas
from subprocess import PIPE, Popen
from enviroplus.noise import Noise
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from fonts.ttf import RobotoMedium as UserFont

import logging

import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info("""
 88888888b                   oo                            dP          .8888b dP                   888888ba   888888ba  
 88                                                  dP    88          88   " 88                   88    `8b  88    `8b 
a88aaaa    88d888b. dP   .dP dP 88d888b. .d8888b.    88    88 88d888b. 88aaa  88 dP    dP dP.  .dP 88     88 a88aaaa8P' 
 88        88'  `88 88   d8' 88 88'  `88 88'  `88 88888888 88 88'  `88 88     88 88    88  `8bd8'  88     88  88   `8b. 
 88        88    88 88 .88'  88 88       88.  .88    88    88 88    88 88     88 88.  .88  .d88b.  88    .8P  88    .88 
 88888888P dP    dP 8888P'   dP dP       `88888P'    dP    dP dP    dP dP     dP `88888P' dP'  `dP 8888888P   88888888P 
                                                                                                                        

Press Ctrl+C to exit!

""")

# BME280 temperature/pressure/humidity sensor
bme280 = BME280()

# PMS5003 particulate sensor
pms5003 = PMS5003()
time.sleep(1.0)

# Create ST7735 LCD display class
st7735 = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=10000000
)

# Initialize display
st7735.begin()

WIDTH = st7735.width
HEIGHT = st7735.height

# Set up canvas and font
img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
font_size_small = 10
font_size_large = 20
font = ImageFont.truetype(UserFont, font_size_large)
smallfont = ImageFont.truetype(UserFont, font_size_small)
x_offset = 2
y_offset = 2

# Set up InfluxDB connection
INFLUXDB_TOKEN = os.environ.get("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.environ.get("INFLUXDB_ORG")
INFLUXDB_URL = os.environ.get("INFLUXDB_URL")
INFLUXDB_BUCKET=os.environ.get("INFLUXDB_BUCKET")
if not INFLUXDB_TOKEN or not INFLUXDB_ORG or not INFLUXDB_URL or not INFLUXDB_BUCKET:
    print("Please set the INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_URL and INFLUXDB_BUCKET environment variables.")
    sys.exit(1)

BME280_SELFHEAT_COMPENSATION = float(os.environ.get("ENVIRO_BME280_SELFHEAT_COMPENSATION", 1.0))
USE_CPU_COMPENSATION=str(os.environ.get("ENVIRO_USE_CPU_COMPENSATION", "false")) == "true"
CPU_FACTOR = float(os.environ.get("ENVIRO_CPU_FACTOR", 2.25))
POLLING_INTERVAL =int( os.environ.get("ENVIRO_POLLING_INTERVAL", 10))
# Create a values dict to store the data
variables = ["temperature","pressure","humidity","light","oxidised","reduced","nh3","pm1","pm25","pm10"]
units = ["C","hPa","%","Lux","kO","kO","kO","ug/m3","ug/m3","ug/m3"]

# Define your own warning limits
# The limits definition follows the order of the variables array
# Example limits explanation for temperature:
# [4,18,28,35] means
# [-273.15 .. 4] -> Dangerously Low
# (4 .. 18]      -> Low
# (18 .. 28]     -> Normal
# (28 .. 35]     -> High
# (35 .. MAX]    -> Dangerously High
# DISCLAIMER: The limits provided here are just examples and come
# with NO WARRANTY. The authors of this example code claim
# NO RESPONSIBILITY if reliance on the following values or this
# code in general leads to ANY DAMAGES or DEATH.
limits = [[4, 18, 28, 35],
          [250, 650, 1013.25, 1015],
          [20, 30, 60, 70],
          [-1, -1, 30000, 100000],
          [-1, -1, 40, 50],
          [-1, -1, 450, 550],
          [-1, -1, 200, 300],
          [-1, -1, 50, 100],
          [-1, -1, 50, 100],
          [-1, -1, 50, 100]]

# RGB palette for values on the combined screen
palette = [(0, 0, 255),           # Dangerously Low
           (0, 255, 255),         # Low
           (0, 255, 0),           # Normal
           (255, 255, 0),         # High
           (255, 0, 0)]           # Dangerously High

values = {}

# Displays all the text on the 0.96" LCD
def display_everything():
    draw.rectangle((0, 0, WIDTH, HEIGHT), (0, 0, 0))
    column_count = 2
    row_count = (len(variables)/ column_count)
    for i in range(len(variables)):
        variable = variables[i]
        data_value = values[variable]
        unit = units[i]
        x = x_offset + ((WIDTH // column_count) * (i // row_count))
        y = y_offset + ((HEIGHT / row_count) * (i % row_count))
        message = "{}: {:.1f} {}".format(variable[:4], data_value, unit)
        lim = limits[i]
        rgb = palette[0]
        for j in range(len(lim)):
            if data_value > lim[j]:
                rgb = palette[j + 1]
        draw.text((x, y), message, font=smallfont, fill=rgb)
    st7735.display(img)


# Get the temperature of the CPU for compensation
def get_cpu_temperature():
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])


def write_to_influx():
    try:
        write_client = influxdb_client.InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)

        write_api = write_client.write_api(write_options=SYNCHRONOUS)
        
        for variable in variables:
            point = (
                Point(variable)
                .field("value", values[variable])
            )
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
    except Exception as e:
        logging.error("Error writing to InfluxDB: %s", e)
        logging.error(traceback.format_exc())

def fetch_and_postdata():
    global values
    # Tuning factor for compensation. Decrease this number to adjust the
    # temperature down, and increase to adjust up
    cpu_temps = [get_cpu_temperature()] * 5
    # Temperature
    cpu_temp = get_cpu_temperature()
    # Smooth out with some averaging to decrease jitter
    cpu_temps = cpu_temps[1:] + [cpu_temp]
    avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
    raw_temp = bme280.get_temperature()
    # compensate for self heating
    raw_temp = raw_temp - BME280_SELFHEAT_COMPENSATION
    # compensate for CPU heating
    if USE_CPU_COMPENSATION:
        temp_data = raw_temp - ((avg_cpu_temp - raw_temp) / CPU_FACTOR)
    else:
        temp_data = raw_temp

    # Pressure
    pressure_data = bme280.get_pressure()
    
    # Humidity
    humidity_data = bme280.get_humidity()
    
    # lux
    lux_data = ltr559.get_lux()

    # Gas Data
    gas_data = gas.read_all()
    oxidising_data = gas_data.oxidising / 1000
    reducing_data = gas_data.reducing / 1000
    nh3_data = gas_data.nh3 / 1000

    # Particulates
    pms_data = pms5003.read()
    pm1_data = pms_data.pm_ug_per_m3(1.0)
    pm2_5_data = pms_data.pm_ug_per_m3(2.5)
    pm10_data = pms_data.pm_ug_per_m3(10)

    values = {
        "temperature": temp_data,
        "pressure": pressure_data,
        "humidity": humidity_data,
        "light": lux_data,
        "oxidised": oxidising_data,
        "reduced": reducing_data,
        "nh3": nh3_data,
        "pm1": pm1_data,
        "pm25": pm2_5_data,
        "pm10": pm10_data
    }

    # round the values to 2 decimal places
    for key in values:
        values[key] = round(values[key], 2)
    # Display the data
    display_everything()
    write_to_influx()
    logging.info("Sensor data: %s", values)

def every(delay, task):
  next_time = time.time() + delay
  while True:
    time.sleep(max(0, next_time - time.time()))
    try:
      task()
    except Exception as e:
        logging.error("Problem while executing repetitive task: %s", e)
        logging.error(traceback.format_exc())
    # Schedule the next run
    # This is a bit of a hack to ensure that the task runs at the
    # correct interval, even if the task takes a long time to run
    # (e.g. if the network is slow
    next_time += (time.time() - next_time) // delay * delay + delay


def main():
    Thread(target=lambda: every(POLLING_INTERVAL, fetch_and_postdata)).start()

if __name__ == "__main__":
    main()
