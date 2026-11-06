#!/usr/bin/env python3
import asyncio
import struct
import logging
import time
from pymodbus import FramerType
from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice
import hashlib
import hmac

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

PAYLOAD_STRUCT = struct.Struct("!4sB16sQQ6H")
LENGTH_PREFIX = struct.Struct("!I")
SECRET_KEY = b"cheie-secreta-css-m3"  # aceeasi cheie ca in bridge
FRAME_SIZE = PAYLOAD_STRUCT.size + 32
MAX_AGE_MS = 5000  # ponytail: presupune ceasuri sincronizate (aceeasi masina); NTP daca sunt pe masini diferite


async def run_aggregator():
    # 1. Init server Modbus TCP pentru Ignition
    unit_id = 1
    device = SimDevice(
        id=unit_id,
        simdata=SimData(address=0, count=6, values=[0] * 6, datatype=DataType.REGISTERS)
    )
    modbus_server = ModbusTcpServer(device, framer=FramerType.SOCKET, address=("0.0.0.0", 5020))

    # 2. Functia care proceseaza datele de la Edge Bridge
    async def handle_bridge_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        logging.info("Bridge conectat.")
        last_seq = 0  # per conexiune: bridge-ul reporneste Seq de la 1
        try:
            while True:
                # Citim lungimea pachetului (4 bytes)
                length_bytes = await reader.readexactly(LENGTH_PREFIX.size)
                frame_length = LENGTH_PREFIX.unpack(length_bytes)[0]
                if frame_length != FRAME_SIZE:
                    logging.warning(f"Lungime invalida: {frame_length}, inchid conexiunea")
                    break

                # Citim frame-ul propriu-zis
                frame = await reader.readexactly(frame_length)

                # AICI VERIFICAM HMAC:

                payload = frame[:-32]
                mac_primit = frame[-32:]
                mac_calculat = hmac.new(SECRET_KEY, payload, hashlib.sha256).digest()
                if not hmac.compare_digest(mac_primit, mac_calculat):
                    logging.warning("HMAC invalid - pachet respins")
                    continue

                # Despachetam datele primite
                unpacked = PAYLOAD_STRUCT.unpack(payload)
                magic, version, device_id, sequence, timestamp_ms, *registers = unpacked
                if magic != b"PVSC" or version != 1:
                    logging.warning("Magic/versiune invalida - pachet respins")
                    continue
                if sequence <= last_seq:
                    logging.warning(f"Replay detectat (Seq={sequence} <= {last_seq}) - pachet respins")
                    continue
                if abs(time.time() * 1000 - timestamp_ms) > MAX_AGE_MS:
                    logging.warning("Pachet expirat (timestamp) - respins")
                    continue
                last_seq = sequence

                # Suprascriem registrele in Modbus TCP Server (Ignition le va citi de aici)
                await modbus_server.async_setValues(unit_id, 3, 0, list(registers))
                logging.info(f"Receptionat & Actualizat Modbus: Seq={sequence}, Reg={registers}")

        except asyncio.IncompleteReadError:
            logging.info("Bridge deconectat.")
        except Exception as e:
            logging.error(f"Eroare procesare client: {e}")
        finally:
            writer.close()

    # 3. Pornim ambele servere simultan
    tcp_listener = await asyncio.start_server(handle_bridge_client, "0.0.0.0", 9000)
    logging.info("Aggregator ascultă pachete pe portul 9000")
    logging.info("Aggregator expune Modbus TCP pe portul 5020 (pentru Ignition)")

    server_task = asyncio.create_task(modbus_server.serve_forever())
    async with tcp_listener:
        await tcp_listener.serve_forever()


if __name__ == "__main__":
    asyncio.run(run_aggregator())