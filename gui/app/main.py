import sys

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import Qt, QObject, QAbstractListModel, QModelIndex, pyqtProperty, pyqtSignal, pyqtSlot


class SatellitesModel(QAbstractListModel):
    testPropertyChanged = pyqtSignal()
    SvIdRole = Qt.UserRole + 1
    CnoRole = Qt.UserRole + 2
    IsUsedRole = Qt.UserRole + 3

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._testProperty = "test data"
        self._satellites = [
            {"svid": "20", "cno": "23", "isUsed": False},
            {"svid": "17", "cno": "65", "isUsed": True},
            {"svid": "12", "cno": "55", "isUsed": True},
        ]

    @pyqtProperty(str, notify=testPropertyChanged)
    def testProperty(self):
        return self._testProperty

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == SatellitesModel.SvIdRole:
            return self._satellites[row]["svid"]
        if role == SatellitesModel.CnoRole:
            return self._satellites[row]["cno"]
        if role == SatellitesModel.IsUsedRole:
            return self._satellites[row]["isUsed"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._satellites)

    def roleNames(self):
        return {
            SatellitesModel.SvIdRole: b"svid",
            SatellitesModel.CnoRole: b"cno",
            SatellitesModel.IsUsedRole: b"isUsed",
        }

    @pyqtSlot(str, int)
    def addSatellite(self, svid, cno, isUsed):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._satellites.append({"svid": svid, "cno": cno, "isUsed": isUsed})
        self.endInsertRows()

    @pyqtSlot(int, str, int)
    def editSatellite(self, row, svid, cno, isUsed):
        ix = self.index(row, 0)
        self._satellites[row] = {"svid": svid, "cno": cno, "isUsed": isUsed}
        self.dataChanged.emit(ix, ix, self.roleNames())

    @pyqtSlot(int)
    def removeSatellite(self, row):
        self.beginRemoveColumns(QModelIndex(), row, row)
        del self._satellites[row]
        self.endRemoveRows()


app = QGuiApplication(sys.argv)
satellitesModel = SatellitesModel()
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("satellitesModel", satellitesModel)
engine.quit.connect(app.quit)
engine.load("main.qml")

sys.exit(app.exec())
