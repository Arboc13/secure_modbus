#!/usr/bin/env python3

import asyncio
import logging
import random

from pymodbus import FramerType
from pymodbus.server import ModbusSerialServer
from pymodbus.simulator import DataType, SimData, SimDevice


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


async def run_inverter():
    unit_id = 1
    device = SimDevice(
        id=unit_id,
        simdata=SimData(address=0, count=6, values=[0]*6, datatype=DataType.REGISTERS)
    )

    # Ascult pe capatul de citire inverter al portului serial
    server = ModbusSerialServer(
        device, port="/tmp/ttyV_inverter", framer=FramerType.RTU, baudrate=9600
    )

    async def update_registers():
        while True:
            await asyncio.sleep(1.0)
            v1, v2, v3 = random.randint(2280, 2320), random.randint(2280, 2320), random.randint(2280, 2320)
            freq = random.randint(4995, 5005)
            power = random.randint(100, 450)
            values = [v1, v2, v3, freq, power, 4]
            await server.async_setValues(unit_id, 3, 0, values)
            logging.info(f"Invertor a generat: {values}")


    asyncio.create_task(update_registers())
    logging.info("Invertor RTU pornit pe /tmp/ttyV_inverter")
    await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(run_inverter())

