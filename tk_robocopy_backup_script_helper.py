import sqlite3
import pathlib
import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

here = pathlib.Path(__file__).parent
_LOG_ANALYZE = here / "log_analyze.py"
_PYTHON = pathlib.Path(sys.executable).resolve()
_SETTINGSPATH = "settings.db"

class SettingsDatabase(sqlite3.Connection):
    ddl = """
    pragma foreign_keys=1;
    pragma recursive_triggers=1;

    create table if not exists config(
    key text,
    value text,
    unique (key) on conflict replace);

    create table if not exists sources(
    id integer primary key,
    path text,
    unique (path) on conflict ignore);

    create table if not exists targets(
    id integer primary key,
    path text,
    source_id integer,
    unique (path) on conflict ignore,
    foreign key (source_id) references sources(id) on delete cascade);
    """

    def __init__(self,name,**kwargs):
        super().__init__(name,**kwargs)
        self.cu = self.cursor()
        self.cu.row_factory = lambda c,r:r[0]
        self.executescript(self.ddl)
        self.commit()
        self.delete_empty()
        list(map(print,self.iterdump()))
    def delete_empty(self):
        self.execute("delete from sources where path=''")
        self.commit()
    def add_source(self,path):
        source = pathlib.Path(path).resolve()
        if source.is_dir():
            self.execute("insert into sources (path) values (?)",(str(source),))
            self.commit()
    def remove_source(self,path):
        self.execute("delete from sources where path=?",(path,))
        self.commit()
        self.delete_empty()
    def remove_target(self,path):
        self.execute("delete from targets where path=?",(path,))
        self.commit()
        self.delete_empty()
    def add_target(self,sourcepath,targetpath):
        target = pathlib.Path(targetpath).resolve()
        if target.is_dir():
            source_id = self.cu.execute("select id from sources where path=?",(sourcepath,)).fetchone()
            self.execute("insert into targets (path,source_id) values (?,?)",(str(target),source_id))
            self.commit()
    def view_sources(self):
        return list(self.cu.execute("select path from sources"))
    def view_targets(self,path):
        source_id = self.cu.execute("select id from sources where path=?",(path,)).fetchone()
        return list(self.cu.execute("select path from targets where source_id=?",(source_id,)))
    def set_output_location(self,path):
        self.execute("insert into config (key,value) values('output_location',?)",(path,))
        self.commit()
    def get_output_location(self):
        value = self.cu.execute("select value from config where key='output_location'").fetchone()
        return value
    def set_logfile_location(self,path):
        self.execute("insert into config (key,value) values('logfile_location',?)",(path,))
        self.commit()
    def get_logfile_location(self):
        value = self.cu.execute("select value from config where key='logfile_location'").fetchone()
        return value
    def main_view(self):
        return list(self.execute("select sources.path,targets.path from sources join targets on sources.id=targets.source_id"))


class Settings:
    _handle = None
    @property
    def cx(self):
        if not self._handle:
            self._handle = sqlite3.connect(
                _SETTINGSPATH,
                factory=SettingsDatabase)
        return self._handle

settings = Settings()

class App(tk.Tk):
    def update_ui(self):
        self.sources.set(settings.cx.view_sources())
        active_source = self.active_source.get()
        if active_source:
            self.remsourcebutton.configure(state="normal")
            self.addtargetbutton.configure(state="normal")
            self.targets.set(settings.cx.view_targets(active_source))
        if self.selected_target:
            self.remtargetbutton.configure(state="normal")
        else:
            self.remtargetbutton.configure(state="disabled")

    def __init__(self):
        super().__init__()
        self.sources = tk.StringVar()
        self.active_source = tk.StringVar()
        self.targets = tk.StringVar()
        self.outputlocation = tk.StringVar()
        self.logfilelocation = tk.StringVar()

        configured_output_location = settings.cx.get_output_location()
        configured_logfilelocation = settings.cx.get_logfile_location()
        if not configured_output_location:
            self.outputlocation.set("-not set-")
        else:
            self.outputlocation.set(configured_output_location)
        self.outputlocation.trace("w",self.outputlocation_trace)

        if not configured_logfilelocation:
            self.logfilelocation.set("-not set-")
        else:
            self.logfilelocation.set(configured_logfilelocation)
        self.logfilelocation.trace("w",self.logfilelocation_trace)

        self.labelwidget_activesource = ttk.Label(self,textvariable=self.active_source)
        self.mainframe = ttk.LabelFrame(self,labelwidget=self.labelwidget_activesource)
        self.mainframe.pack(fill="both",expand=True)
        self.actionframe = ttk.Frame(self)
        self.actionframe.pack(fill="both",expand=True)

        self.sourceframewrapper = ttk.Frame(self.mainframe)
        self.sourceframewrapper.pack(side="left",fill="both",expand=True)
        self.targetframewrapper = ttk.Frame(self.mainframe)
        self.targetframewrapper.pack(side="right",fill="both",expand=True)

        self.sourceframe = ttk.LabelFrame(self.sourceframewrapper,text="Sources")
        self.sourceframe.pack(fill="both",expand=True)
        self.targetframe = ttk.LabelFrame(self.targetframewrapper,text="Targets")
        self.targetframe.pack(fill="both",expand=True)

        self.sourcelistbox = tk.Listbox(self.sourceframe,width=60,listvariable=self.sources)
        self.sourcelistbox.pack(side="left",fill="both",expand=True)
        self.sourcelistboxscroll = tk.Scrollbar(self.sourceframe)
        self.sourcelistboxscroll.pack(side="right",fill="y",expand=True,anchor="w")
        self.sourcelistbox.configure(yscrollcommand=self.sourcelistboxscroll.set)
        self.sourcelistboxscroll.configure(command=self.sourcelistbox.yview)

        self.targetlistbox = tk.Listbox(self.targetframe,width=60,listvariable=self.targets)
        self.targetlistbox.pack(side="left",fill="both",expand=True)
        self.targetlistboxscroll = tk.Scrollbar(self.targetframe)
        self.targetlistboxscroll.pack(side="right",fill="y",expand=True,anchor="w")
        self.targetlistbox.configure(yscrollcommand=self.targetlistboxscroll.set)
        self.targetlistboxscroll.configure(command=self.targetlistbox.yview)

        self.sourcebuttonbox = ttk.Frame(self.sourceframewrapper)
        self.sourcebuttonbox.pack(side="bottom")
        self.addsourcebutton = ttk.Button(self.sourcebuttonbox,text="Add Source",command=self.add_source)
        self.addsourcebutton.pack()
        self.remsourcebutton = ttk.Button(self.sourcebuttonbox,text="Remove Source",command=self.remove_source)
        self.remsourcebutton.pack()
        self.remsourcebutton.configure(state="disabled")

        self.targetbuttonbox = ttk.Frame(self.targetframewrapper)
        self.targetbuttonbox.pack(side="bottom")
        self.addtargetbutton = ttk.Button(self.targetbuttonbox,text="Add Target",command=self.add_target)
        self.addtargetbutton.pack()
        self.remtargetbutton = ttk.Button(self.targetbuttonbox,text="Remove Target",command=self.remove_target)
        self.remtargetbutton.pack()
        self.addtargetbutton.configure(state="disabled")
        self.remtargetbutton.configure(state="disabled")

        self.setoutputlocationbutton = ttk.Button(self.actionframe,text="Set Output Location",command=self.set_output_location)
        self.setoutputlocationbutton.pack()
        self.outputlabel = ttk.Label(self.actionframe,textvariable=self.outputlocation)
        self.outputlabel.pack()

        self.setlogfilelocationbutton = ttk.Button(self.actionframe,text="Set Logfile Location",command=self.set_logfile_location)
        self.setlogfilelocationbutton.pack()
        self.logfilelabel = ttk.Label(self.actionframe,textvariable=self.logfilelocation)
        self.logfilelabel.pack()

        self.separator = ttk.Separator(self.actionframe)
        self.separator.pack(fill="x")

        self.actionbutton = ttk.Button(self.actionframe,text="Generate Script",command=self.generate)
        self.actionbutton.pack()

        self.sourcelistbox.bind("<<ListboxSelect>>",self.sourcelistboxselect)
        self.targetlistbox.bind("<<ListboxSelect>>",self.targetlistboxselect)

        self.update_ui()

    @property
    def selected_source(self):
        index = self.sourcelistbox.curselection()
        if len(index):
            item = self.sourcelistbox.get(index[0])
            return item
    @property
    def selected_target(self):
        index = self.targetlistbox.curselection()
        if len(index):
            item = self.targetlistbox.get(index[0])
            return item
    def sourcelistboxselect(self,event):
        index = self.sourcelistbox.curselection()
        if len(index):
            item = self.sourcelistbox.get(index[0])
            self.active_source.set(item)
        self.update_ui()
    def targetlistboxselect(self,event):
        index = self.targetlistbox.curselection()
        if len(index):
            item = self.targetlistbox.get(index[0])
    def add_source(self):
        p = filedialog.askdirectory()
        if pathlib.Path(p).resolve() == here:
            return
        settings.cx.add_source(p)
        self.update_ui()
    def remove_source(self):
        path = self.selected_source
        settings.cx.remove_source(path)
        self.update_ui()
    def add_target(self):
        p = filedialog.askdirectory()
        if pathlib.Path(p).resolve() == here:
            return
        settings.cx.add_target(self.selected_source,p)
        self.update_ui()
    def remove_target(self):
        path = self.selected_target
        settings.cx.remove_target(path)
        self.update_ui()
    def outputlocation_trace(self,*traceargs):
        loc = self.outputlocation.get()
        settings.cx.set_output_location(loc)
    def set_output_location(self):
        p = filedialog.asksaveasfilename(defaultextension=".cmd")
        path = str(pathlib.Path(p).resolve())
        self.outputlocation.set(path)
    def logfilelocation_trace(self,*traceargs):
        loc = self.logfilelocation.get()
        settings.cx.set_logfile_location(loc)
    def set_logfile_location(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt")
        path = str(pathlib.Path(p).resolve())
        self.logfilelocation.set(path)
    def generate(self):
        lines = []
        output = pathlib.Path(self.outputlocation.get())
        logfile = self.logfilelocation.get()
        line1fmt = """ROBOCOPY "{a}" "{b}" /COPY:DATO /ZB /E /UNILOG:"{c}" /TEE"""
        lineNfmt = """ROBOCOPY "{a}" "{b}" /COPY:DATO /ZB /E /UNILOG+:"{c}" /TEE"""
        fmt = line1fmt
        for source,target in settings.cx.main_view():
            lines.append(fmt.format(a=source,b=target,c=logfile))
            fmt = lineNfmt
        lines.append('"{}" "{}" "{}"'.format(_PYTHON,_LOG_ANALYZE,logfile))
        with open(output,"w") as f:
            f.write("\n".join(lines))


# {{{1

if __name__ == "__main__":
    app = App()
    app.mainloop()
