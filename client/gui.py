#!/usr/bin/env python

import wx
import sys
import logging
import gnupg
import socket
import threading
import base64

from wx.lib.mixins.inspection import InspectableApp

__version__ = "0.0.0"
log = logging.getLogger(__name__)

myEVT_RECV = wx.NewEventType()
EVT_RECV = wx.PyEventBinder(myEVT_RECV, 1)


class RecvEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, value=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        return self._value


def uid_to_name(uid):
    return uid.partition("(")[0].partition("<")[0].strip()



class ChumList(wx.Panel):
    def __get_ids(self):
        ids = ["Anonymous"]
        for key in self.main.gpg.list_keys(True):
            ids.append(key["uids"][0])
        return ids

    def get_my_key(self):
        # find which identity to use
        keyname = self.identity.GetValue()
        my_key = {"uids": ["Anonymous Self"], "keyid": None}
        for key in self.main.gpg.list_keys(True):
            if key["uids"][0] == keyname:
                my_key = key
        return my_key

    def __init__(self, parent, main):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.main = main

        box = wx.BoxSizer(wx.VERTICAL)
        box.SetMinSize((250, 200))

        self.identity = wx.ComboBox(self, choices=self.__get_ids(), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.identity.Select(0)

        self.status = wx.ComboBox(self, choices=["Available", "Busy"], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.status.Select(0)

        self.chums = wx.FlexGridSizer(0, 2)
        self.chums.AddGrowableCol(0)
        self.chum_list = []

        add_chum = wx.Button(self, -1, "Add Chum")

        #self.Bind(ulc.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.char_list)
        #self.Bind(wx.EVT_BUTTON, self.OnAddSetup, add_chum)
        #self.Bind(wx.EVT_BUTTON, self.OnDelSetup, del_chum)

        box.Add(self.identity, 0, wx.EXPAND)
        box.Add(self.status, 0, wx.EXPAND)
        box.Add(self.chums, 1, wx.EXPAND)
        box.Add(add_chum, 0, wx.EXPAND)

        self.SetSizer(box)
        self.Layout()

        self.update()

    def update(self):
        self.chums.Clear(True)
        self.chum_list = []

        for n, key in enumerate(self.main.gpg.list_keys()):
            self.chum_list.append(key["uids"][0])

            name = wx.Button(self, 4100 + n, uid_to_name(key["uids"][0]))
            self.Bind(wx.EVT_BUTTON, self.OnItemSelected, name)
            self.chums.Add(name, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)

            button = wx.Button(self, 4200 + n, label="Online?")
            #self.Bind(wx.EVT_BUTTON, self.OnLaunch, button)
            self.chums.Add(button)

        self.Layout()

    def OnItemSelected(self, evt):
        uid = evt.GetId() - 4100
        self.main.get_chat(self.chum_list[uid])
        self.update()


class ChatPanel(wx.Panel):
    def __init__(self, parent, main, target):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.main = main
        self.target = target

        box = wx.BoxSizer(wx.VERTICAL)

        self.chat = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.line = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)

        self.Bind(wx.EVT_TEXT_ENTER, self.send_line, self.line)

        box.Add(self.chat, 1, wx.EXPAND)
        box.Add(self.line, 0, wx.EXPAND)

        self.SetSizer(box)
        self.Layout()

        #self.show("New chat with " + self.target)

    def send_line(self, evt):
        data = self.line.GetValue()
        self.main.send(self.target, data)
        self.line.SetValue("")

    def show(self, msg):
        self.chat.SetValue(self.chat.GetValue() + msg + "\n")


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

        m_rempasswd = menu.Append(2040, "Accept unsigned messages", "", kind=wx.ITEM_CHECK)

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
        wx.Frame.__init__(self, parent, -1, "Firehose Client [%s]" % __version__, size=(600, 400))
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
        try:
            self.icon = TrayIcon(self)
            if self.config.settings["start-tray"]:
                log.info("Start-in-tray enabled, hiding main window")
                show = False
        except Exception as e:
            log.exception("Failed to create tray icon:")
            self.icon = None
        if show:
            self.Show(True)

    def get_chat(self, name):
        if name not in self.chats:
            log.info("Creating new chat window with %r" % name)
            self.chats[name] = ChatPanel(self.tabs, self, name)
            self.tabs.AddPage(self.chats[name], name)
        self.tabs.SetSelection(1)
        return self.chats[name]

    def __connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("firehose.shishnet.org", 9988))

    def send(self, target, data):
        """
        TODO: add to queue rather than sending directly
        """
        self.__send(target, data)

    def __send(self, target, data):
        """
        TODO: be a thread which reads from a queue and trickles out slowly
        TODO: if queue is empty, trickle random data
        """
        my_key = self.chums.get_my_key()
        my_name = uid_to_name(my_key["uids"][0])
        self.get_chat(target).show("%s: %s" % (my_name, data))
        data = self.gpg.encrypt(data, target, sign=my_key["keyid"], passphrase=self.passphrase, always_trust=True)
        self.sock.sendall(base64.b64encode(str(data.data)))

    def __recv(self):
        while True:
            data = self.sock.recv(4096)
            if not data:
                break
            try:
                data = self.gpg.decrypt(base64.b64decode(data), passphrase=self.passphrase)
                if data:
                    wx.PostEvent(self, RecvEvent(myEVT_RECV, -1, data))
            except Exception as e:
                #self.get_chat("Status").show("Error decoding: %r (%r)" % (data, e))
                pass
        self.sock.close()
        self.sock = None

    def OnRecv(self, evt):
        data = evt.GetValue()
        target = data.username or "Anonymous"
        self.get_chat(target).show("%s: %s" % (uid_to_name(target), data.data))

    def __init__(self, parent):
        self.gpg = gnupg.GPG()
        self.passphrase = "firehose"
        self.chats = {}
        self.sock = None

        self.__init_gui(parent)
        self.__connect()

        self.Bind(EVT_RECV, self.OnRecv)

        thread = threading.Thread(target=self.__recv)
        thread.daemon = True
        thread.start()

    def OnClose(self, evt):
        self.Close()

    def OnWinClose(self, evt):
        log.info("Saving config and exiting")
        if self.icon:
            self.icon.Destroy()
        self.Destroy()

    def OnAbout(self, evt):
        info = wx.AboutDialogInfo()
        info.SetName("Firehose Client")
        info.SetDescription("A GPG-based chat app")
        info.SetVersion(__version__)
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



def main(args=sys.argv):
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)19.19s %(levelname)4.4s %(name)s: %(message)s")
    module_log = logging.getLogger("firehose")
    module_log.setLevel(logging.DEBUG)
    module_log = logging.getLogger("gnupg")
    module_log.setLevel(logging.INFO)

    app = InspectableApp(False)
    frame = MainFrame(None)
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
