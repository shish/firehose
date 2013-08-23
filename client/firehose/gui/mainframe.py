import wx
import logging

from firehose.gui.chat import ChatPanel
from firehose.gui.chums import ChumList
import firehose.common as common

log = logging.getLogger(__name__)


myEVT_RECV = wx.NewEventType()
EVT_RECV = wx.PyEventBinder(myEVT_RECV, 1)


class RecvEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, value=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        return self._value


class MainFrame(wx.Frame):
    def __menu(self):
        menu_bar = wx.MenuBar()

        ###############################################################
        menu = wx.Menu()
        m_exit = menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Close window and exit program.")
        self.Bind(wx.EVT_MENU, self.OnClose, m_exit)
        menu_bar.Append(menu, "&File")

        ###############################################################
        menu = wx.Menu()

        m_rempasswd = menu.Append(2020, "Ping contacts for their status", "", kind=wx.ITEM_CHECK)
        m_rempasswd = menu.Append(2021, "Broadcast own status changes", "", kind=wx.ITEM_CHECK)
        m_rempasswd = menu.Append(2022, "Respond to status reqests", "", kind=wx.ITEM_CHECK)

        menu.AppendSeparator()

        m_rempasswd = menu.Append(2030, "Request message acknowledgement", "", kind=wx.ITEM_CHECK)
        m_rempasswd = menu.Append(2031, "Acknowledge received messages", "", kind=wx.ITEM_CHECK)

        menu.AppendSeparator()

        m_rempasswd = menu.Append(2040, "Accept anonymous messages", "", kind=wx.ITEM_CHECK)

        menu.AppendSeparator()

        m_start_tray = menu.Append(2050, "Start in Systray", "", kind=wx.ITEM_CHECK)
        #self.m_start_tray = m_start_tray  # event handler needs this object, not just ID?
        #if self.config.settings["start-tray"]:
        #    m_start_tray.Check(True)
        #self.Bind(wx.EVT_MENU, self.OnToggleStartTray, m_start_tray)

        menu_bar.Append(menu, "&Options")

        ###############################################################
        menu = wx.Menu()
        m_about = menu.Append(wx.ID_ABOUT, "&About", "Information about this program")
        self.Bind(wx.EVT_MENU, self.OnAbout, m_about)
        menu_bar.Append(menu, "&Help")

        ###############################################################
        return menu_bar

    def __init_gui(self, parent):
        wx.Frame.__init__(self, parent, -1, "Firehose Client [%s]" % common.__version__, size=(800, 600))
        self.Bind(wx.EVT_CLOSE, self.OnWinClose)

        self.SetMenuBar(self.__menu())
        self.statusbar = self.CreateStatusBar()

        self.chums = ChumList(self, self)

        self.tabs = wx.Notebook(self)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.chums, 0, wx.EXPAND)
        box.Add(self.tabs, 1, wx.EXPAND)
        #self.SetAutoLayout(True)
        self.SetSizer(box)
        self.Layout()

        self.get_chat("Status")

        show = True
        #try:
        #    self.icon = TrayIcon(self)
        #    if self.config.settings["start-tray"]:
        #        log.info("Start-in-tray enabled, hiding main window")
        #        show = False
        #except Exception as e:
        #    log.exception("Failed to create tray icon:")
        #    self.icon = None
        if show:
            self.Show(True)

    def get_chat(self, name):
        if name not in self.chats:
            log.info("Creating new chat window with %r" % name)
            self.chats[name] = ChatPanel(self.tabs, self, self.fhc.get_chum(name))
            self.tabs.AddPage(self.chats[name], name)
        self.tabs.SetSelection(1)
        return self.chats[name]

    def OnData(self, chum, data):
        wx.PostEvent(self, RecvEvent(myEVT_RECV, -1, (chum, data)))

    def OnRecv(self, evt):
        chum, data = evt.GetValue()

        cmd, _, args = data.data.partition(" ")
        if cmd == "MSG":
            self.get_chat(chum.uid).show("%s: %s" % (chum.name, args))
        elif cmd == "ACT":
            self.get_chat(chum.uid).show("* %s %s" % (chum.name, args))
        elif cmd == "PING":
            if data.username:
                self.fhc.send(data.username, "PONG %s" % self.chums.status.GetValue())
        elif cmd == "PONG":
            self.chums.set_status(chum, args)
        else:
            self.get_chat(chum.uid).show("??? %s %s" % (chum.name, data.data))

    def __init__(self, parent):
        self.fhc = common.FHC()
        self.gpg = self.fhc.gpg
        self.chats = {}

        self.__init_gui(parent)

        self.Bind(EVT_RECV, self.OnRecv)
        self.fhc.start(self.OnData)

    def OnClose(self, evt):
        self.Close()

    def OnWinClose(self, evt):
        log.info("Saving config and exiting")
        #if self.icon:
        #    self.icon.Destroy()
        self.Destroy()

    def OnAbout(self, evt):
        info = wx.AboutDialogInfo()
        info.SetName("Firehose Client")
        info.SetDescription("A GPG-based chat app")
        info.SetVersion(common.__version__)
        info.SetCopyright("(c) Shish 2013")
        info.SetWebSite("https://github.com/shish/firehose")
        info.AddDeveloper("Shish <webmaster@shishnet.org>")

        # Had some trouble with pyinstaller not putting these resources
        # in the places they should be, so make sure we can live without
        # them until the pyinstaller config gets fixed
        try:
            info.SetIcon(wx.Icon(resource("icon.ico"), wx.BITMAP_TYPE_ICO))
        except Exception as e:
            log.exception("Error getting icon:")

        try:
            info.SetLicense(file(resource("LICENSE.txt")).read())
        except Exception as e:
            log.exception("Error getting license:")
            info.SetLicense("MIT")

        wx.AboutBox(info)
