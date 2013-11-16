import wx


class CreateKeyDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title="Create New ID", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        name_label = wx.StaticText(self, -1, "Name")
        self.name = wx.TextCtrl(self, -1)
        comment_label = wx.StaticText(self, -1, "Comment")
        self.comment = wx.TextCtrl(self, -1)
        email_label = wx.StaticText(self, -1, "Email")
        self.email = wx.TextCtrl(self, -1)
        exp = wx.StaticText(self, -1, "Note: generating a key can take a couple of minutes,\nduring which the program will be unresponsive")
        buttons = self.CreateButtonSizer(wx.OK|wx.CANCEL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(name_label, 0, wx.ALL, 5)
        sizer.Add(self.name, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(comment_label, 0, wx.ALL, 5)
        sizer.Add(self.comment, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(email_label, 0, wx.ALL, 5)
        sizer.Add(self.email, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(exp, 0, wx.ALL, 5)
        sizer.Add(buttons, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizerAndFit(sizer)

    def GetValue(self):
        return (
            self.name.GetValue(),
            self.comment.GetValue(),
            self.email.GetValue()
        )
