__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2018-2022, Palette2 Splicer Post Processing Project'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 'P2PP@pandora.be'

import sys
import os
import requests
import p2pp.variables as v
import p2pp.gui as gui
from PyQt5 import uic, QtCore

from PyQt5 import QtWebEngineWidgets


def uploadfile(localfile, p3file):
    _error = None

    v.retry_state = True

    while v.p3_hostname == "":
        form.label_5.setText("Please specify hostname or IP.\nP3_HOSTNAME config parameter missing.")
        form.RetryButton.setText("Upload")
        window.show()
        gui.app.exec()
        v.p3_hostname = form.hostname.text()
    else:
        form.hostname.setText(v.p3_hostname)

    form.RetryButton.setText("Retry")

    gui.create_logitem("Sending file {}  to P3 ({})".format(p3file, v.p3_hostname), "blue", True)
    gui.app.sync()
    while v.retry_state:
        try:
            with open(localfile, "rb") as mcfx_file:
                gui.create_logitem("Uploading {}".format(p3file), "blue", True)
                upload_dict = {p3file: mcfx_file}
                url = "http://{}:3000/print-file".format(v.p3_hostname)
                response = requests.post(url, files=upload_dict)
                if response.ok:
                    _error = None
                    v.retry_state = False
                    gui.create_logitem("Upload completed".format(p3file), "blue", True)
                else:
                    _error = "Error [{}] {} ".format(response.status_code, response.reason)

        except Exception as e:
            gui.log_warning("Could not send file ({}) to P3 ({})".format(p3file, v.p3_hostname))
            gui.app.sync()
            _error = "Connection Error occurred!"

        if v.showwebbrowser:
            try:
                # todo - change to supplied hostname:5000
                # tgtName = "http://{}:5000".format(v.p3_hostname)

                tgtName = "http://{}:5000".format("0PLM-P3P")
                webform.webBrowser.load(QtCore.QUrl("http://192.168.3.201:5000"))
                webwindow.show()
                gui.app.exec()

            except Exception as e:
                gui.logexception(e)

        if v.retry_state and _error is not None:
            form.label_5.setText(_error)
            window.show()
            gui.app.exec()
            v.p3_hostname = form.hostname.text()

    gui.close_button_enable()


def on_clickretry():
    v.retry_state = True
    window.hide()
    # webwindow.hide()
    gui.app.quit()


def on_clickclose():
    webwindow.hide()
    # webwindow.hide()
    gui.close_button_enable()


def on_clickabort():
    v.retry_state = False
    gui.create_logitem("Upload aborted by user")
    window.hide()
    gui.app.quit()

# LOAD FORM

if sys.platform == 'darwin':
    if len(os.path.dirname(sys.argv[0])) > 0:
        ui = "{}/SendError.ui".format(os.path.dirname(sys.argv[0]))
    else:
        ui = "SendError.ui"
else:
    ui = "SendError.ui"
    if len(os.path.dirname(sys.argv[0])) > 0:
        ui = "{}\\SendError.ui".format(os.path.dirname(sys.argv[0]))
    else:
        ui = "SendError.ui"

Form, Window = uic.loadUiType(ui)
window = Window()
form = Form()

form.setupUi(window)
window.setWindowFlag(QtCore.Qt.CustomizeWindowHint, True)
window.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
window.setWindowFlag(QtCore.Qt.WindowMinMaxButtonsHint, False)

form.AbortButton.clicked.connect(on_clickabort)
form.RetryButton.clicked.connect(on_clickretry)


if sys.platform == 'darwin':
    if len(os.path.dirname(sys.argv[0])) > 0:
        ui = "{}/p3browser.ui".format(os.path.dirname(sys.argv[0]))
    else:
        ui = "p3browser.ui"
else:
    ui = "p3browser.ui"
    if len(os.path.dirname(sys.argv[0])) > 0:
        ui = "{}\\p3browser.ui".format(os.path.dirname(sys.argv[0]))
    else:
        ui = "p3browser.ui"

WebForm, WebWindow = uic.loadUiType(ui)
webwindow = WebWindow()

webwindow.setWindowFlags(webwindow.windowFlags() | QtCore.Qt.CustomizeWindowHint)
webwindow.setWindowFlags(webwindow.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)

webform = WebForm()
webform.setupUi(webwindow)
webform.closeButton.clicked.connect(on_clickclose)
