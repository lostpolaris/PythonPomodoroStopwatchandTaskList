from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QApplication,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QLabel,
    QGridLayout,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QSizePolicy,
    QHeaderView,
)
from PySide6.QtCore import Qt, QElapsedTimer, QTimer, QSize, QSettings, Slot
from PySide6.QtGui import QAction, QIcon, QMovie

from datetime import timedelta
import os
import sys
import utils.constants as constants

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class TaskTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Task", "Task Time"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            print(self.removeRow(self.itemAt(event.pos()).row()))

    def mousePressEvent(self, event):
        pass


class TimerWidget(QWidget):
    def __init__(self, parent: QStackedWidget | None = None):
        super().__init__()

        self.parent = parent
        self.working = True
        self.pomo_time, self.break_time = (
            constants.DEFAULT_POMO_TIME,
            constants.DEFAULT_BREAK_TIME,
        )
        self.pomo_count, self.time, self.lap_time, self.gif_play_time = 0, 0, 0, 0
        self.lap = 0

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # pomo timers and controls
        pomodoro_layout = QHBoxLayout()
        self.pomo_count_widget = QLabel(
            "0", font=constants.HEADER_FONT, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.pomo_time_widget = QLabel(
            timedelta(seconds=constants.DEFAULT_POMO_TIME).__str__(),
            font=constants.HEADER_FONT,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        self.break_time_widget = QLabel(
            timedelta(seconds=constants.DEFAULT_BREAK_TIME).__str__(),
            font=constants.HEADER_FONT,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        pomodoro_layout.addWidget(self.pomo_count_widget)
        pomodoro_layout.addWidget(self.pomo_time_widget)
        pomodoro_layout.addWidget(self.break_time_widget)
        main_layout.addLayout(pomodoro_layout)

        # main timer
        self.main_time_widget = QLabel("0:00:00", font=constants.HEADER_FONT)
        main_layout.addWidget(
            self.main_time_widget, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # control buttons
        control_button_layout = QHBoxLayout()
        main_layout.addLayout(control_button_layout),
        button_confs = [("Start/Pause", True), ("Lap", False), ("Skip Break", False)]
        buttons = [
            QPushButton(title, checkable=checkable) for title, checkable in button_confs
        ]
        for button in buttons:
            control_button_layout.addWidget(button)

        # task entry
        task_entry_widget = QLineEdit(placeholderText="Add task...")
        main_layout.addWidget(task_entry_widget)

        # task table
        task_table_widget = TaskTable()
        task_table_widget.itemDoubleClicked.connect(
            lambda: print(task_table_widget.currentItem().text())
        )
        main_layout.addWidget(task_table_widget)

        self.timer = QTimer()
        self.timer.timeout.connect(
            lambda: self.show_time(buttons[0].isChecked(), self.lap, task_table_widget)
        )
        self.timer.start(1000)
        # events
        # task added
        task_entry_widget.returnPressed.connect(
            lambda: self.task_added(task_table_widget, task_entry_widget)
        )
        # lap to next task
        buttons[1].clicked.connect(lambda: self.lap_task(task_table_widget))
        # skip break
        buttons[2].clicked.connect(lambda: self.skip_break(task_table_widget))

        self.show()

    @Slot(bool, int, QTableWidget)
    def show_time(self, checked: bool, lap: int, task_table_widget: QTableWidget):
        # start global and lap timer, countdown pomo or break time
        if checked:
            self.pomo_time -= 1 if self.working else 0
            self.break_time -= 1 if not self.working else 0
            self.time += 1
            self.main_time_widget.setText(timedelta(seconds=self.time).__str__())
            self.pomo_time_widget.setText(timedelta(seconds=self.pomo_time).__str__())
            self.break_time_widget.setText(timedelta(seconds=self.break_time).__str__())
            if task_table_widget.rowCount():
                self.lap_time += 1
                lap_timer_label = task_table_widget.item(lap, 1)
                lap_timer_label.setText(timedelta(seconds=self.lap_time).__str__())
            if self.pomo_time == 0:
                self.working = False
                self.pomo_time = constants.DEFAULT_POMO_TIME
            if self.break_time == 0:
                self.pomo_count += 1
                self.working = True
                self.break_time = constants.DEFAULT_BREAK_TIME
            self.pomo_count_widget.setText(str(self.pomo_count))

        if self.parent.currentWidget() == self.parent.widget(1):
            self.gif_play_time += 1
            if self.gif_play_time == 6:
                self.gif_play_time = 0
                self.parent.removeWidget(self.parent.widget(1))

    @Slot(QTableWidget)
    def lap_task(self, task_table_widget: QTableWidget):
        # handle lap being larger than current task size
        # stop current lap timer, start new lap timer
        if self.lap + 1 < task_table_widget.rowCount():
            self.lap += 1
            self.lap_time = 0
        if self.lap < 30:
            label = QLabel()
            label.setGeometry(0, 0, self.parent.width(), self.parent.height())
            label.setScaledContents(True)
            video = QMovie(resource_path("media/giphy1.gif"))
            label.setMovie(video)
            video.setScaledSize(QSize(self.parent.width(), self.parent.height()))
            video.start()
            self.parent.addWidget(label)
            self.parent.setCurrentWidget(label)

    @Slot()
    def skip_break(self):
        # TODO: add nerd seal gif
        if not self.working:
            self.break_time = constants.DEFAULT_BREAK_TIME
            self.break_time_widget.setText(timedelta(seconds=self.break_time).__str__())
            self.pomo_count += 1
            self.working = True

    @Slot(QTableWidget, QLineEdit)
    def task_added(self, task_table_widget: QTableWidget, task_entry_widget: QLineEdit):
        print("task added", task_table_widget.rowCount())
        print(task_entry_widget.text())
        task_table_widget.insertRow(task_table_widget.rowCount())
        task_table_widget.setItem(
            task_table_widget.rowCount() - 1,
            0,
            QTableWidgetItem(task_entry_widget.text()),
        )
        task_table_widget.setItem(
            task_table_widget.rowCount() - 1, 1, QTableWidgetItem("0:00:00")
        )
        task_table_widget.item(task_table_widget.rowCount() - 1, 1).setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        task_entry_widget.setText("")

    @Slot()
    def table_double_clicked(self):
        print("table double clicked")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Polaris Pomo")
        self.setWindowIcon(QIcon(resource_path("media/logo.png")))

        stack_widget = QStackedWidget()
        timer_widget = TimerWidget(stack_widget)
        stack_widget.addWidget(timer_widget)
        self.setCentralWidget(stack_widget)

        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(
            lambda: QMessageBox.about(
                self,
                "Settings",
                "Settings are not yet implemented.",
            )
        )
        about_action = QAction("&About", self)
        about_action.triggered.connect(
            lambda: QMessageBox.about(
                self,
                "About PomoLapTimer",
                "PomoLapTimer is a simple timer for managing tasks and laps.\nDouble Right-Click on a task to delete it.",
            )
        )
        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addActions([settings_action, about_action])

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(Path(resource_path("utils/stylesheet.css")).read_text())
    w = MainWindow()
    sys.exit(app.exec())
