from PyQt6.QtWidgets import (QLabel, QGridLayout,  QWidget, QFrame, QFileDialog, QCheckBox,
                             QSpinBox, QComboBox, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QButtonGroup)
from PyQt6.QtCore import Qt
import qasync
from qasync import asyncSlot, asyncClose, QApplication, QEventLoop
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot as Slot


from obi.commands import BeamSelectCommand, BeamType, ExternalCtrlCommand
from obi.transfer import TCPConnection
#from obi.config.scope import OBIScope, OBIBeam
from obi.config.meta import ScopeSettings, BeamSettings

class BeamButton(QPushButton):
    def __init__(self, name, beam: BeamSettings):
        self.name = name
        self.beam_type = beam.type
        super().__init__(name)

class BeamControl(QWidget):
    sigBeamTypeChanged = pyqtSignal(str)
    def __init__(self, conn, beams={}):
        super().__init__()
        self.conn = conn
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.beams = QButtonGroup()
        noBeam = BeamSettings(type=BeamType.NoBeam, pinout=None, mag_cal=None)
        beams.update({"All Off":noBeam})
        for beam_name, beam in beams.items():
            btn = BeamButton(beam_name, beam)
            btn.setCheckable(True)
            self.beams.addButton(btn)
            layout.addWidget(btn)
        self.beams.idClicked.connect(self.beam_select)

        self.ext = QPushButton("Lock External Control")
        self.ext.setCheckable(True)
        self.ext.clicked.connect(self.toggle_ext)
        # layout.addWidget(self.ext)
    
    def get_current_beam(self):
        b_id = self.beams.checkedId()
        btn = self.beams.button(b_id)
        if btn is not None:
            return btn.name
        else:
            return None

    @asyncSlot(int)
    async def beam_select(self, b_id):
        btn = self.beams.button(b_id)
        await self.conn.transfer(BeamSelectCommand(beam_type=btn.beam_type))
        self.sigBeamTypeChanged.emit(btn.name)

    @asyncSlot()
    async def toggle_ext(self):
        enable=self.ext.isChecked()
        if enable:
            self.ext.setText("Release External Control")
        else:
            self.ext.setText("Lock External Control")
        await self.conn.transfer(ExternalCtrlCommand(enable=enable))


if __name__ == "__main__":
    import sys
    import asyncio
    app = QApplication(sys.argv)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    conn = TCPConnection('localhost', 2224)
    
    scope_settings = ScopeSettings.from_toml_file()
    b = BeamControl(conn, scope_settings.beam_settings)
    b.show()

    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())
