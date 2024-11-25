import time
from smbus2 import SMBus, i2c_msg

VEML7700_I2C_ADDRESS = 0x10

def gen_7700():
    try:
        addr = VEML7700_I2C_ADDRESS
        als_conf_0 = 0x00
        als_WH = 0x00
        als_WL = 0x00
        pow_sav = 0x00
        als = 0x04

        confValues = [0x00, 0x18] 
        interrupt_high = [0x00, 0x00] 
        interrupt_low = [0x00, 0x00]
        power_save_mode = [0x00, 0x00]

        with SMBus(1) as bus:
            bus.write_i2c_block_data(addr, als_conf_0, confValues)
            bus.write_i2c_block_data(addr, als_WH, interrupt_high)
            bus.write_i2c_block_data(addr, als_WL, interrupt_low)
            bus.write_i2c_block_data(addr, pow_sav, power_save_mode) 
            
            time.sleep(0.04)
            raw_data = bus.read_word_data(addr, als)
            
            # Convert raw data (little-endian)
            data = ((raw_data & 0xFF) << 8) | ((raw_data >> 8) & 0xFF)
            
            # Apply resolution scaling factor
            gain = 0.0036  # for ALS gain x1
            integration_time = 1  # for 100ms
            resolution = gain * integration_time
            
            lux = data * resolution
            return round(lux, 2)

    except Exception as e:
        print(f"Error reading VEML7700: {e}")
        return None
