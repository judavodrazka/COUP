import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import time


class GUI:

    def __init__(self, conn):
        self.darkest = "#0d0d0d"
        self.dark = "#212121"
        self.light = "#2f2f2f"
        self.lighter = "#676767"
        self.lightest = "#ffffff"

        self.conn = conn
        self.send_line = None

        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.root.config(bg=self.dark)
        self.root.title("UDP communication")

        self.infoFrame = tk.Frame(self.root, width=500, height=400, bg=self.dark)
        self.logFrame = tk.Frame(self.root, width=500, height=400, bg=self.dark, pady=5)
        self.controlFrame = tk.Frame(self.root, width=200, height=400, bg=self.dark)

        self.infoFrame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)
        self.logFrame.pack(side=tk.LEFT, fill=tk.Y)
        self.controlFrame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)

        self.infoFrame.pack_propagate(False)
        self.logFrame.pack_propagate(False)
        # self.controlFrame.pack_propagate(False)

        # --- INFO FRAME ---
        tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=f"Listening port:").grid(row=0, column=0, sticky='w')
        self.port_rec = tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=self.conn.ip_src)
        self.port_rec.grid(row=0, column=1, sticky='e')

        tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=f"Source IP:").grid(row=1, column=0, sticky='w')
        self.ip_src = tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=self.conn.ip_src)
        self.ip_src.grid(row=1, column=1, sticky='e')

        tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=f"Source port:").grid(row=2,column=0,sticky='w')    
        self.port_src = tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=self.conn.port_src)
        self.port_src.grid(row=2, column=1, sticky='e')

        tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=f"Destination IP:").grid(row=3,column=0,sticky='w')    
        self.ip_dst = tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=self.conn.ip_dst)
        self.ip_dst.grid(row=3, column=1, sticky='e')

        tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=f"Destination port:").grid(row=4,column=0,sticky='w')    
        self.port_dst = tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=self.conn.port_dst)
        self.port_dst.grid(row=4, column=1, sticky='e')

        tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=f"Fragment Size:").grid(row=5,column=0,sticky='w')    
        self.frag_size = tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text=self.conn.frag_size)
        self.frag_size.grid(row=5, column=1, sticky='e')

        self.state = tk.Label(self.infoFrame, bg=self.dark, fg=self.lightest, text="_"*40+"\n\nStatus: "+("Connected" if self.conn.connected else "Listening" if self.conn.listening else "Off"), justify=tk.LEFT)
        self.state.grid(row=7, column=0, columnspan=2, sticky='w')

        self.download_folder = tk.Entry(self.infoFrame, textvariable=self.conn.download_folder, bg=self.dark, fg=self.lightest, readonlybackground=self.dark, state='readonly')
        self.download_folder.grid(row=8, column=0, columnspan=2, sticky='we')
        scrollbar = ttk.Scrollbar(self.infoFrame, orient='horizontal', command=self.download_folder.xview)
        self.download_folder.config(xscrollcommand=scrollbar.set, )
        scrollbar.grid(row=9, column=0, columnspan=2, sticky='we')
        
        # --- LOG FRAME ---
        self.log = tk.Text(self.logFrame, bg=self.light, fg=self.lightest, width=302, height=26, state=tk.DISABLED, wrap=tk.WORD)
        self.log.pack()
        self.message_entry = tk.Entry(self.logFrame, bg=self.light, fg=self.lightest, width=70)
        self.message_entry.pack(side=tk.LEFT)
        self.send_button = tk.Button(self.logFrame, bg=self.light, fg=self.lightest, relief="flat", text="Send", command=self.send_message, state="disabled", padx=10)#, command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        # --- CONTROL FRAME ---
        tk.Label(self.controlFrame, bg=self.dark, fg=self.lightest, text="Listening port:*").grid(row=0, column=0, sticky='w')
        self.port_rec_entry = tk.Entry(self.controlFrame, bg=self.light, fg=self.lightest)
        self.port_rec_entry.grid(row=1, column=0, columnspan=2, sticky='we', padx=(20,10))
        tk.Button(self.controlFrame, bg=self.light, fg=self.lightest, relief="flat", text="Confirm", command=lambda: self.update_values("port_rec")).grid(row=1, column=2)

        tk.Label(self.controlFrame, bg=self.dark, fg=self.lightest, text="Source IP:*").grid(row=2, column=0, sticky='w')
        self.ip_src_entry = tk.Entry(self.controlFrame, bg=self.light, fg=self.lightest)
        self.ip_src_entry.grid(row=3, column=0, columnspan=2, sticky='we', padx=(20,10))
        tk.Button(self.controlFrame, bg=self.light, fg=self.lightest, relief="flat", text="Confirm", command=lambda: self.update_values("ip_src")).grid(row=3, column=2)

        tk.Label(self.controlFrame, bg=self.dark, fg=self.lightest, text="Source port:").grid(row=4, column=0, sticky='w')
        self.port_src_entry = tk.Entry(self.controlFrame, bg=self.light, fg=self.lightest)
        self.port_src_entry.grid(row=5, column=0, columnspan=2, sticky='we', padx=(20,10))
        tk.Button(self.controlFrame, bg=self.light, fg=self.lightest, relief="flat", text="Confirm", command=lambda: self.update_values("port_src")).grid(row=5, column=2)

        tk.Label(self.controlFrame, bg=self.dark, fg=self.lightest, text="Destination IP:*").grid(row=6, column=0, sticky='w')
        self.ip_dst_entry = tk.Entry(self.controlFrame, bg=self.light, fg=self.lightest)
        self.ip_dst_entry.grid(row=7, column=0, columnspan=2, sticky='we', padx=(20,10))
        tk.Button(self.controlFrame, bg=self.light, fg=self.lightest, relief="flat", text="Confirm", command=lambda: self.update_values("ip_dst")).grid(row=7, column=2)
        
        tk.Label(self.controlFrame, bg=self.dark, fg=self.lightest, text="Destination port:*").grid(row=8, column=0, sticky='w')
        self.port_dst_entry = tk.Entry(self.controlFrame, bg=self.light, fg=self.lightest)
        self.port_dst_entry.grid(row=9, column=0, columnspan=2, sticky='we', padx=(20,10))
        tk.Button(self.controlFrame, bg=self.light, fg=self.lightest, relief="flat", text="Confirm", command=lambda: self.update_values("port_dst")).grid(row=9, column=2)

        tk.Label(self.controlFrame, bg=self.dark, fg=self.lightest, text="Fragmentation size:").grid(row=10, column=0, sticky='w')
        self.frag_size_entry = tk.Entry(self.controlFrame, bg=self.light, fg=self.lightest)
        self.frag_size_entry.grid(row=11, column=0, columnspan=2, sticky='we', padx=(20,10))
        tk.Button(self.controlFrame, bg=self.light, fg=self.lightest, relief="flat", text="Confirm", command=lambda: self.update_values("frag_size")).grid(row=11, column=2)


        self.open_ports_button = tk.Button(self.controlFrame, bg=self.light, fg=self.lightest, relief="flat", text=('Close ports' if self.conn.listening else 'Open ports'), width=15, height=1, command=self.open_ports)
        self.open_ports_button.grid(row=12,column=0,sticky='w', padx=(0,10), pady=(25,0))

        self.connect_button = tk.Button(self.controlFrame, bg=self.light, fg=self.lightest, relief="flat", text=('Disconnect' if self.conn.connected else 'Connect'), width=15, height=1, command=self.establish_connection)
        self.connect_button.grid(row=12, column=1,sticky='e', padx=(10,0), pady=(25,0))

        self.select_file_button = tk.Button(self.controlFrame, bg=self.light, fg=self.lightest, relief="flat", text='Select file', width=15, height=1, command=self.select_file)
        self.select_file_button.grid(row=13, column=0,sticky='w', pady=25, padx=(0,10))

        self.select_download_folder_button = tk.Button(self.controlFrame, bg=self.light, fg=self.lightest, relief="flat", text='Download folder', width=15, height=1, command=self.select_folder)
        self.select_download_folder_button.grid(row=13, column=1, pady=25, sticky='e', padx=(10,0))

        self.clear_log_button = tk.Button(self.controlFrame, bg=self.light, fg=self.lightest, relief="flat", text='Clear', height=1, command=self.clear_log)
        self.clear_log_button.grid(row=14, column=0, columnspan=2, sticky='we', pady=(10,0))


        self.update_info()
        self.update_log()
        self.message_sendable()
        self.download_folder.config(state='normal')
        self.download_folder.delete(0, tk.END)
        self.download_folder.insert(0, self.conn.download_folder)

        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    def select_folder(self):
        path = filedialog.askdirectory(title="Select download folder")
        self.conn.download_folder = path
        self.download_folder.config(state='normal')
        self.download_folder.delete(0, tk.END)
        self.download_folder.insert(0, self.conn.download_folder)
        self.download_folder.config(state='readonly')


    def select_file(self):
        path = filedialog.askopenfilename(title="Select a file to send")
        self.message_entry.delete(0, tk.END)
        self.message_entry.insert(0, "\\sendfile " + path)

    # send a text message from user input
    def send_message(self):
        message = self.message_entry.get()
        self.send_line = message if message[:10] != '\\sendfile ' else None
        self.conn.send(['PSH'], message)
        self.message_entry.delete(0, tk.END)

    # bind sockets
    def open_ports(self):
        if not self.conn.listening and self.conn.ip_src and self.conn.port_rec and self.conn.ip_dst and self.conn.port_dst:
            self.conn.open_ports()
        
        elif self.conn.listening:
            self.conn.close_ports()
        

    # attempt to connect to specified IPs and ports / or disconnect if a connection has been established already
    def establish_connection(self):
        if (not self.conn.connected # cannot be connected already
            and self.conn.ip_src    # source IP address needs to be specified
            and self.conn.ip_dst    # destination IP needs to be specified
            and self.conn.port_rec  # receiving port needs to be specified
            and self.conn.port_dst):# destination port needs to be specified

            self.conn.establish_connection()
        
        elif self.conn.connected:
            self.conn.close_connection()
        

    # changing values in app logic based on user input
    def update_values(self, name):
        # change in IP addresses or ports necessitates reconnection
        if self.conn.connected and ('port' in name or 'ip' in name):
            self.conn.close_ports()


        value = getattr(self, name+"_entry").get()
        if name.split('_')[0] == 'port' or name.split('_')[0] == 'frag':
            setattr(self.conn, name, (int(value) if len(value) > 0 else None))
        
        else:
            setattr(self.conn, name, (value if len(value) > 0 else None))

        getattr(self, name+"_entry").delete(0, tk.END)

        if self.conn.frag_size == None or not (0 < self.conn.frag_size < 1400):
            self.conn.frag_size = 1400


    # check if "send" button should be disabled
    def message_sendable(self):
        if self.conn.connected:
            if len(self.message_entry.get()) > 0:
                self.send_button.config(state="normal")
            self.select_file_button.config(state="normal")
        
        else: 
            self.send_button.config(state="disabled")
            self.select_file_button.config(state="disabled")

        self.connect_button.config(text=('Disconnect' if self.conn.connected else 'Connect'))
        self.open_ports_button.config(text=('Close ports' if self.conn.listening else 'Open ports'))

        self.root.after(50, self.message_sendable)

    # infoFrame mainloop
    def update_info(self):
        self.port_rec.config(text=self.conn.port_rec if self.conn.port_rec else "")
        self.ip_src.config(text=self.conn.ip_src if self.conn.ip_src else "")
        self.port_src.config(text=self.conn.port_src if self.conn.port_src else "")
        self.ip_dst.config(text=self.conn.ip_dst if self.conn.ip_dst else "")
        self.port_dst.config(text=self.conn.port_dst if self.conn.port_dst else "")
        self.frag_size.config(text=self.conn.frag_size if self.conn.frag_size else "")
        self.state.config(text="_"*40+
                          "\n\nStatus: "+("Connected" if self.conn.connected else "Listening" if self.conn.listening else "Off")+
                          "\nK-A Retries: " + str(self.conn.keep_alive_retries)+
                          "\nLast activity: " + (str(round(time.time() - self.conn.last_activity, 4)) if  self.conn.last_activity else "Disconnected")+
                          "\nDownload folder:\n")

        self.root.after(50, self.update_info)

    # logFrame mainloop
    def update_log(self):
        if len(self.conn.console_line) > 0:
            for l in self.conn.console_line[:]:
                self.log.config(state=tk.NORMAL)
                self.log.insert(tk.END,f"{l}\n")
                self.log.config(state=tk.DISABLED)
                self.conn.console_line.remove(l)
        
        if self.send_line is not None:
            self.log.config(state=tk.NORMAL)
            self.log.insert(tk.END, f"You> {self.send_line}\n")
            self.log.config(state=tk.DISABLED)
            self.send_line = None

        self.root.after(10, self.update_log)

    def clear_log(self):
        self.log.config(state=tk.NORMAL)
        self.log.delete('1.0', tk.END)
        self.log.config(state=tk.DISABLED)


    def exit_app(self):
        self.conn.close_connection()
        self.root.destroy()
        print("App closed")

    def run(self):
        self.root.mainloop()  