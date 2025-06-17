# main.py

from machine import Pin
from time import sleep
from umodbus.serial import Serial as ModbusRTUMaster
import secrets
import boot

# ==== CONFIG ====
MODBUS_SLAVE_ADDR = 10
MODBUS_BAUDRATE = 115200
UART_ID = 2
TX_PIN = 16
RX_PIN = 17
CONFIG_FILE = "config.txt"
READ_INTERVAL = 10  # seconds

# ==== INIT MODBUS ====
modbus = ModbusRTUMaster(
    baudrate=MODBUS_BAUDRATE,
    data_bits=8,
    stop_bits=2,
    parity=None,
    pins=(Pin(TX_PIN), Pin(RX_PIN)),
    ctrl_pin=None,
    uart_id=UART_ID
)

# ==== LOAD CONFIG.TXT ====
def load_registers():
    try:
        with open(CONFIG_FILE, "r") as f:
            contents = f.read()
            reg_list = []
            for item in contents.strip().split(","):
                parts = item.strip().split(":")
                if len(parts) == 3:
                    addr = int(parts[0])
                    qty = int(parts[1])
                    scale = float(parts[2])
                    reg_list.append((addr, qty, scale))
            return sorted(reg_list)
    except Exception as e:
        print("Error loading config.txt:", e)
        return []

registers = load_registers()
print("Loaded registers from config.txt:", registers)

# ==== MQTT Setup ====
mqtt = boot.init_mqtt()

# ==== MAIN LOOP ====
while True:
    payload = {}
    print("----- Reading Modbus Registers -----")
    
    for idx, (reg, qty, scale) in enumerate(registers, start=1):
        try:
            result = modbus.read_holding_registers(
                slave_addr=MODBUS_SLAVE_ADDR,
                starting_addr=reg,
                register_qty=qty,
                signed=False
            )
            if qty == 1:
                value = result[0] * scale
                print(f"{idx}. Reg {reg:>3} = {value:.2f} (16-bit)")
                payload[str(reg)] = "{:.2f}".format(value)
            elif qty == 2:
                combined = (result[0] << 16) | result[1]
                value = combined * scale
                print(f"{idx}. Regs {reg}-{reg+1} = {value:.2f} (32-bit)")
                payload[f"{reg}-{reg+1}"] = "{:.2f}".format(value)
        except Exception as e:
            print(f"{idx}. Error reading reg {reg}: {e}")

    # ==== Publish as single JSON message ====
    try:
        import ujson
        json_payload = ujson.dumps(payload)
        if mqtt:
            mqtt.publish(secrets.MQTT_TOPIC, json_payload)
            print("Published MQTT:", json_payload)
    except Exception as e:
        print("Error publishing MQTT:", e)

    sleep(READ_INTERVAL)
