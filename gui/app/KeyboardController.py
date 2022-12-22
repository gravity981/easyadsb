from PyQt5.QtCore import QObject, pyqtSlot, Qt, QVariant
from PyQt5.QtQuick import QQuickItem
from PyQt5.QtGui import QKeyEvent, QGuiApplication
import logging

logger = logging.getLogger("logger")


class KeyboardController(QObject):

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    @pyqtSlot(QQuickItem, QVariant)
    def onKeyPressed(self, receiver, txt):
        code, text = self._getTextAndCode(txt)
        logger.debug("key pressed {}, {}".format(code, text))
        ev = QKeyEvent(QKeyEvent.KeyPress, code, Qt.NoModifier, text, False)
        QGuiApplication.sendEvent(receiver, ev)

    @pyqtSlot(QQuickItem, QVariant)
    def onKeyLongPressed(self, receiver, txt):
        code, text = self._getTextAndCode(txt)
        logger.debug("key long pressed {}, {}".format(code, text))
        ev = QKeyEvent(QKeyEvent.KeyPress, code, Qt.NoModifier, text, True)
        QGuiApplication.sendEvent(receiver, ev)

    @pyqtSlot(QQuickItem, QVariant)
    def onKeyReleased(self, receiver, txt):
        code, text = self._getTextAndCode(txt)
        logger.debug("key released {}, {}".format(code, text))
        ev = QKeyEvent(QKeyEvent.KeyRelease, code, Qt.NoModifier, text, False)
        QGuiApplication.sendEvent(receiver, ev)

    def _getTextAndCode(self, txt):
        if type(txt) == int:
            code = Qt.Key(txt)  # get keycode, e.g. backspace
            text = ""  # text doesn't matter for special key codes
        else:
            code = Qt.Key_A  # it looks like it doesn't matter which code is assigned if it is not a special key
            text = txt  # important is the character

        return (code, text)
