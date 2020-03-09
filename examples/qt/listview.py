import pathlib
from qtpy import QtWidgets

import happi
import happi.qt


class HappiDeviceExplorer(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super(HappiDeviceExplorer, self).__init__(parent=parent)

        self.filter_label = QtWidgets.QLabel("&Filter")
        self.filter_edit = QtWidgets.QLineEdit()
        self.filter_label.setBuddy(self.filter_edit)

        def set_filter(text):
            self.view.proxy_model.setFilterRegExp(text)

        self.filter_edit.textEdited.connect(set_filter)

        self.view = happi.qt.model.HappiDeviceListView(self)

        self.setLayout(QtWidgets.QGridLayout())
        self.layout().addWidget(self.filter_label, 1, 0)
        self.layout().addWidget(self.filter_edit, 1, 1)
        self.layout().addWidget(self.view, 3, 0, 1, 2)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    db_path = pathlib.Path(__file__).parent.parent / "db.json"
    cli = happi.Client(path=db_path)
    w = HappiDeviceExplorer()
    w.view.client = cli
    w.view.search(beamline="DEMO_BEAMLINE")
    w.show()

    app.exec_()