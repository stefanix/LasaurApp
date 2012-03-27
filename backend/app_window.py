

from Tkinter import Tk, RIGHT, BOTH, RAISED
from ttk import Frame, Button, Style


class Example(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)   
        self.parent = parent
        self.initUI()
        
    def initUI(self):
        self.parent.title("Buttons")
        self.style = Style()
        self.style.theme_use("default")
        
        frame = Frame(self, relief=RAISED, borderwidth=1)
        frame.pack(fill=BOTH, expand=1)
        
        self.pack(fill=BOTH, expand=1)
        
        closeButton = Button(self, text="Close")
        closeButton.pack(side=RIGHT, padx=5, pady=5)
        okButton = Button(self, text="OK")
        okButton.pack(side=RIGHT)
        
        self.centerWindow()
        
    def centerWindow(self):
        w = 290
        h = 150

        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()
        
        x = (sw - w)/2
        y = (sh - h)/2
        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))   
        
        
class TkGui(Tk):
    def __init__(self):
        Tk.__init__(self)   
        # root.iconbitmap(default=os.path.join(data_root(), 'backend', 'lasersaur.ico'))    
        mainframe = Example(self)   
    
    def mainloop(self):
        Tk.mainloop(self)
            