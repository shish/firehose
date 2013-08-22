#!/usr/bin/env python

import sys
import logging

from wx.lib.mixins.inspection import InspectableApp
from firehose.gui.mainframe import MainFrame

import firehose.common as common

log = logging.getLogger(__name__)



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
