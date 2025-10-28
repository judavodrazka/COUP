# About the project
**Communication Over UDP Protocol (COUP)** is a custom protocol created for safe and reliable message transmission over UDP.
To ensure no datagrams are lost, the protocol employs selective repeat with sliding window ARQ.

The protocol header is 16 bytes long and consists of the following fields:
- Sequence Number (4 bytes)
- Acknowledgement Number (4 bytes)
- CRC (2 bytes)
- Identification (2 bytes) 
- reserved (6 bits)
- Flags (10 bits)
- Fragmnent Number (2 bytes)

The project consists of an application which lets the user send messages and files using COUP, Wireshark lua script for COUP
packet color coding, and documentation written in LATEX.

