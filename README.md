# secure_modbus


Project for Cybersecurity for Sustainable Systems course. 


This lab simulates four-layer arhitecture of a modern smart grid: 

- Field Layer: Since commercial inverters do not support cryptography natively, we simulate a hardware bridge (eg. a Raspberry Pi with an RS-485 Hat) that is instaleld inside the inverter cabinet. This bridge reads the raw Modbus RTU data, packages it, appends a Timestamp, signs it wiht HMAC-SHA256 and transmits it over the insecure field network. 
- Edge & Aggregation layer: A secure Server (Edge Gateway) situated in the control room. It receives encrypted packets, validates in HMAC signature and exposes the clean, validated data as standard Modbus TCP server.
- OT Networks (Local SCADA): The centralized supervisory platform that connects to Layer 2 via standard Modbus TCP to visualize, log and monitor the plant.



