import crcmod

class PacketBuilder:

    def __init__(self, frag_size: int, id_num: int = None, seq: int = None, ack: int = None, packet_type: str = 'data', flags: list[str] = None, raw_payload: str = None):
        self.header_length = 16
        self.frag_size = frag_size
        self.id_num = id_num
        self.seq = seq
        self.ack = ack
        self.packet_type = packet_type
        self.flags_array = ["NAK", "KEA", "FIL", "MFG", "FRG", "FIN", "SYN", "RST", "PSH", "ACK"]
        self.flags = flags
        self.raw_payload = raw_payload
        self.header = None
        self.payload = None
        self.packet = []

        self.crc16 = crcmod.predefined.mkPredefinedCrcFun('crc-16')


    def build_header(self, seq: int,  payload: bytes, frag_number: int = 0, flags: list[str]=[]):
        header = b''
        header += seq.to_bytes(4, byteorder='big')                  # sequence number
        header += self.ack.to_bytes(4, byteorder='big')             # acknowledgement number
        header += self.crc16(payload).to_bytes(2, byteorder='big')  # CRC16
        header += self.id_num.to_bytes(2, byteorder='big')          # identification number

        flags_bin = 0
        for i, flag in enumerate(self.flags_array):
            if flag in (self.flags+flags):
                flags_bin |= (1 << (len(self.flags_array) - i - 1))
        
        header += (flags_bin).to_bytes(2, byteorder='big')          # type + reserved + flags

        header += frag_number.to_bytes(2, byteorder='big')          # fragment number
        return header
    

    def format_payload(self):
        try:
            self.payload = bytes(self.raw_payload, encoding="utf-8")    # for messages which are strings
        except TypeError:
            self.payload = self.raw_payload                             # for files, which are already a bytes object
    

    def fragment_data(self):
        if len(self.payload) <= self.frag_size:
            self.packet.append(self.build_header(self.seq, self.payload)+self.payload)
            return False
        fragments = []
        frag_num = 0
        for i in range(0, len(self.payload), self.frag_size):
            seq = (i%self.frag_size) or self.frag_size
            payload = self.payload[i:i+self.frag_size]
            if i + self.frag_size >= len(self.payload): 
                flags = ['FRG']
            else: 
                flags = ['MFG', 'FRG']

            header = self.build_header(self.seq, payload, flags=flags, frag_number=frag_num)
            fragments.append(header+payload)
            frag_num += 1
            self.seq += seq

        self.packet.extend(fragments)
        return True



    def decode_flags(self, header):
        no_flags = len(self.flags_array)
        flag_byte = int.from_bytes(header[12:14], 'big') & ((1<<no_flags) - 1)
        b = 2**(no_flags-1)
        flags = []
        for i in range(no_flags):
            if (flag_byte << i) & b == b:
                flags.append(self.flags_array[i])

        return flags
    

    def defragment_data(self, all_fragments):
        frag_size = len(all_fragments[0]['payload'])
        sorted_fragments = sorted(all_fragments, key=lambda x: x['frag_num'])
        file_name_bytes = None
        file_name = None
        reassembled_payload = b''
        remaining_name_length = 0
        remainder = 0
        for i, f in enumerate(sorted_fragments):
            header = f['header']
            payload = f['payload']

            if i == 0 and 'FIL' in self.decode_flags(header):
                name_length = payload[0]
                remaining_name_length = name_length + 1

            if remaining_name_length > 0:
                remainder = remaining_name_length % frag_size
                file_name_bytes = payload[:remainder or frag_size]
                remaining_name_length -= frag_size
            
            if remainder > 0:
                reassembled_payload += payload[remainder:]
                remainder = 0

            else:
                reassembled_payload += payload

        if file_name_bytes:
            file_name = bytes.decode(file_name_bytes[1:])

        return file_name, reassembled_payload, len(sorted_fragments[0]['payload']), len(sorted_fragments[-1]['payload'])
    
    def verify_crc16(self, header, payload):
        # print(f"Rec: {int.from_bytes(header[8:10], 'big')} | Calc: {self.crc16(payload)}")
        return self.crc16(payload) == int.from_bytes(header[8:10], 'big')