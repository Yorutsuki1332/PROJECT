import time
from smbus2 import SMBus, i2c_msg

DEV_ADDR_SHT4X = 0x44

def gen_sht4x():
    try:
        with SMBus(1) as bus:
            bus.write_byte(DEV_ADDR_SHT4X, 0xFD)
            time.sleep(0.5)
            msg = i2c_msg.read(DEV_ADDR_SHT4X, 6)
            bus.i2c_rdwr(msg)
            data = list(msg)
            raw_t = int((data[0] << 8) | data[1])
            raw_rh = int((data[3] << 8) | data[4]) 
            rh = -6 + (125 * (raw_rh / 65535.0))
            temperature = -45 + (175 * (raw_t / 65535.0))
            return [temperature, rh]
    except Exception as e:
        print(f"Error reading SHT4X: {e}")
        return [None, None]