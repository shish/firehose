import wx


class ChatPanel(wx.Panel):
    def __init__(self, parent, main, chum):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.main = main
        self.chum = chum

        box = wx.BoxSizer(wx.VERTICAL)

        self.chat = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY)
        box.Add(self.chat, 1, wx.EXPAND)

        if chum.keyid:
            self.line = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
            self.Bind(wx.EVT_TEXT_ENTER, self.send_line, self.line)
            box.Add(self.line, 0, wx.EXPAND)

        self.SetSizer(box)
        self.Layout()

    def send_line(self, evt):
        data = self.line.GetValue()
        cmd, _, args = data.partition(" ")
        if cmd == "/me":
            self.main.get_chat(self.chum.uid).show("* %s %s" % (self.main.identity.name, args))
            data = "ACT " + args
        else:
            self.main.get_chat(self.chum.uid).show("%s: %s" % (self.main.identity.name, data))
            data = "MSG " + data
        self.chum.send(data)
        self.line.SetValue("")

    def show(self, msg):
        self.chat.SetValue(self.chat.GetValue() + msg + "\n")
