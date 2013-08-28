import wx
import time
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


class MainFrame(wx.Frame, common.FirehoseClient):
    def __init__(self, parent):
        # wx.Frame.__init__(self)
        common.FirehoseClient.__init__(self)
        self.load_config()

        self.chats = {}

        self.__init_gui(parent)

        self.Bind(EVT_RECV, self.on_recv)
        self.start_recv_thread()

    ###################################################################
    # GUI setup
    ###################################################################

    def __init_gui(self, parent):
        wx.Frame.__init__(self, parent, -1, "Firehose Client [%s]" % common.__version__, size=(800, 600))
        self.Bind(wx.EVT_CLOSE, self.on_win_close)

        self.SetMenuBar(self.__gui_menu())
        self.statusbar = self.CreateStatusBar()

        self.chums = self.__gui_control_panel()

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

    def __gui_menu(self):
        menu_bar = wx.MenuBar()

        ###############################################################
        menu = wx.Menu()
        m_exit = menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Close window and exit program.")
        self.Bind(wx.EVT_MENU, self.on_close, m_exit)
        menu_bar.Append(menu, "&File")

        ###############################################################
        menu = wx.Menu()

        m_status_request = menu.Append(2020, "Ping contacts for their status", "", kind=wx.ITEM_CHECK)
        if self.config["status_request"]:
            m_status_request.Check(True)
        def on_toggle_status_request(evt):
            self.config["status_request"] = m_status_request.IsChecked()
            if self.config["status_request"]:
                for chum in self.get_chums():
                    self.chums.set_status(chum, "Checking...")
                    chum.send("PING %d" % int(time.time()))
        self.Bind(wx.EVT_MENU, on_toggle_status_request, m_status_request)

        m_status_broadcast = menu.Append(2021, "Broadcast own status changes", "", kind=wx.ITEM_CHECK)
        if self.config["status_broadcast"]:
            m_status_broadcast.Check(True)
        def on_toggle_status_broadcast(evt):
            self.config["status_broadcast"] = m_status_broadcast.IsChecked()
            if self.config["status_broadcast"]:
                self.set_status(self.status)
        self.Bind(wx.EVT_MENU, on_toggle_status_broadcast, m_status_broadcast)

        m_status_respond = menu.Append(2022, "Respond to status reqests", "", kind=wx.ITEM_CHECK)
        if self.config["status_respond"]:
            m_status_respond.Check(True)
        def on_toggle_status_respond(evt):
            self.config["status_respond"] = m_status_respond.IsChecked()
            if self.config["status_respond"]:
                self.set_status(self.status)
        self.Bind(wx.EVT_MENU, on_toggle_status_respond, m_status_respond)

        menu.AppendSeparator()

        #m_msg_ack_request = menu.Append(2030, "Request message acknowledgement", "", kind=wx.ITEM_CHECK)
        #if self.config["msg_ack_request"]:
        #    m_msg_ack_request.Check(True)

        #m_msg_ack_respond = menu.Append(2031, "Acknowledge received messages", "", kind=wx.ITEM_CHECK)
        #if self.config["msg_ack_respond"]:
        #    m_msg_ack_respond.Check(True)

        #menu.AppendSeparator()

        m_accept_anon = menu.Append(2040, "Accept anonymous messages", "", kind=wx.ITEM_CHECK)
        if self.config["accept_anon"]:
            m_accept_anon.Check(True)
        def on_toggle_accept_anon(evt):
            self.config["accept_anon"] = m_accept_anon.IsChecked()
        self.Bind(wx.EVT_MENU, on_toggle_accept_anon, m_accept_anon)

        #menu.AppendSeparator()

        #m_start_in_tray = menu.Append(2050, "Start in Systray", "", kind=wx.ITEM_CHECK)
        #if self.config["start_in_tray"]:
        #    m_start_in_tray.Check(True)
        #self.m_start_tray = m_start_tray  # event handler needs this object, not just ID?
        #if self.config.settings["start-tray"]:
        #    m_start_tray.Check(True)
        #self.Bind(wx.EVT_MENU, self.on_toggle_start_tray, m_start_tray)

        menu_bar.Append(menu, "&Options")

        ###############################################################
        menu = wx.Menu()
        m_about = menu.Append(wx.ID_ABOUT, "&About", "Information about this program")
        self.Bind(wx.EVT_MENU, self.on_about, m_about)
        menu_bar.Append(menu, "&Help")

        ###############################################################
        return menu_bar

    def __gui_control_panel(self):
        self.chum_list = []
        self.statuses = {}

        box = wx.BoxSizer(wx.VERTICAL)
        box.SetMinSize((250, 200))

        self.identity = wx.ComboBox(self, choices=[i.uid for i in self.get_identities()], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.identity.Select(0)
        self.Bind(wx.EVT_COMBOBOX, self.on_identity_selected, self.identity)

        self.status = wx.ComboBox(self, choices=["Available", "Busy"], style=wx.CB_DROPDOWN)
        self.status.Select(0)
        self.Bind(wx.EVT_COMBOBOX, self.on_status_selected, self.status)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_status_selected, self.status)

        self.chum_grid = wx.FlexGridSizer(0, 2)
        self.chum_grid.AddGrowableCol(0)

        add_chum = wx.Button(self, -1, "Add Chum")

        get_key = wx.Button(self, -1, "Show My ID")
        self.Bind(wx.EVT_BUTTON, self.on_get_key, get_key)

        box.Add(self.identity, 0, wx.EXPAND)
        box.Add(self.status, 0, wx.EXPAND)
        box.Add(self.chum_grid, 1, wx.EXPAND)
        box.Add(add_chum, 0, wx.EXPAND)
        box.Add(get_key, 0, wx.EXPAND)

        self.update_chum_list()
        return box

    def get_my_key(self):
        # find which identity to use
        keyname = self.identity.GetValue()
        my_key = {"uids": ["Anonymous Self"], "keyid": None}
        for key in self.gpg.list_keys(True):
            if key["uids"][0] == keyname:
                my_key = key
        return my_key

    def update_chum_list(self):
        self.chum_grid.Clear(True)
        self.chum_list = self.get_chums()

        for n, chum in enumerate(self.chum_list):
            name = wx.Button(self, 4100 + n, chum.name)
            self.Bind(wx.EVT_BUTTON, self.on_chum_selected, name)
            self.chum_grid.Add(name, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)

            button = wx.Button(self, 4200 + n, label=self.statuses.get(chum.uid, "Online?"))
            self.Bind(wx.EVT_BUTTON, self.on_request_ping, button)
            self.chum_grid.Add(button)

        self.Layout()

    def set_status(self, chum, state):
        self.statuses[chum.uid] = state
        self.update_chum_list()

    def get_chat(self, name):
        if name not in self.chats:
            log.info("Creating new chat window with %r" % name)
            self.chats[name] = ChatPanel(self.tabs, self, self.get_chum(name))
            self.tabs.AddPage(self.chats[name], name)
        self.tabs.SetSelection(1)
        return self.chats[name]

    ###################################################################
    # GUI event handling
    ###################################################################

    def on_identity_selected(self, evt):
        self.set_identity(self.get_chum(self.identity.GetValue()))

    def on_status_selected(self, evt):
        self.set_status(self.status.GetValue())

    def on_get_key(self, evt):
        my_key = self.get_my_key()
        if my_key["keyid"]:
            key_data = self.gpg.export_keys(my_key["keyid"])
            if key_data:
                self.get_chat("Status").show("ID for %s:\n%s" % (my_key["uids"][0], key_data))
        else:
            self.get_chat("Status").show("The currently selected ID has no key")

    def on_chum_selected(self, evt):
        uid = evt.GetId() - 4100
        self.get_chat(self.chum_list[uid].uid)
        self.update_chum_list()

    def on_close(self, evt):
        self.Close()

    def on_win_close(self, evt):
        log.info("Saving config and exiting")
        self.save_config()
        #if self.icon:
        #    self.icon.Destroy()
        self.Destroy()

    def on_about(self, evt):
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

    def on_request_ping(self, evt):
        uid = evt.GetId() - 4200
        chum = self.chum_list[uid]
        self.set_status(chum, "Checking...")
        chum.send("PING %d" % int(time.time()))

    ###################################################################
    # Network event handling
    ###################################################################

    def on_raw_data(self, data):
        chum = self.get_chum(data.username)
        target = None
        wx.PostEvent(self, RecvEvent(myEVT_RECV, -1, (chum, target, data)))

    def on_recv(self, evt):
        chum, target, data = evt.GetValue()
        self.on_data(chum, target, data)

    def on_msg(self, chum, target, msg):
        self.get_chat(chum.uid).show("%s: %s" % (chum.name, msg))

    def on_act(self, chum, target, msg):
        self.get_chat(chum.uid).show("* %s %s" % (chum.name, msg))

