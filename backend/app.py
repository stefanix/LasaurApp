import os
import wx 
import wx.html2 

class MyBrowser(wx.Frame): 
    def __init__(self, *args, **kwds): 
        wx.Frame.__init__(self, *args, **kwds) 
        sizer = wx.BoxSizer(wx.VERTICAL) 
        self.browser = wx.html2.WebView.New(self) 
        sizer.Add(self.browser, 1, wx.EXPAND, 10) 
        self.SetSizer(sizer) 
        self.SetSize((1024, 768)) 
        
        self.CreateStatusBar() # A Statusbar in the bottom of the window
        
        # Setting up the menu.
        filemenu= wx.Menu()
        
        # wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets.
        menuAbout = filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        menuExit = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")        

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        
        # Set events.
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)        
        
        self.Show(True)        
        
    def OnAbout(self,e):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog( self, "A small text editor", "About Sample Editor", wx.OK)
        dlg.ShowModal() # Show it
        dlg.Destroy() # finally destroy it when finished.

    def OnExit(self,e):
        self.Close(True)  # Close the frame.        

app = wx.App() 
dialog = MyBrowser(None, -1) 
dialog.browser.LoadURL("http://127.0.0.1:4444/") 
dialog.Show() 
app.MainLoop() 
  
  
  
  # 1 import wx
  #  2 
  #  3 class MainWindow(wx.Frame):
  #  4     def __init__(self, parent, title):
  #  5         wx.Frame.__init__(self, parent, title=title, size=(200,100))
  #  6         self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
  #  7         self.CreateStatusBar() # A Statusbar in the bottom of the window
  #  8 
  # 
  # 22 
  # 23 app = wx.App(False)
  # 24 frame = MainWindow(None, "Sample editor")
  # 25 app.MainLoop()