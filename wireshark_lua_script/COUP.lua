local coup_proto = Proto("coup", "Communication Over UDP Protocol (COUP)")

local f_seq = ProtoField.uint32("coup.seq", "Sequence Number", base.DEC)
local f_ack = ProtoField.uint32("coup.ack", "Acknowledgement Number", base.DEC)
local f_crc = ProtoField.uint16("coup.crc", "CRC16", base.HEX)
local f_id = ProtoField.uint16("coup.id", "Identification Number", base.HEX)
local f_flags = ProtoField.uint16("coup.flags", "Flags", base.HEX)
local f_frag_num = ProtoField.uint16("coup.frag_num", "Fragment Number", base.DEC)
local f_file_name_len = ProtoField.uint8("coup.file_name_len", "File Name Length", base.DEC)
local f_file_name = ProtoField.string("coup.file_name", "File Name")
local f_data = ProtoField.bytes("coup.data", "Data")

coup_proto.fields = { f_seq, f_ack, f_crc, f_id, f_flags, f_frag_num, f_file_name_len, f_file_name, f_data }

function dissect_flags(flags)
    flags_names = {
        [0x001] = "ACK",
        [0x002] = "PSH",
        [0x004] = "RST",
        [0x008] = "SYN",
        [0x010] = "FIN",
        [0x020] = "FRG",
        [0x040] = "MFG",
        [0x080] = "FIL",
        [0x100] = "KEA",
        [0x200] = "NAK"
    }
    local decodedFlags = {}

    for mask, name in pairs(flags_names) do
        if bit.band(flags, mask) ~= 0 then
            table.insert(decodedFlags, name)
        end
    end

    return table.concat(decodedFlags, ", ")
    
end

function coup_proto.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = "COUP"

    local subtree = tree:add(coup_proto, buffer(), "COUP Protocol Data")

    subtree:add(f_seq, buffer(0, 4))
    subtree:add(f_ack, buffer(4, 4))
    subtree:add(f_crc, buffer(8, 2))
    subtree:add(f_id, buffer(10, 2))
    local flags = buffer(12, 2):uint()
    local decoded = dissect_flags(flags)
    subtree:add(f_flags, buffer(12, 2)):append_text(" [" .. decoded .. "]")
    subtree:add(f_frag_num, buffer(14, 2)) 

    local frag_num = buffer(14, 2):uint()
    

    if bit.band(flags, 0x2) ~= 0 then
        if bit.band(flags, 0x80) ~= 0 and frag_num == 0 then
            local file_name_len = buffer(16, 1):uint()
            subtree:add(f_file_name_len, buffer(16, 1))
            subtree:add(f_file_name, buffer(17, file_name_len))
            subtree:add(f_data, buffer(17+file_name_len))
        else
            subtree:add(f_data, buffer(16))
        end
    end
end

local udp_port = DissectorTable.get("udp.port")
udp_port:add(55777, coup_proto)
udp_port:add(55888, coup_proto)
