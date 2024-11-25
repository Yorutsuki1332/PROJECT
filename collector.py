import sht4x, veml7700, pm25
import sqlite3
import random
from datetime import datetime
import threading
import time

def init_db():
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                 (timestamp TEXT, temperature REAL, humidity REAL, 
                  light_level REAL, particle_level REAL)''')
    conn.commit()
    conn.close()

def collect_sensor_data():
    while True:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        [temperature, humidity] = sht4x.gen_sht4x()
        light_level =  veml7700.gen_7700()
        particle_level = pm25.get_pm25_reading()

        conn = sqlite3.connect('sensor_data.db')
        c = conn.cursor()
        c.execute('''INSERT INTO sensor_data VALUES (?, ?, ?, ?, ?)''',
                 (timestamp, temperature, humidity, light_level, particle_level))
        conn.commit()
        conn.close()
        time.sleep(5)