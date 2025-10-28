import socket
import time
import os
from threading import Thread
from threading import Lock
from threading import Timer
from App.packetbuilder import PacketBuilder
from math import ceil
from random import randint


KEEP_ALIVE_RETRIES = 3
MAX_FRAG_SIZE = 1415
HEADER_LENGTH = 16

class Connector:

    def __init__(self):
        self.listener_sock = None
        self.sender_sock = None

        self.ip_src = ""
        self.port_rec = 55777
        self.port_src = None
        self.ip_dst = ""
        self.port_dst = 55777
        self.frag_size = MAX_FRAG_SIZE

        

        self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        
        self.console_line = []

        self.listening = False
        self.connected = False

        self.header_length = HEADER_LENGTH # bytes
        self.seq = 0
        self.seq_lock = Lock()
        self.ack = 0
        self.ack_lock = Lock()
        self.id = 0

        self.keep_alive_retries = KEEP_ALIVE_RETRIES
        self.keep_alive_retries_lock = Lock()
        self.keep_alive_time = 5
        self.last_activity = None
        self.last_activity_lock = Lock()
        self.ka = False

        self.received_fragments = {}
        self.number_of_fragments = 0
        self.not_acknowledged_packets = []
        self.not_acknowledged_packets_lock = Lock()
        self.packet_timers = []
        self.packets = []
        self.packet_timers_lock = Lock()
        self.window_size = 20
        self.ack_timeout = 0.5
        self.j = 0
        self.j_lock = Lock()
        self.first_seq = 0

        self.state = 0 # 0 - closed port; 1 - listening; 2 - SYN; 3 - SYN,ACK; 4 - ACK; 5 - EST
        self.state_lock = Lock()

        self.start_time = time.time()

        

    
    def to_console_line(self, message):
        self.console_line.append(message)


    def prepare_packet(self, flags: list[str] = [], raw_payload = '', packet_type: str = 'data'):
        pb = PacketBuilder(self.frag_size, self.id, self.seq, self.ack, packet_type, flags, raw_payload)
        pb.format_payload()
        pb.fragment_data()
        return pb.packet
    
    def resend_packet(self, packet, index):
        self.sender_sock.sendto(packet, (self.ip_dst, self.port_dst))
        # print(f"resending packet: id={int.from_bytes(packet[10:12], 'big')} | fragment number={int.from_bytes(packet[14:16], 'big')}")
        with self.packet_timers_lock:
            try:
                if self.packet_timers[index] is not None:
                    self.packet_timers[index].cancel()
                    self.packet_timers[index] = Timer(self.ack_timeout, lambda: self.resend_packet(packet, index))
                    self.packet_timers[index].start()
            except IndexError:
                print(f"{index} not in packet timers")
                print(f"{self.packet_timers}")

        
    def send(self, flags: list[str] = [], raw_payload: str = ''):
        fault = False
        if raw_payload[:7] == '\\fault ':
            fault = True
            raw_payload = raw_payload[7:]

        if raw_payload[:10] == '\\sendfile ':
            path = raw_payload[10:]
            file_name = os.path.basename(path)
            self.to_console_line(f"System> Sending file: {file_name} from {path}")
            try:
                with open(path, 'rb') as f:
                    file_content = f.read()
            except Exception as e:
                self.to_console_line("System> Err: failed to read file; " + str(e))
                return
            file_name_bytes = bytes(file_name, encoding="utf-8")
            metadata = (len(file_name_bytes)).to_bytes(1, 'big') + file_name_bytes
            self.packets = self.prepare_packet(flags + ['FIL'], metadata+file_content, 'file')
        else:
            self.packets = self.prepare_packet(flags, raw_payload)

        packets_size = len(self.packets)
        with self.not_acknowledged_packets_lock:
            self.not_acknowledged_packets = [0 for i in range(packets_size)]
        with self.packet_timers_lock:
            self.packet_timers = [0 for i in range(packets_size)]

        self.id += 1
        if packets_size == 1 and ('KEA' in flags or 'SYN' in flags or 'ACK' in flags or 'NAK' in flags):
            self.sender_sock.sendto(self.packets[0], (self.ip_dst, self.port_dst))
            return
        
        data_size = sum(len(p[HEADER_LENGTH:]) for p in self.packets)
        if packets_size > 1:
            self.to_console_line(f"System> Sending {data_size}B of data in {len(self.packets)} fragments.")
            self.to_console_line(f"System> Fragment size: {len(self.packets[0][HEADER_LENGTH:])}B")
            self.to_console_line(f"System> Last fragment size: {len(self.packets[-1][HEADER_LENGTH:])}B")

        i = 0
        self.first_seq = self.seq+len(self.packets[0][HEADER_LENGTH:])
        with self.j_lock:
            self.j = min(packets_size, self.window_size)

        if fault: # pick which packets will be send with fault in data
            no_faulty_packets = randint(1, packets_size)
            faulty_packets = []
            for k in range(no_faulty_packets):
                while True:
                    faulty_index = randint(0, packets_size-1)
                    if faulty_index not in faulty_packets:
                        faulty_packets.append(faulty_index)
                        break
            faulty_packets = set(faulty_packets)
            # print(faulty_packets)
        
        start = time.time()
        while i < packets_size:
            with self.j_lock:
                while i < self.j:
                    # print(f"packet: {i}")
                    if fault and i in faulty_packets: # send faulty packet instead of the normal one
                        # print(f"fault: {i}")
                        faulty_packet = bytearray(self.packets[i])
                        faulty_bytes = max(1, randint(0,len(faulty_packet)-HEADER_LENGTH-1))
                        faulty_packet[HEADER_LENGTH:faulty_bytes+HEADER_LENGTH] = os.urandom(faulty_bytes)
                        self.sender_sock.sendto(faulty_packet, (self.ip_dst, self.port_dst))
                        # print(f"Sent faulty packet {i}")
                    else:
                        self.sender_sock.sendto(self.packets[i], (self.ip_dst, self.port_dst))
                        # print(f"Sent packet {i}")
                    with self.packet_timers_lock:
                        self.packet_timers[i] = Timer(self.ack_timeout, lambda pkt = self.packets[i], index = i: self.resend_packet(pkt, index))
                        self.packet_timers[i].start()
                    i += 1
        end = time.time()
        if end-start > 0 and packets_size > 1:
            self.to_console_line(f"System> Time to transfer: {round(end - start, 2)}s")
            self.to_console_line(f"System> 2MB/{round((end-start)/(data_size)*2*1024*1024, 2)}s")
        with self.seq_lock:
            self.seq += data_size
        with self.last_activity_lock:
            self.last_activity = time.time()


    def listen(self):
        while self.listening:
            data = None
            try:
                data, address = self.listener_sock.recvfrom(MAX_FRAG_SIZE+HEADER_LENGTH)                
            except Exception as e:
                if e == TypeError or e.errno != 10038:
                    self.to_console_line("Error receiving data:" + str(e))
                    continue
            if data is None:
                continue
            
            header, payload = data[:self.header_length], data[self.header_length:]
            with self.ack_lock:
                self.ack = int.from_bytes(header[:4], 'big')+len(payload)
            with self.keep_alive_retries_lock:
                self.keep_alive_retries = KEEP_ALIVE_RETRIES
            with self.last_activity_lock:
                self.last_activity = time.time()
            pb = PacketBuilder(self.frag_size)
            flags = pb.decode_flags(header)
            # print(f"Received:\t{flags}\tseq: {int.from_bytes(header[:4], 'big')}\tack: {int.from_bytes(header[4:8], 'big')}")
            if self.connected:
                self.process_received_data(header, flags, payload, address)
            else: 
                self.state_machine(header, flags)

    def state_machine(self, header, flags):
        seq = int.from_bytes(header[:4], byteorder='big')
        ack = int.from_bytes(header[4:8], byteorder='big')

        if self.state == 1 and flags == ['SYN']: # received SYN; send SYN,ACK
            self.sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                self.sender_sock.bind((self.ip_src,self.port_src if self.port_src else 0))
            except Exception as e:
                    self.to_console_line("System> Err: failed to bind sender_sock; " + str(e))
                    self.sender_sock.close()
                    return
            self.to_console_line("System> received SYN; sending SYN,ACK")
            with self.state_lock:
                self.state = 3
            with self.ack_lock:
                self.ack = seq+1
            self.send(['SYN', 'ACK'])

        elif self.state == 2 and flags == ['SYN', 'ACK']: # received SYN,ACK; send ACK - connection established
            with self.ack_lock:
                self.ack = seq+1
            self.send(['ACK'])
            self.to_console_line("System> received SYN,ACK; sending ACK - connection established")
            self.set_connected()

        elif self.state == 3 and flags == ['ACK']: # received ACK after sending SYN,ACK - connection established 
            self.to_console_line("System> received ACK - connection established")
            self.set_connected()
        
        elif self.state == 1 and flags == ['KEA', 'SYN'] and seq == self.ack and ack == self.seq:
            if self.sender_sock == None:
                self.sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    self.sender_sock.bind((self.ip_src,self.port_src if self.port_src else 0))
                except Exception as e:
                        self.to_console_line("System> Err: failed to bind sender_sock; " + str(e))
                        self.sender_sock.close()
                        self.sender_sock = None
                        return
            self.set_connected()

    def set_connected(self):
        self.connected = True   
        with self.state_lock:
            self.state = 5
        Thread(target=self.keep_alive, daemon=True).start()
        self.to_console_line(f"System> Connected to {self.ip_dst}:{self.port_dst}")

    

    def process_received_data(self, header, flags, payload, address):
        seq = int.from_bytes(header[:4], byteorder='big')
        ack = int.from_bytes(header[4:8], byteorder='big')
        id_number = int.from_bytes(header[10:12], byteorder='big')
        frag_num = int.from_bytes(header[14:], byteorder='big')

        if flags == ['ACK']:
            packet_index = ceil((ack-self.first_seq)/self.frag_size)
            # print(f"Received ack for seq: {ack}\tRelative: ({packet_index})")
            with self.not_acknowledged_packets_lock:
                try:
                    self.not_acknowledged_packets[packet_index] = 1
                except IndexError:
                    print(f"Index error: {packet_index}\t{len(self.not_acknowledged_packets)}\t{ack}\t{self.first_seq}\t{self.frag_size}")
                    exit()
            with self.packet_timers_lock:
                if self.packet_timers[packet_index]:
                    self.packet_timers[packet_index].cancel()
                    self.packet_timers[packet_index] = None
            while self.j < len(self.not_acknowledged_packets) and self.not_acknowledged_packets[self.j-self.window_size]:
                with self.j_lock:
                    self.j += 1
            return
        
        if flags == ['NAK']:
            packet_index = ceil((ack-self.first_seq)/self.frag_size)
            # print(f"Received NAK for seq: {ack}\tRelative: ({packet_index})")
            self.resend_packet(self.packets[packet_index],packet_index)
            return

        if flags == ['KEA', 'SYN']:
            self.send(['KEA', 'ACK'])
            return
        
        if flags == ['KEA', 'ACK']:
            # with self.keep_alive_retries_lock:
            #     self.keep_alive_retries = KEEP_ALIVE_RETRIES
            return


        if len(payload) and not PacketBuilder(self.frag_size).verify_crc16(header, payload): # crc16 check
            print(f'Received a faulty packet: {frag_num}; requesting retransmission')
            self.send(['NAK'])
            return

        if 'FRG' not in flags and 'PSH' in flags:   # not fragmented payload
            self.to_console_line(f"{address[0]}:{address[1]}> {payload.decode('utf-8')}")
            self.send(['ACK'])
            return
        

        if 'FRG' in flags:
            # print(f"Fragment number: {frag_num}\tFragment size: {len(payload)}")
            if id_number not in self.received_fragments:
                self.received_fragments[id_number] = []

            if not any(subdict.get('var') == seq for subdict in self.received_fragments[id_number]):
                self.received_fragments[id_number].append({
                    'frag_num': frag_num,
                    'header': header,
                    'payload': payload,
                    'last': 'MFG' not in flags
                })
            self.send(['ACK'])
            print(f"Successfully received packet: {frag_num}")
        
        if 'FRG' in flags and 'MFG' not in flags:
            self.number_of_fragments = frag_num + 1


        if self.number_of_fragments != 0 and len(self.received_fragments[id_number]) == self.number_of_fragments:  # fragmented, last
            metadata, defragmented, fragment_size, last_fragment_size = PacketBuilder(len(self.received_fragments[id_number][0]['payload'])).defragment_data(self.received_fragments[id_number])
            self.to_console_line(f"{address[0]}:{address[1]}> Received {len(defragmented) + (len(metadata) if metadata else 0)}B of data in {len(self.received_fragments[id_number])} fragments.")
            self.to_console_line(f"{address[0]}:{address[1]}> Fragment size: {fragment_size}B | Last fragment size: {last_fragment_size}B")
            if metadata:
                with open(f"{self.download_folder}/{metadata}", 'wb') as f:
                    f.write(defragmented)
                self.to_console_line(f"System> Saved received file {metadata} to {self.download_folder}")
            else:
                self.to_console_line(f"{address[0]}:{address[1]}> {defragmented.decode('utf-8')}")

            self.received_fragments.pop(id_number)
            self.number_of_fragments = 0


            
    def open_ports(self):
        if not self.listening:
            self.listener_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                self.listener_sock.bind((self.ip_src, self.port_rec))
            except Exception as e:
                self.to_console_line("System> Err: failed to bind listener_sock; " + str(e))
                return
            self.sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                self.sender_sock.bind((self.ip_src,self.port_src if self.port_src else 0))
            except Exception as e:
                    self.to_console_line("System> Err: failed to bind sender_sock; " + str(e))
                    self.sender_sock.close()
                    return
            self.listening = True
            self.listenerThread = Thread(target=self.listen, daemon=True).start()
            self.to_console_line(f"System> Opened port {self.port_rec}")
            self.state += 1

    def keep_alive(self):
        while self.connected:
                if self.last_activity and time.time() - self.last_activity >= self.keep_alive_time:
                    self.send(['KEA', 'SYN'])
                    with self.keep_alive_retries_lock:
                        self.keep_alive_retries -= 1
                    time.sleep(1)
                    if 0 < self.keep_alive_retries < 3:
                        self.to_console_line(f"System> Lost connection - reconnecting; retries left: {self.keep_alive_retries}")
                    time.sleep(4)
                    if self.keep_alive_retries <= 0:
                        self.close_connection()
                        with self.keep_alive_retries_lock:
                            self.keep_alive_retries = KEEP_ALIVE_RETRIES
                else:
                    time.sleep(1)

    def handshake_loop(self):
        timeout = time.time()
        while True:
            if self.connected:
                return

            if time.time() - timeout >= 10:
                break
        with self.state_lock:
            self.state = 1

        self.to_console_line(f"System> Connection refused - timed out")

    def handshake_init(self):
        self.to_console_line("System> sending SYN")
        self.send(['SYN'])
        with self.seq_lock:
            self.seq += 1
        with self.state_lock:
            self.state = 2
        self.handshake_loop()


    def establish_connection(self):
        if self.ip_dst == self.ip_src and self.port_dst == self.port_rec:
            self.to_console_line("System> cannot send and receive from the same IP address and port")
            return

        if not self.listening:
            self.open_ports()

        self.port_src = self.sender_sock.getsockname()[1]

        # handshake
        Thread(target=self.handshake_init, daemon=True).start()


    def close_ports(self):
        self.close_connection()
        if self.listening:
            self.listening = False
            self.listener_sock.close()
            self.sender_sock.close()
            self.sender_sock = None
            self.listener_sock = None
            with self.state_lock:
                self.state = 0
            self.to_console_line(f"System> Closed port {self.port_rec}")


    def close_connection(self): # placeholder for now, gonna be a proper connection FIN
        if self.connected:
            self.connected = False
            with self.state_lock:
                self.state = 1
            with self.last_activity_lock:
                self.last_activity = None
            self.to_console_line("System> Disconnected")

