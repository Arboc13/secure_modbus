#!/usr/bin/env python3
import socket
import struct 
import time
import logging
from pymodbus.client import ModbusSerialClient
import hashlib
import hmac

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


# Structura pachetului: Magic(4), Version(1), DeviceID(16), Seq(8), Time(8), Registers(12)
PAYLOAD_STRUCT = struct.Struct("!4sB16sQQ6H")
LENGTH_PREFIX = struct.Struct("!I")
SECRET_KEY = b"cheie-secreta-css-m3"  # aceeasi cheie in aggregator


def main():
    rtu_client = ModbusSerialClient(port="/tmp/ttyV_bridge", baudrate=9600)
    if not rtu_client.connect():
        logging.error("Nu s-a putut deschide portul RTU")
        return


    tcp_socket = None
    sequence = 0


    try:
        while True:
            time.sleep(1.0)
            #print("Citesc de la Invertor (MODBUS RTU)")
            response = rtu_client.read_holding_registers(address=0, count=6)
            if response.isError():
                logging.warning("Eroare citire Modbus RTU")
                continue
            print("trecut de response")
            registers = response.registers
            sequence += 1
            timestamp_ms = int(time.time() * 1000)

            print("# Impachetez datele")
            device_field = b"INV-001".ljust(16, b"\x00")
            payload = PAYLOAD_STRUCT.pack(
                b"PVSC", 1, device_field, sequence, timestamp_ms, *registers
            )

            # Pt participanti: AICI ADAUGAM HMAC:
            mac = hmac.new(SECRET_KEY, payload, hashlib.sha256).digest()  # 32 bytes
            frame_to_send = payload + mac

            # 3. Trimitem catre Aggregator via TCP (cu prefix de lungime)
            try:
                if tcp_socket is None:
                    tcp_socket = socket.create_connection(("127.0.0.1", 9000))

                tcp_socket.sendall(LENGTH_PREFIX.pack(len(frame_to_send)) + frame_to_send)
                logging.info(f"Trimis Seq={sequence} | Reg={registers}")
            except Exception as e:
                logging.error(f"Eroare TCP: {e}")
                tcp_socket = None


    except KeyboardInterrupt:
        logging.info("Oprit")
    finally:
        rtu_client.close()
        if tcp_socket: tcp_socket.close()


if __name__ == "__main__":
    main()