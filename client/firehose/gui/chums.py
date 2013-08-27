import wx
import time

from .chat import ChatPanel


class ChumList(wx.Panel):
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
        self.chum_list = []
        self.statuses = {}

        box = wx.BoxSizer(wx.VERTICAL)
        box.SetMinSize((250, 200))

        self.identity = wx.ComboBox(self, choices=[i.uid for i in main.get_identities()], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.identity.Select(0)
        self.Bind(wx.EVT_COMBOBOX, self.OnIdentitySelected, self.identity)

        self.status = wx.ComboBox(self, choices=["Available", "Busy"], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.status.Select(0)
        self.Bind(wx.EVT_COMBOBOX, self.OnStatusSelected, self.status)

        self.chums = wx.FlexGridSizer(0, 2)
        self.chums.AddGrowableCol(0)

        add_chum = wx.Button(self, -1, "Add Chum")

        get_key = wx.Button(self, -1, "Show My ID")
        self.Bind(wx.EVT_BUTTON, self.OnGetKey, get_key)

        box.Add(self.identity, 0, wx.EXPAND)
        box.Add(self.status, 0, wx.EXPAND)
        box.Add(self.chums, 1, wx.EXPAND)
        box.Add(add_chum, 0, wx.EXPAND)
        box.Add(get_key, 0, wx.EXPAND)

        self.SetSizer(box)
        self.Layout()

        self.update()

    def OnIdentitySelected(self, evt):
        self.main.set_identity(self.main.get_chum(self.identity.GetValue()))

    def OnStatusSelected(self, evt):
        self.main.set_status(self.status.GetValue())

    def set_status(self, chum, state):
        self.statuses[chum.uid] = state
        self.update()

    def OnGetKey(self, evt):
        my_key = self.get_my_key()
        if my_key["keyid"]:
            key_data = self.main.gpg.export_keys(my_key["keyid"])
            if key_data:
                self.main.get_chat("Status").show("ID for %s:\n%s" % (my_key["uids"][0], key_data))
        else:
            self.main.get_chat("Status").show("The currently selected ID has no key")

    def update(self):
        self.chums.Clear(True)
        self.chum_list = self.main.get_chums()

        for n, chum in enumerate(self.chum_list):
            name = wx.Button(self, 4100 + n, chum.name)
            self.Bind(wx.EVT_BUTTON, self.OnItemSelected, name)
            self.chums.Add(name, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)

            button = wx.Button(self, 4200 + n, label=self.statuses.get(chum.uid, "Online?"))
            self.Bind(wx.EVT_BUTTON, self.OnRequestPing, button)
            self.chums.Add(button)

        self.Layout()

    def OnItemSelected(self, evt):
        uid = evt.GetId() - 4100
        self.main.get_chat(self.chum_list[uid].uid)
        self.update()

    def OnRequestPing(self, evt):
        uid = evt.GetId() - 4200
        chum = self.chum_list[uid]
        self.set_status(chum, "Checking...")
        chum.send("PING %d" % int(time.time()))
