#!/usr/bin/env python

import socket, threading, time
import Tkinter as tkinter
import gnupg
import base64
#from Tkinter.scrolledtext import ScrolledText


class ChatWin(object):
    def __init__(self, main, target):
        self.main = main
        self.target = target
        self.root = tkinter.Toplevel(main.root)
        self.root.title(target)

        self.output_box = tkinter.Text(self.root, width=40, height=15)
        #self.output_box.config(state=tkinter.DISABLED)
        self.output_box.pack(fill=tkinter.BOTH, expand=1)
        self.input_box = tkinter.Entry(self.root)
        self.input_box.pack(fill=tkinter.BOTH)
        self.input_box.bind("<KeyRelease-Return>", self.__send)
        self.input_box.focus_set()

    def show(self, data):
        self.output_box.insert(tkinter.END, data + "\n")
        self.output_box.yview(tkinter.END)

    def __send(self, e):
        data = self.input_box.get()
        self.show("You: " + data)
        data = self.main.gpg.encrypt(data, self.target, passphrase=self.main.passphrase, always_trust=True)
        self.main.sock.sendall(base64.b64encode(str(data.data)))
        self.input_box.delete(0, tkinter.END)


class KeyGen(object):
    def __init__(self, main):
        self.main = main
        self.root = tkinter.Toplevel(main.root)
        self.root.title("Create Account")

        self.label = tkinter.Label(self.root, "You don't appear to have any private keys in your GPG keyring")
        self.label.pack(fill=tkinter.BOTH)

        self.name_box = tkinter.Entry(self.root)
        self.name_box.pack(fill=tkinter.BOTH)
        self.email_box = tkinter.Entry(self.root)
        self.email_box.pack(fill=tkinter.BOTH)
        self.comment_box = tkinter.Entry(self.root)
        self.comment_box.pack(fill=tkinter.BOTH)


class Noise(object):
    def __init__(self):
        self.sock = None
        self.targets = []
        self.passphrase = "firehose"
        self.gpg = gnupg.GPG()  # gnupghome="./gpg/", verbose=False)
        self.chats = {}

    def __connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("firehose.shishnet.org", 9988))

    def __get_chat(self, target):
        if target not in self.chats:
            self.chats[target] = ChatWin(self, target)
        return self.chats[target]

    def __recv(self):
        while True:
            data = self.sock.recv(4096)
            if not data:
                break
            try:
                data = self.gpg.decrypt(base64.b64decode(data), passphrase=self.passphrase)
                if data:
                    target = data.username or "Unknown"
                    self.__get_chat(target).show("%s: %s" % (target.split()[0], data.data))
            except Exception as e:
                self.__get_chat("Status").show("Error decoding: %r (%r)" % (data, e))
        self.sock.close()

    def __start_chat(self, evt):
        w = evt.widget
        index = int(w.curselection()[0])
        value = w.get(index).split()[0]
        self.__get_chat(value)

    def __gui(self):
        chums = tkinter.Listbox(self.root)
        for key in self.gpg.list_keys():
            chums.insert(tkinter.END, "%s - %s" % (key["uids"][0], key["keyid"]))
        chums.bind("<Double-Button-1>", self.__start_chat)
        chums.pack()

    def main(self):
        self.root = tkinter.Tk()
        self.root.title("Chums")
        self.__gui()

        self.__get_chat("Status")
        self.__connect()

        thread = threading.Thread(target=self.__recv)
        thread.daemon = True
        thread.start()

        if not self.gpg.list_keys(True):
            KeyGen(self)

        self.root.mainloop()

if __name__ == "__main__":
    n = Noise()
    n.main()
