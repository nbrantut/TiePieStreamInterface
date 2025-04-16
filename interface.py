import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import libtiepie
import time
import os
import datetime
import h5py
import threading

class InstrumentBox:
    def __init__(self):
        self.frame = None
        self.channels = []
        self.enabled = False

class ChannelInterface:
    def __init__(self, root):
        self.enable_button = None
        self.name_entry = None
        self.scale_entry = None
        self.enabled_var = tk.IntVar(root)
        self.name_var = tk.StringVar(root)
        self.scale_var = tk.DoubleVar(root)
        self.scale_list = []

class Interface():
    def __init__(self):

        self.WATCH_BG_COLOR = '#2e332e'
        self.WATCH_FG_COLOR = '#6bff91'
        
        # oscilloscope object
        self.scp = None
        self.n_instr = 0
        self.chan_names = []
        
        # Create the GUI base
        self.root = tk.Tk()
        self.root.title("TiePie Streaming Interface")
        self.root.geometry('620x700')


        # Key default variables:
        self.foldername = tk.StringVar(self.root, os.path.expanduser('~'))
        self.filename = tk.StringVar(self.root, "datastream")
        fileext_list = [".hdf5", ".csv"]
        self.fileext = tk.StringVar(self.root)
        self.fileext.set(fileext_list[0])

        self.freq = tk.DoubleVar(self.root)
        self.res  = tk.IntVar(self.root)
        self.reclength = tk.IntVar(self.root)
        
        self.newfileperiod = tk.DoubleVar(self.root, 1)
        timeunit_list = ["s", "min", "h", "d", "infty"]
        self.newfileunit = tk.StringVar(self.root, "infty")
        self.new_file_per = 0.0

        self.stop = False
        self.watch = False

        mainframe = ttk.Frame(self.root, padding="10")
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

        # menu
        menubar = tk.Menu(self.root)  
        filemenu = tk.Menu(menubar)  
        filemenu.add_command(label="Open config...", command = self.open_config_file_dialog)  
        filemenu.add_command(label="Save config...", command = self.save_config_file_dialog)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)  
        self.root.config(menu=menubar)

        # File etc
        file_frame = ttk.LabelFrame(mainframe, text="File settings", width=590, height=150)
        file_frame.grid(column=0, row=0, columnspan=2, sticky=tk.N)
        file_frame.grid_propagate(0)
        
        ttk.Label(file_frame, text="Folder:").grid(column=0, row=1, pady=5, padx=5, sticky=tk.E)
        self.folder_entry = ttk.Entry(file_frame, width=40, textvariable=self.foldername)
        self.folder_entry.grid(column=1, row=1, columnspan=4, pady=5, padx=5)
        
        self.browse_button = ttk.Button(file_frame, text="Browse", command=self.browsefolder)
        self.browse_button.grid(column=5, row=1, padx=5, pady=5)
        
        ttk.Label(file_frame, text="File base name:").grid(column=0, row=2, pady=5, sticky=tk.E)
        self.filename_entry = ttk.Entry(file_frame, width=40, textvariable=self.filename)
        self.filename_entry.grid(column=1, row=2, columnspan=4, pady=5, padx=5)
        self.filetype_list = ttk.OptionMenu(file_frame, self.fileext, fileext_list[0],  *fileext_list)
        self.filetype_list.grid(column=5, row=2, padx=5, pady=5)

        ttk.Label(file_frame, text="New file every:").grid(column=0, row=3, pady=5, padx=5, sticky=tk.E)
        self.newfileperiod_entry = ttk.Entry(file_frame, width=14, textvariable=self.newfileperiod)
        self.newfileperiod_entry.grid(column=1, row=3, columnspan=2, padx=5, pady=5, sticky=tk.E)
        self.newfileunit_list = ttk.OptionMenu(file_frame, self.newfileunit, timeunit_list[4],  *timeunit_list)
        self.newfileunit_list.grid(column=3, row=3, padx=5, pady=5, sticky=tk.W)
        self.newfileunit_list.config(width=4)
        
        # Main interaction commands
        op_frame = ttk.LabelFrame(mainframe, text="Operations", width=590, height=70)
        op_frame.grid(column=0, row=1, columnspan=2)
        op_frame.grid_propagate(0)
        for c in [0,1,2,3]:
            op_frame.columnconfigure(c, minsize=140)
        
        self.open_button  = ttk.Button(op_frame, text="Open DEV", command=self.open_dev)
        self.arm_button = ttk.Button(op_frame, text="Arm!", state=tk.DISABLED, command=self.arm_dev)
        self.start_button = ttk.Button(op_frame, text="Stream!", state=tk.DISABLED, command=self.start_streaming)
        self.watch_button = ttk.Button(op_frame, text="Watch!", command=self.open_watch)

        self.open_button.grid(column=0, row=3, columnspan=1, padx=5, pady=5,sticky=tk.W)
        self.arm_button.grid(column=1, row=3, columnspan=1, padx=5, pady=5)
        self.start_button.grid(column=2, row=3, columnspan=1, padx=5, pady=5)
        self.watch_button.grid(column=3, row=3, columnspan=1, padx=5, pady=5,sticky=tk.E)

        # Global options
        self.glob_frame = ttk.LabelFrame(mainframe, text="Global settings", width=590, height=70)
        self.glob_frame.grid(column=0, row=2, columnspan=2)
        self.glob_frame.grid_propagate(0)

        ttk.Label(self.glob_frame, text="Sampling freq. (Hz):").grid(column=0, row=0, padx=5, pady=5)
        self.freq_entry = ttk.Entry(self.glob_frame, width=8, textvariable=self.freq)
        self.freq_entry.grid(column=1,row=0, padx=5, pady=5)

        ttk.Label(self.glob_frame, text="Bit resolution:").grid(column=2, row=0, padx=5, pady=5)
        self.res_list = ttk.OptionMenu(self.glob_frame, self.res, [])
        self.res_list.grid(column=3, row=0, padx=5, pady=5)

        ttk.Label(self.glob_frame, text="Record length:").grid(column=4, row=0, padx=5, pady=5)
        self.reclength_entry = ttk.Entry(self.glob_frame, width=8, textvariable=self.reclength)
        self.reclength_entry.grid(column=5,row=0, padx=5, pady=5)
        
        # Instrument list
        self.instr_list = []
        col = [0,1,0,1]
        row = [3,3,4,4]
        for i in [0,1,2,3]:
            self.instr_list.append(InstrumentBox())
            self.instr_list[i].frame = ttk.LabelFrame(mainframe, text="Serial", width=290, height=180)
            self.instr_list[i].frame.grid(column=col[i], row=row[i],  padx=5, pady=5, sticky=tk.NW)
            self.instr_list[i].frame.grid_propagate(0)
            ttk.Label(self.instr_list[i].frame, text="Channel 1").grid(column=0, row=0, padx=5, pady=5)
            ttk.Label(self.instr_list[i].frame, text="Channel 2").grid(column=0, row=1, padx=5, pady=5)
            ttk.Label(self.instr_list[i].frame, text="Channel 3").grid(column=0, row=2, padx=5, pady=5)
            ttk.Label(self.instr_list[i].frame, text="Channel 4").grid(column=0, row=3, padx=5, pady=5)

            self.instr_list[i].channels = []
            for c in [0,1,2,3]:
                self.instr_list[i].channels.append(ChannelInterface(self.root))

                self.instr_list[i].channels[c].name_var.set("Chan_"+str(4*i + c+1))
                #self.instr_list[i].channels[c].scale_list = ["(V)"]
                self.instr_list[i].channels[c].scale_var.set(0)

                self.instr_list[i].channels[c].enable_button = ttk.Checkbutton(self.instr_list[i].frame, variable=self.instr_list[i].channels[c].enabled_var)
                self.instr_list[i].channels[c].name_entry = ttk.Entry(self.instr_list[i].frame, textvariable=self.instr_list[i].channels[c].name_var, width=8)
                self.instr_list[i].channels[c].scale_entry = ttk.OptionMenu(self.instr_list[i].frame, self.instr_list[i].channels[c].scale_var, [])

                self.instr_list[i].channels[c].enable_button.grid(column=1, row=c, padx=5, pady=5)
                self.instr_list[i].channels[c].name_entry.grid(column=2, row=c, padx=5, pady=5)
                self.instr_list[i].channels[c].scale_entry.grid(column=3, row=c, padx=5, pady=5)
                self.instr_list[i].channels[c].scale_entry.config(width=5)

        # disable everything by default
        self.disable_all_instr()

    def disable_all_instr(self):
        for item in self.glob_frame.winfo_children():
            item.configure(state=tk.DISABLED)
            
        for i in [0,1,2,3]:
            for item in self.instr_list[i].frame.winfo_children():
                item.configure(state=tk.DISABLED)
        
    def browsefolder(self):
        self.foldername.set(filedialog.askdirectory())
        
    def open_dev(self):
        print("Update device list...")
        libtiepie.device_list.update()
        print("Found ", len(libtiepie.device_list), " devices")
        devlist = libtiepie.device_list
        ids = [device._get_product_id() for device in devlist]
        i = 0
        try:
            ind = ids.index(2)
            print("Found combined oscilloscope device")
            device = devlist[ind]
            if device.can_open(libtiepie.DEVICETYPE_OSCILLOSCOPE):
                print("Opening", device.name, "#", device.serial_number)
                self.scp = device.open_oscilloscope()
                sn = device.contained_serial_numbers
                print("Contained serial numbers:")
                for _sn in sn:
                    print(_sn)
                    self.instr_list[i].enabled=True
                    self.instr_list[i].frame.configure(text="Serial #"+str(_sn))
                    for item in self.instr_list[i].frame.winfo_children():
                        item.configure(state=tk.NORMAL)
                            
                    i = i+1

                self.n_instr = i+1
            else:
                print("Cannot open device")
                return
        except:
            print("Single device")
            ind = 0
            device = devlist[ind]
            if device.can_open(libtiepie.DEVICETYPE_OSCILLOSCOPE):
                print("Opening", device.name, "#", device.serial_number)
                self.scp = device.open_oscilloscope()
                sn = device.serial_number
                self.instr_list[i].enabled=True
                self.instr_list[i].frame.configure(text="Serial #"+str(sn))
                for item in self.instr_list[i].frame.winfo_children():
                    item.configure(state=tk.NORMAL)

                self.n_instr = i+1      
            else:
                print("Cannot open device")
                return
                
        if self.n_instr>0:
            if self.scp.measure_modes & libtiepie.MM_STREAM:
                self.enable_options()
            else:
                print("Device does not support streaming mode")
        else:
            print("Oscilloscope(s) cannot be opened")

            

    def arm_dev(self):
        print("Arm device...")
        # set scope parameters:
        self.scp.sample_rate = self.freq.get()
        self.scp.resolution = self.res.get()
        self.scp.record_length = self.reclength.get()
        self.scp.measure_mode = libtiepie.MM_STREAM

        # read it back to check:
        self.freq.set(self.scp.sample_rate)
        self.res.set(self.scp.resolution)
        self.reclength.set(self.scp.record_length)
        
        for c, chan in enumerate(self.scp.channels):
            _c = c%4
            _i = c//4
            chan.enabled = self.instr_list[_i].channels[_c].enabled_var.get()
            chan.range = self.instr_list[_i].channels[_c].scale_var.get()
            chan.coupling = libtiepie.CK_DCV

    def compute_period(self, value, unit):
        if unit=='s':
            return value
        elif unit=='min':
            return value*60
        elif unit=='h':
            return value*3600
        elif unit=='d':
            return value*3600*24

    def start_streaming(self):
        self.arm_dev()
        self.disable_all_instr()

        self.arm_button.configure(state=tk.DISABLED)
        self.start_button.configure(text="Stop", command = self.stop_streaming)

        self.new_file_per = self.compute_period(self.newfileperiod.get(), self.newfileunit.get())
        self.stop = False

        self.run_th = threading.Thread(target=self.run_streaming)
        self.run_th.start()
        #self.run_streaming()

    def run_streaming(self):
        
        fname = os.path.join(self.foldername.get(), self.filename.get())
        okchans = self.chan_indices()
        self.chan_names = self.get_chan_names()

        count = 0
        fcount = 0
        timer = time.time()
        
        print("Acquiring on channels:", okchans)

        if (self.newfileunit.get()!="infty"):
            fullfilename = fname+str(fcount).rjust(6,'0')+self.fileext.get()
        else:
            fullfilename = fname+self.fileext.get()

        print("Make new file:", fullfilename)
        file = self.init_file(fullfilename)

        self.scp.start()

        while not self.stop:
            print("Data chunk", count)
            
            while not (self.scp.is_data_ready or self.scp.is_data_overflow):
                self.root.after(10)
                
            if self.scp.is_data_overflow:
                print("Data overflow!")
                break

            data = self.scp.get_data()
            self.write_data(data, okchans, count, file)
            #print("... data written to", file.name)

            count = count+1

            if self.watch:
                self.root.after(0, self.show_data, data, okchans)

            if (self.newfileunit.get()!="infty"):
                if ((time.time() - timer) >= self.new_file_per):
                    file.close()
                    fcount = fcount+1
                    fullfilename = fname+str(fcount).rjust(6,'0')+self.fileext.get()
                    print("Make new file:", fullfilename)
                    file = self.init_file(fullfilename)
                    timer = time.time()
            
        file.close()
        self.scp.stop()

    def open_watch(self):
        self.watch = True
        self.watch_button.configure(text="Close", command = self.close_watch)
        self.watch_window = tk.Toplevel(self.root, bg=self.WATCH_BG_COLOR)
        self.watch_window.title("Watch")
        self.watch_window.geometry('825x865')
        self.watch_window.protocol("WM_DELETE_WINDOW", self.close_watch)
        self.plot_canvas = []
        self.plot_line_tag = []
        self.plot_text = []
        for i in range(16):
            self.plot_canvas.append(tk.Canvas(self.watch_window, width=400, height=100, bg=self.WATCH_BG_COLOR, bd=-1, highlightthickness  = 0,))
            self.plot_canvas[i].grid(column=i//8, row=i%8, padx=5, pady=5)
            self.plot_line_tag.append(self.plot_canvas[i].create_line([(0,50),(400,50)], fill=self.WATCH_FG_COLOR, width=2))
            self.plot_text.append(self.plot_canvas[i].create_text(1,1,text="", anchor=tk.NW, fill=self.WATCH_FG_COLOR))

    # Where is create_line and create_text?

    def close_watch(self):
        self.watch = False
        self.watch_button.configure(text="Watch!", command = self.open_watch)
        self.watch_window.update()
        self.watch_window.destroy()

    def show_data(self, data, ch):
        for k,c in enumerate(ch):
            ymin = min(data[c])
            ymax = max(data[c])
            stepsz = max(1, len(data[c])//400)
            subdata = data[c][::stepsz]
            line = []
            for i in range(len(subdata)):
                line.append(400*i/len(subdata))
                line.append(20+80*(-(subdata[i]-ymin)/(1e-12 + ymax-ymin) +1))

            #self.plot_canvas[k].coords(self.plot_line_tag[k], [line[0],line[1],line[99],line[100],line[-2],line[-1]])
            self.plot_canvas[k].coords(self.plot_line_tag[k], line) 
            #(line, fill=self.WATCH_FG_COLOR, width=2)
            self.plot_canvas[k].itemconfigure(self.plot_text[k], text=self.chan_names[c]+"  range:"+str(round(ymin,4))+" "+str(round(ymax,4)))#(1,1,text=self.chan_names[c]+"  range:"+str(round(ymin,4))+" "+str(round(ymax,4)), anchor=tk.NW, fill=self.WATCH_FG_COLOR)


    def chan_indices(self):
        ind = []
        for c, chan in enumerate(self.scp.channels):
            if chan.enabled:
                ind.append(c)
        return ind

    def get_chan_names(self):
        cnames=[]
        for i in [0,1,2,3]:
            for c in [0,1,2,3]:
                cnames.append(self.instr_list[i].channels[c].name_var.get())

        return cnames
    

    def init_file(self, fname):
        if self.fileext.get()==".csv":
            f = open(fname, 'w')
            f.write("Date:"+str(datetime.datetime.now())+os.linesep)
            f.write("Sampling freq:"+str(self.scp.sample_rate)+os.linesep)
            f.write("Resolution:"+str(self.scp.resolution)+os.linesep)
            f.write("Record length:"+str(self.scp.record_length)+os.linesep)
            f.write(os.linesep)
            for c, chan in enumerate(self.scp.channels):
                _c = c%4
                _i = c//4
                if chan.enabled:
                    f.write(';'+self.instr_list[_i].channels[_c].name_var.get())

            f.write(os.linesep)

            return f

        elif self.fileext.get()==".hdf5":
            f = h5py.File(fname,'w')
            info = f.create_group("Info")
            info.attrs["Date"] = str(datetime.datetime.now())
            info.attrs["Sampling_freq"] = self.scp.sample_rate
            info.attrs["Resolution"] = self.scp.resolution
            info.attrs["Record_length"] = self.scp.record_length
            for c, chan in enumerate(self.scp.channels):
                _c = c%4
                _i = c//4
                if chan.enabled:
                    info.attrs["chan"+str(c+1).rjust(2,'0')] = self.instr_list[_i].channels[_c].name_var.get()

            return f
            
        
    def write_data(self, data, ch, count, f):
        if self.fileext.get()==".csv":
            for i in range(len(data[ch[0]])):
                for j in range(len(ch)):
                        f.write(';'+str(data[ch[j]][i]))
                f.write(os.linesep)

        elif self.fileext.get()==".hdf5":
            grp = f.create_group("chunk_"+str(count).rjust(8,'0'))
            grp.attrs["Date"] = str(datetime.datetime.now())
            for c in ch:
                grp.create_dataset("chan"+str(c+1).rjust(2,'0'), data=data[c])

        
    def stop_streaming(self):
        try:
            self.stop = True
            self.run_th.join(0)
            self.run_th = None
            
            self.arm_button.configure(state=tk.NORMAL)
            self.start_button.configure(text="Stream!", command = self.start_streaming)
            self.enable_options()
            for i in range(self.n_instr-1):
                for item in self.instr_list[i].frame.winfo_children():
                    item.configure(state=tk.NORMAL)

        except (AttributeError, RuntimeError):
            pass 

    def enable_options(self):
        self.open_button.configure(text="Close DEV", command=self.close_dev)
        self.arm_button.configure(state=tk.NORMAL)
        self.start_button.configure(state=tk.NORMAL)

        for item in self.glob_frame.winfo_children():
            item.configure(state=tk.NORMAL)

        self.freq.set(self.scp.sample_rate)
        self.res.set(self.scp.resolution)
        self.reclength.set(self.scp.record_length)
        # refresh res list
        self.res_list['menu'].delete(0,'end')
        for r in self.scp.resolutions:
            self.res_list['menu'].add_command(label=str(r), command=tk._setit(self.res, r))

        for c, chan in enumerate(self.scp.channels):
            _c = c%4
            _i = c//4
            #self.instr_list[_i].channels[_c].scale_list = chan.ranges
            self.instr_list[_i].channels[_c].enabled_var.set(chan.enabled)

            # refresh scale list
            #self.instr_list[_i].channels[_c].scale_var.set("(V)")
            self.instr_list[_i].channels[_c].scale_entry['menu'].delete(0,'end')
            for scale in chan.ranges:#self.instr_list[_i].channels[_c].scale_list:
                self.instr_list[_i].channels[_c].scale_entry['menu'].add_command(label = str(scale),
                                                                                command=tk._setit(self.instr_list[_i].channels[_c].scale_var, scale))
                
            self.instr_list[_i].channels[_c].scale_var.set(chan.range)
             
            #self.instr_list[i].channels[c].scale_entry.configure(self.instr_list[_i].frame, self.instr_list[i].channels[c].scale_var,  *self.instr_list[_i].channels[_c].scale_list)
            

    def close_dev(self):
        print("Close devices...")
        self.scp = None
        self.open_button.configure(text="Open DEV", command=self.open_dev)
        self.arm_button.configure(state=tk.DISABLED)
        self.start_button.configure(state=tk.DISABLED)
        self.disable_all_instr()
            
    def save_config_file(self, filename):
        print("Save config file as", filename, "...")
        f = open(filename, "w", newline='\n')
        f.write("Date:"+str(datetime.datetime.now())+'\n')
        f.write("File format:"+self.fileext.get()+'\n')
        f.write("New file period:"+str(self.newfileperiod.get())+'\n')
        f.write("New file unit:"+str(self.newfileunit.get())+'\n')
        f.write("Sampling freq:"+str(self.freq.get())+'\n')
        f.write("Resolution:"+str(self.res.get())+'\n')
        f.write("Record length:"+str(self.reclength.get())+'\n')
        for _i in [0,1,2,3]:
            for _c in [0,1,2,3]:
                name = "Instr"+str(_i+1)+"_Chan"+str(_c+1)+":"
                f.write(name+str(self.instr_list[_i].channels[_c].enabled_var.get())+'\n')
                f.write(name+self.instr_list[_i].channels[_c].name_var.get()+'\n')
                f.write(name+str(self.instr_list[_i].channels[_c].scale_var.get())+'\n')
            
        f.close()

    def save_config_file_dialog(self):
        fname = filedialog.asksaveasfilename(initialdir=self.foldername.get(), initialfile=self.filename.get()+"_config", defaultextension=".txt")
        if len(fname)>0:
            self.save_config_file(fname)

    def open_config_file(self, filename):
        print("Open config file ", filename, "...")
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
        self.fileext.set(lines[1].split(':')[1].strip("\n"))
        self.newfileperiod.set(float(lines[2].split(':')[1]))
        self.newfileunit.set(lines[3].split(':')[1].strip("\n"))
        self.freq.set(float(lines[4].split(':')[1]))
        self.res.set(int(lines[5].split(':')[1]))
        self.reclength.set(int(lines[6].split(':')[1]))
        #f.write("Date:"+str(datetime.datetime.now())+os.linesep)
        #f.write("Sampling freq:"+str(self.freq.get())+os.linesep)
        #f.write("Resolution:"+str(self.res.get())+os.linesep)
        n=7
        for _i in [0,1,2,3]:
            for _c in [0,1,2,3]:
                en_val = int(lines[n].split(':')[1])
                name_val = lines[n+1].split(':')[1].strip("\n\r")
                scale_val = float(lines[n+2].split(':')[1])
                self.instr_list[_i].channels[_c].enabled_var.set(en_val)
                self.instr_list[_i].channels[_c].name_var.set(name_val)
                self.instr_list[_i].channels[_c].scale_var.set(scale_val)
                n = n+3

    def open_config_file_dialog(self):
        fname = filedialog.askopenfilename(initialdir=self.foldername.get(), defaultextension=".txt")
        if len(fname)>0:
            self.open_config_file(fname)

inter = Interface()
# Run gui
inter.root.mainloop()

