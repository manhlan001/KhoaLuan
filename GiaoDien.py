from PyQt6 import QtCore, QtGui, QtWidgets
import re
import sys
import Assembly
import data
from dict import line_edit_dict, conditon_dict, parse_labels, replace_memory, replace_memory_byte
import Create_memory
from encoder import Encoder
from decoder import Decoder

class RunCode(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal()
    def __init__(self):
        super().__init__()
        self._running = False
    def start_run_code(self):
        self._running = True
        while self._running:
            self.progress.emit()
            for _ in range(500000):
                pass
        self.finished.emit()
    def stop_run_code(self):
        self._running = False

class CustomCheckBoxDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.data(QtCore.Qt.ItemDataRole.CheckStateRole) is not None:
            self.drawBackground(painter, option, index)
            self.drawCircle(painter, option, index)
        else:
            super().paint(painter, option, index)
    def drawBackground(self, painter, option, index):
        painter.save()
        painter.fillRect(option.rect, QtGui.QColor('#DDDDDD'))
        painter.restore()
    def drawCircle(self, painter, option, index):
        checked = index.data(QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked
        rect = option.rect
        size = min(rect.width(), rect.height()) // 2
        circle_rect = QtCore.QRect(
            rect.left() + (rect.width() - size) // 2,
            rect.top() + (rect.height() - size) // 2,
            size,
            size
        )
        painter.save()
        if checked:
            painter.setBrush(QtGui.QColor('red'))
        else:
            painter.setBrush(QtGui.QColor('#DDDDDD'))
        painter.setPen(QtGui.QPen(QtGui.QColor('#DDDDDD'), 1))
        painter.drawEllipse(circle_rect)
        painter.restore()
    def editorEvent(self, event, model, option, index):
        if event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            if index.flags() & QtCore.Qt.ItemFlag.ItemIsEnabled and index.flags() & QtCore.Qt.ItemFlag.ItemIsUserCheckable:
                current_value = index.data(QtCore.Qt.ItemDataRole.CheckStateRole)
                new_value = QtCore.Qt.CheckState.Checked if current_value == QtCore.Qt.CheckState.Unchecked else QtCore.Qt.CheckState.Unchecked
                model.setData(index, new_value, QtCore.Qt.ItemDataRole.CheckStateRole)
                return True
        return super().editorEvent(event, model, option, index)
    
class CustomDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None, input_value=0, highlight_column=0):
        super().__init__(parent)
        self.input = input_value
        self.highlight_column = highlight_column

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if self.input == 0 and self.highlight_column == 0 and index.column() == 0:
            option.backgroundBrush = QtGui.QBrush(QtGui.QColor("#DDDDDD"))
        if self.input == 0 and self.highlight_column == 1 and (index.column() == 1 or index.column() == 2):
            option.backgroundBrush = QtGui.QBrush(QtGui.QColor("#F0F8FF"))

class CustomTableView(QtWidgets.QTableView):
    def __init__(self, parent=None, input_value=0):
        super().__init__(parent)
        self.setShowGrid(False)
        self.input = input_value
        self.delegate = CustomDelegate(self, input_value)
        self.setItemDelegate(self.delegate)

    def setHighlightColumn(self, column):
        self.delegate.highlight_column = column
        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self.viewport())
        painter.setPen(QtGui.QColor(QtCore.Qt.GlobalColor.darkGray))
        column_count = self.model().columnCount()
        if self.input == 1:
            column = self.delegate.highlight_column
            x = self.columnViewportPosition(column) + self.columnWidth(column)
            painter.drawLine(x, 0, x, self.viewport().height())
        else:
            for column in range(column_count - 1):
                x = self.columnViewportPosition(column) + self.columnWidth(column)
                painter.drawLine(x, 0, x, self.viewport().height())

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1080, 720)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.scrollArea = QtWidgets.QScrollArea(parent=self.centralwidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1060, 700))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(parent=self.scrollAreaWidgetContents)
        font = QtGui.QFont()
        font.setPointSize(24)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.tabWidget = QtWidgets.QTabWidget(parent=self.scrollAreaWidgetContents)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.tabWidget.setFont(font)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_1 = QtWidgets.QWidget()
        self.tab_1.setObjectName("tab_1")
        self.CompileButton = QtWidgets.QPushButton(parent=self.tab_1)
        self.CompileButton.setGeometry(QtCore.QRect(270, 10, 111, 51))
        self.CompileButton.setObjectName("CompileButton")
        self.QuitButton = QtWidgets.QPushButton(parent=self.tab_1)
        self.QuitButton.setGeometry(QtCore.QRect(270, 190, 111, 51))
        self.QuitButton.setObjectName("QuitButton")
        self.StepButton = QtWidgets.QPushButton(parent=self.tab_1)
        self.StepButton.setGeometry(QtCore.QRect(270, 130, 111, 51))
        self.StepButton.setObjectName("StepButton")
        self.ImportButton = QtWidgets.QPushButton(parent=self.tab_1)
        self.ImportButton.setGeometry(QtCore.QRect(140, 10, 111, 51))
        self.ImportButton.setObjectName("ImportButton")
        self.ExportButton = QtWidgets.QPushButton(parent=self.tab_1)
        self.ExportButton.setGeometry(QtCore.QRect(10, 10, 111, 51))
        self.ExportButton.setObjectName("ExportButton")
        self.RunButton = QtWidgets.QPushButton(parent=self.tab_1)
        self.RunButton.setGeometry(QtCore.QRect(270, 70, 111, 51))
        self.RunButton.setObjectName("RunButton")
        self.stackedCodeWidget = QtWidgets.QStackedWidget(parent=self.tab_1)
        self.stackedCodeWidget.setGeometry(QtCore.QRect(400, 0, 631, 601))
        self.stackedCodeWidget.setObjectName("stackedCodeWidget")
        self.pageCode_1 = QtWidgets.QWidget()
        self.pageCode_1.setObjectName("pageCode_1")
        self.CodeEditText = QtWidgets.QTextEdit(parent=self.pageCode_1)
        self.CodeEditText.setGeometry(QtCore.QRect(10, 20, 611, 571))
        self.CodeEditText.setObjectName("CodeEditText")
        self.stackedCodeWidget.addWidget(self.pageCode_1)
        self.pageCode_2 = QtWidgets.QWidget()
        self.pageCode_2.setObjectName("pageCode_2")
        self.CodeView = CustomTableView(parent=self.pageCode_2)
        self.CodeView.setGeometry(QtCore.QRect(10, 20, 611, 571))
        self.CodeView.setObjectName("CodeView")
        self.CodeView.verticalHeader().setVisible(False)
        self.CodeView.horizontalHeader().setVisible(False)
        self.stackedCodeWidget.addWidget(self.pageCode_2)
        
        self.CompileButton.clicked.connect(self.show_code_view)
        self.RunButton.clicked.connect(self.RunCode)
        self.QuitButton.clicked.connect(self.Quit)
        self.StepButton.clicked.connect(self.check_next_line)
        self.ImportButton.clicked.connect(self.import_file)
        self.ExportButton.clicked.connect(self.export)
        
        self.formLayoutWidget = QtWidgets.QWidget(parent=self.tab_1)
        self.formLayoutWidget.setGeometry(QtCore.QRect(10, 80, 201, 511))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.Layout_registers = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.Layout_registers.setContentsMargins(10, 10, 10, 0)
        self.Layout_registers.setObjectName("Layout_registers")
        self.r0_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r0_Label.setObjectName("r0_Label")
        self.Layout_registers.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r0_Label)
        self.r1_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r1_Label.setObjectName("r1_Label")
        self.Layout_registers.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r1_Label)
        self.r1_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r1_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r1_LineEdit.setObjectName("r1_LineEdit")
        self.Layout_registers.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r1_LineEdit)
        self.r2_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r2_Label.setObjectName("r2_Label")
        self.Layout_registers.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r2_Label)
        self.r2_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r2_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r2_LineEdit.setObjectName("r2_LineEdit")
        self.Layout_registers.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r2_LineEdit)
        self.r3_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r3_Label.setObjectName("r3_Label")
        self.Layout_registers.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r3_Label)
        self.r3_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r3_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r3_LineEdit.setObjectName("r3_LineEdit")
        self.Layout_registers.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r3_LineEdit)
        self.r4_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r4_Label.setObjectName("r4_Label")
        self.Layout_registers.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r4_Label)
        self.r4_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r4_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r4_LineEdit.setObjectName("r4_LineEdit")
        self.Layout_registers.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r4_LineEdit)
        self.r5_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r5_Label.setObjectName("r5_Label")
        self.Layout_registers.setWidget(5, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r5_Label)
        self.r5_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r5_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r5_LineEdit.setObjectName("r5_LineEdit")
        self.Layout_registers.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r5_LineEdit)
        self.r6_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r6_Label.setObjectName("r6_Label")
        self.Layout_registers.setWidget(6, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r6_Label)
        self.r6_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r6_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r6_LineEdit.setObjectName("r6_LineEdit")
        self.Layout_registers.setWidget(6, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r6_LineEdit)
        self.r7_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r7_Label.setObjectName("r7_Label")
        self.Layout_registers.setWidget(7, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r7_Label)
        self.r7_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r7_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r7_LineEdit.setObjectName("r7_LineEdit")
        self.Layout_registers.setWidget(7, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r7_LineEdit)
        self.r8_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r8_Label.setObjectName("r8_Label")
        self.Layout_registers.setWidget(8, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r8_Label)
        self.r8_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r8_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r8_LineEdit.setObjectName("r8_LineEdit")
        self.Layout_registers.setWidget(8, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r8_LineEdit)
        self.r9_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r9_Label.setObjectName("r9_Label")
        self.Layout_registers.setWidget(9, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r9_Label)
        self.r9_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r9_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r9_LineEdit.setObjectName("r9_LineEdit")
        self.Layout_registers.setWidget(9, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r9_LineEdit)
        self.r10_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r10_Label.setObjectName("r10_Label")
        self.Layout_registers.setWidget(10, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r10_Label)
        self.r10_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r10_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r10_LineEdit.setObjectName("r10_LineEdit")
        self.Layout_registers.setWidget(10, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r10_LineEdit)
        self.r11_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r11_Label.setObjectName("r11_Label")
        self.Layout_registers.setWidget(11, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r11_Label)
        self.r11_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r11_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r11_LineEdit.setObjectName("r11_LineEdit")
        self.Layout_registers.setWidget(11, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r11_LineEdit)
        self.r12_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.r12_Label.setObjectName("r12_Label")
        self.Layout_registers.setWidget(12, QtWidgets.QFormLayout.ItemRole.LabelRole, self.r12_Label)
        self.r12_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r12_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r12_LineEdit.setObjectName("r12_LineEdit")
        self.Layout_registers.setWidget(12, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r12_LineEdit)
        self.sp_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.sp_Label.setObjectName("sp_Label")
        self.Layout_registers.setWidget(13, QtWidgets.QFormLayout.ItemRole.LabelRole, self.sp_Label)
        self.sp_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.sp_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.sp_LineEdit.setObjectName("sp_LineEdit")
        self.Layout_registers.setWidget(13, QtWidgets.QFormLayout.ItemRole.FieldRole, self.sp_LineEdit)
        self.lr_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.lr_Label.setObjectName("lr_Label")
        self.Layout_registers.setWidget(14, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lr_Label)
        self.lr_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.lr_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lr_LineEdit.setObjectName("lr_LineEdit")
        self.Layout_registers.setWidget(14, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lr_LineEdit)
        self.pc_Label = QtWidgets.QLabel(parent=self.formLayoutWidget)
        self.pc_Label.setObjectName("pc_Label")
        self.Layout_registers.setWidget(15, QtWidgets.QFormLayout.ItemRole.LabelRole, self.pc_Label)
        self.pc_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.pc_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.pc_LineEdit.setObjectName("pc_LineEdit")
        self.Layout_registers.setWidget(15, QtWidgets.QFormLayout.ItemRole.FieldRole, self.pc_LineEdit)
        self.r0_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget)
        self.r0_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.r0_LineEdit.setObjectName("r0_LineEdit")
        self.Layout_registers.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.r0_LineEdit)
        
        line_edit_dict["r0"] = self.r0_LineEdit
        line_edit_dict["r1"] = self.r1_LineEdit
        line_edit_dict["r2"] = self.r2_LineEdit
        line_edit_dict["r3"] = self.r3_LineEdit
        line_edit_dict["r4"] = self.r4_LineEdit
        line_edit_dict["r5"] = self.r5_LineEdit
        line_edit_dict["r6"] = self.r6_LineEdit
        line_edit_dict["r7"] = self.r7_LineEdit
        line_edit_dict["r8"] = self.r8_LineEdit
        line_edit_dict["r9"] = self.r9_LineEdit
        line_edit_dict["r10"] = self.r10_LineEdit
        line_edit_dict["r11"] = self.r11_LineEdit
        line_edit_dict["r12"] = self.r12_LineEdit
        line_edit_dict["lr"] = self.lr_LineEdit
        line_edit_dict["sp"] = self.sp_LineEdit
        line_edit_dict["pc"] = self.pc_LineEdit

        self.formLayoutWidget_2 = QtWidgets.QWidget(parent=self.tab_1)
        self.formLayoutWidget_2.setGeometry(QtCore.QRect(240, 300, 160, 138))
        self.formLayoutWidget_2.setObjectName("formLayoutWidget_2")
        self.Layout_condition = QtWidgets.QFormLayout(self.formLayoutWidget_2)
        self.Layout_condition.setContentsMargins(10, 10, 10, 10)
        self.Layout_condition.setObjectName("Layout_condition")
        self.n_Label = QtWidgets.QLabel(parent=self.formLayoutWidget_2)
        self.n_Label.setObjectName("n_Label")
        self.Layout_condition.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.n_Label)
        self.n_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget_2)
        self.n_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.n_LineEdit.setObjectName("n_LineEdit")
        self.Layout_condition.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.n_LineEdit)
        self.z_Label = QtWidgets.QLabel(parent=self.formLayoutWidget_2)
        self.z_Label.setObjectName("z_Label")
        self.Layout_condition.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.z_Label)
        self.z_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget_2)
        self.z_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.z_LineEdit.setObjectName("z_LineEdit")
        self.Layout_condition.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.z_LineEdit)
        self.c_Label = QtWidgets.QLabel(parent=self.formLayoutWidget_2)
        self.c_Label.setObjectName("c_Label")
        self.Layout_condition.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.c_Label)
        self.c_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget_2)
        self.c_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.c_LineEdit.setObjectName("c_LineEdit")
        self.Layout_condition.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.c_LineEdit)
        self.v_Label = QtWidgets.QLabel(parent=self.formLayoutWidget_2)
        self.v_Label.setObjectName("v_Label")
        self.Layout_condition.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.v_Label)
        self.v_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget_2)
        self.v_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.v_LineEdit.setObjectName("v_LineEdit")
        self.Layout_condition.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.v_LineEdit)
        
        conditon_dict["n"] = self.n_LineEdit
        conditon_dict["z"] = self.z_LineEdit
        conditon_dict["c"] = self.c_LineEdit
        conditon_dict["v"] = self.v_LineEdit
        
        self.formLayoutWidget_4 = QtWidgets.QWidget(parent=self.tab_1)
        self.formLayoutWidget_4.setGeometry(QtCore.QRect(240, 470, 161, 80))
        self.formLayoutWidget_4.setObjectName("formLayoutWidget_4")
        self.formLayout_2 = QtWidgets.QFormLayout(self.formLayoutWidget_4)
        self.formLayout_2.setContentsMargins(0, 0, 0, 0)
        self.formLayout_2.setObjectName("formLayout_2")
        self.cpsr_Label = QtWidgets.QLabel(parent=self.formLayoutWidget_4)
        self.cpsr_Label.setObjectName("cpsr_Label")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.cpsr_Label)
        self.cpsr_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget_4)
        self.cpsr_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.cpsr_LineEdit.setObjectName("cpsr_LineEdit")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.cpsr_LineEdit)
        self.spsr_Label = QtWidgets.QLabel(parent=self.formLayoutWidget_4)
        self.spsr_Label.setObjectName("spsr_Label")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.spsr_Label)
        self.spsr_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget_4)
        self.spsr_LineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.spsr_LineEdit.setObjectName("spsr_LineEdit")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.spsr_LineEdit)
        
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor('white'))  # Thiết lập màu nền trắng
        
        self.tabWidget.addTab(self.tab_1, "")
        self.tab_memory = QtWidgets.QWidget()
        self.tab_memory.setObjectName("tab_memory")
        self.groupBox = QtWidgets.QGroupBox(parent=self.tab_memory)
        self.groupBox.setGeometry(QtCore.QRect(940, 0, 91, 591))
        self.groupBox.setObjectName("groupBox")
        self.label_size_memory = QtWidgets.QLabel(parent=self.groupBox)
        self.label_size_memory.setGeometry(QtCore.QRect(0, 30, 81, 41))
        self.label_size_memory.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.label_size_memory.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignTop)
        self.label_size_memory.setObjectName("label_size_memory")
        self.label_memory_words_per_row = QtWidgets.QLabel(parent=self.groupBox)
        self.label_memory_words_per_row.setGeometry(QtCore.QRect(0, 140, 81, 61))
        self.label_memory_words_per_row.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.label_memory_words_per_row.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignTop)
        self.label_memory_words_per_row.setObjectName("label_memory_words_per_row")
        self.comboBox_memory_words_per_row = QtWidgets.QComboBox(parent=self.groupBox)
        self.comboBox_memory_words_per_row.setGeometry(QtCore.QRect(10, 210, 71, 22))
        self.comboBox_memory_words_per_row.setObjectName("comboBox_memory_words_per_row")
        self.comboBox_memory_words_per_row.addItem("")
        self.comboBox_memory_words_per_row.addItem("")
        self.comboBox_memory_words_per_row.addItem("")
        self.comboBox_memory_words_per_row.addItem("")
        self.comboBox_memory_words_per_row.setPalette(palette)
        self.comboBox_size_memory = QtWidgets.QComboBox(parent=self.groupBox)
        self.comboBox_size_memory.setGeometry(QtCore.QRect(10, 80, 71, 25))
        self.comboBox_size_memory.setObjectName("comboBox_size_memory")
        self.comboBox_size_memory.addItem("")
        self.comboBox_size_memory.addItem("")
        self.comboBox_size_memory.setPalette(palette)
        self.formLayoutWidget_5 = QtWidgets.QWidget(parent=self.tab_memory)
        self.formLayoutWidget_5.setGeometry(QtCore.QRect(10, 10, 251, 29))
        self.formLayoutWidget_5.setObjectName("formLayoutWidget_5")
        self.formLayout_4 = QtWidgets.QFormLayout(self.formLayoutWidget_5)
        self.formLayout_4.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignTop)
        self.formLayout_4.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignTop)
        self.formLayout_4.setContentsMargins(0, 0, 0, 0)
        self.formLayout_4.setObjectName("formLayout_4")
        self.Address_search_LineEdit = QtWidgets.QLineEdit(parent=self.formLayoutWidget_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Address_search_LineEdit.sizePolicy().hasHeightForWidth())
        self.Address_search_LineEdit.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.Address_search_LineEdit.setFont(font)
        self.Address_search_LineEdit.setObjectName("Address_search_LineEdit")
        self.formLayout_4.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.Address_search_LineEdit)
        self.GotoAddr = QtWidgets.QPushButton(parent=self.formLayoutWidget_5)
        self.GotoAddr.setObjectName("GotoAddr")
        self.formLayout_4.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.GotoAddr)
        self.Addrr_Mem_View = CustomTableView(parent=self.tab_memory, input_value=1)
        self.Addrr_Mem_View.setGeometry(QtCore.QRect(10, 50, 921, 541))
        self.Addrr_Mem_View.setObjectName("Addrr_Mem_View")
        self.Addrr_Mem_View.verticalHeader().setVisible(False)
        self.Addrr_Mem_View.horizontalHeader().setVisible(False)
        self.Addrr_Mem_View.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.tabWidget.addTab(self.tab_memory, "")
        self.gridLayout.addWidget(self.tabWidget, 1, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout_2.addWidget(self.scrollArea, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        
        self.thread = QtCore.QThread()
        self.worker = RunCode()
        self.worker.moveToThread(self.thread)
        self.worker.progress.connect(self.Check)
        self.worker.finished.connect(self.thread.quit)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        self.model_code = QtGui.QStandardItemModel(0, 3)
        self.CodeView.setModel(self.model_code)
        self.CodeView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.model_code = self.Add_header_model_code(self.model_code)
        
        self.model = QtGui.QStandardItemModel(0, 7)
        self.model = self.Add_header_model_mem(self.model)
        
        self.model_2 = QtGui.QStandardItemModel(0, 7)
        self.model_2 = self.Add_header_model_mem(self.model_2)
        
        self.model_4 = QtGui.QStandardItemModel(0, 7)
        self.model_4 = self.Add_header_model_mem(self.model_4)
        
        self.model_8 = QtGui.QStandardItemModel(0, 7)
        self.model_8 = self.Add_header_model_mem(self.model_8)
        
        self.model_byte = QtGui.QStandardItemModel(0, 7)
        self.model_byte = self.Add_header_model_mem(self.model_byte)
        
        self.model_2_byte = QtGui.QStandardItemModel(0, 7)
        self.model_2_byte = self.Add_header_model_mem(self.model_2_byte)
        
        self.model_4_byte = QtGui.QStandardItemModel(0, 7)
        self.model_4_byte = self.Add_header_model_mem(self.model_4_byte)
        
        self.model_8_byte = QtGui.QStandardItemModel(0, 7)
        self.model_8_byte = self.Add_header_model_mem(self.model_8_byte)
    
        self.current_index = 0
        self.current_index_x2 = 0
        self.current_index_x4 = 0
        self.current_index_x8 = 0
        self.current_index_byte = 0
        self.current_index_x2_byte = 0
        self.current_index_x4_byte = 0
        self.current_index_x8_byte = 0
        self.total_items = 1073741823
        self.items_per_batch = 100
        
        self.load_mem_x1()
        self.load_mem_x2()
        self.load_mem_x4()
        self.load_mem_x8()
        self.load_mem_x1_byte()
        self.load_mem_x2_byte()
        self.load_mem_x4_byte()
        self.load_mem_x8_byte()
        self.check_mem_per_row_option()
        
        delegate = CustomCheckBoxDelegate(self.CodeView)
        self.CodeView.setItemDelegateForColumn(0, delegate)
        
        self.GotoAddr.clicked.connect(self.search_memory)
        self.comboBox_memory_words_per_row.currentIndexChanged.connect(self.check_mem_per_row_option)
        self.comboBox_size_memory.currentIndexChanged.connect(self.check_mem_per_row_option)
    
    def Add_header_model_code(self, model_code):
        label_bkpt = QtGui.QStandardItem()
        label_bkpt.setCheckState(QtCore.Qt.CheckState.Checked)
        label_bkpt.setData(QtCore.Qt.CheckState.Checked, QtCore.Qt.ItemDataRole.CheckStateRole)
        label_bkpt.setCheckable(False)
        label_bkpt.setFlags(label_bkpt.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_address_code = QtGui.QStandardItem('Address')
        label_address_code.setFlags(label_address_code.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_address_code.setBackground(QtGui.QColor("#F0F8FF"))
        label_address_code.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label_opcode = QtGui.QStandardItem('Opcode')
        label_opcode.setFlags(label_opcode.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_opcode.setBackground(QtGui.QColor("#F0F8FF"))
        label_opcode.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label_assembly = QtGui.QStandardItem('Assembly')
        label_assembly.setFlags(label_assembly.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_assembly.setBackground(QtGui.QColor("#F0F8FF"))
        label_assembly.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        model_code.appendRow([label_bkpt, label_address_code, label_opcode, label_assembly])
        self.CodeView.setColumnWidth(0, 25)
        self.CodeView.setColumnWidth(1, 80)
        self.CodeView.setColumnWidth(2, 80)
        self.CodeView.setColumnWidth(3, 380)
        return model_code
    def Add_header_model_mem(self, model):
        self.Addrr_Mem_View.setSpan(0, 1, 1, 8)
        label_address = QtGui.QStandardItem('Address')
        label_address.setFlags(label_address.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_address.setBackground(QtGui.QColor("#F0F8FF"))
        label_memory = QtGui.QStandardItem('Memory')
        label_memory.setFlags(label_memory.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_memory.setBackground(QtGui.QColor("#F0F8FF"))
        label_space_1 = QtGui.QStandardItem(" ")
        label_space_1.setFlags(label_space_1.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_space_1.setBackground(QtGui.QColor("#F0F8FF"))
        label_space_2 = QtGui.QStandardItem(" ")
        label_space_2.setFlags(label_space_2.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_space_2.setBackground(QtGui.QColor("#F0F8FF"))
        label_space_3 = QtGui.QStandardItem(" ")
        label_space_3.setFlags(label_space_3.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_space_3.setBackground(QtGui.QColor("#F0F8FF"))
        label_space_4 = QtGui.QStandardItem(" ")
        label_space_4.setFlags(label_space_4.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_space_4.setBackground(QtGui.QColor("#F0F8FF"))
        label_space_5 = QtGui.QStandardItem(" ")
        label_space_5.setFlags(label_space_5.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_space_5.setBackground(QtGui.QColor("#F0F8FF"))
        label_space_6 = QtGui.QStandardItem(" ")
        label_space_6.setFlags(label_space_6.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_space_6.setBackground(QtGui.QColor("#F0F8FF"))
        label_space_7 = QtGui.QStandardItem(" ")
        label_space_7.setFlags(label_space_7.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        label_space_7.setBackground(QtGui.QColor("#F0F8FF"))
        model.appendRow([label_address, label_memory, label_space_1, label_space_2, label_space_3, label_space_4, label_space_5, label_space_6, label_space_7])
        return model
    
    def check_mem_per_row_option(self):
        if self.comboBox_size_memory.currentIndex() == 0:
            if self.comboBox_memory_words_per_row.currentIndex() == 0:
                self.Addrr_Mem_View.setModel(self.model)
                self.Addrr_Mem_View.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            if self.comboBox_memory_words_per_row.currentIndex() == 1:
                self.Addrr_Mem_View.setModel(self.model_2)
                self.Addrr_Mem_View.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            if self.comboBox_memory_words_per_row.currentIndex() == 2:
                self.Addrr_Mem_View.setModel(self.model_4)
                self.Addrr_Mem_View.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            if self.comboBox_memory_words_per_row.currentIndex() == 3:
                self.Addrr_Mem_View.setModel(self.model_8)
                self.Addrr_Mem_View.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        if self.comboBox_size_memory.currentIndex() == 1:
            if self.comboBox_memory_words_per_row.currentIndex() == 0:
                self.Addrr_Mem_View.setModel(self.model_byte)
                self.Addrr_Mem_View.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            if self.comboBox_memory_words_per_row.currentIndex() == 1:
                self.Addrr_Mem_View.setModel(self.model_2_byte)
                self.Addrr_Mem_View.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            if self.comboBox_memory_words_per_row.currentIndex() == 2:
                self.Addrr_Mem_View.setModel(self.model_4_byte)
                self.Addrr_Mem_View.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            if self.comboBox_memory_words_per_row.currentIndex() == 3:
                self.Addrr_Mem_View.setModel(self.model_8_byte)
                self.Addrr_Mem_View.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
    def load_mem_x1(self):
        for i in range(self.current_index, min(self.current_index + self.items_per_batch * 8, self.total_items)):
            addr = QtGui.QStandardItem(format(i * 4, '08x'))
            addr.setFlags(addr.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            addr.setBackground(QtGui.QColor("#F0F8FF"))
            mem_1 = QtGui.QStandardItem('aaaaaaaa')
            mem_1.setFlags(mem_1.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.model.appendRow([addr, mem_1])
        self.current_index += self.items_per_batch * 8
    def load_mem_x1_byte(self):
        for i in range(self.current_index_byte, min(self.current_index_byte + self.items_per_batch * 8, self.total_items)):
            addr = QtGui.QStandardItem(format(i * 4, '08x'))
            addr.setFlags(addr.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            addr.setBackground(QtGui.QColor("#F0F8FF"))
            mem_1 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_1.setFlags(mem_1.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.model_byte.appendRow([addr, mem_1])
        self.current_index_byte += self.items_per_batch * 8
    def load_mem_x2(self):
        for i in range(self.current_index_x2, min(self.current_index_x2 + self.items_per_batch * 4, self.total_items)):
            addr = QtGui.QStandardItem(format(i * 8, '08x'))
            addr.setFlags(addr.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            addr.setBackground(QtGui.QColor("#F0F8FF"))
            mem_1 = QtGui.QStandardItem('aaaaaaaa')
            mem_1.setFlags(mem_1.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_2 = QtGui.QStandardItem('aaaaaaaa')
            mem_2.setFlags(mem_2.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.model_2.appendRow([addr, mem_1, mem_2])
        self.current_index_x2 += self.items_per_batch * 4
    def load_mem_x2_byte(self):
        for i in range(self.current_index_x2_byte, min(self.current_index_x2_byte + self.items_per_batch * 4, self.total_items)):
            addr = QtGui.QStandardItem(format(i * 8, '08x'))
            addr.setFlags(addr.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            addr.setBackground(QtGui.QColor("#F0F8FF"))
            mem_1 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_1.setFlags(mem_1.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_2 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_2.setFlags(mem_2.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.model_2_byte.appendRow([addr, mem_1, mem_2])
        self.current_index_x2_byte += self.items_per_batch * 4
    def load_mem_x4(self):
        for i in range(self.current_index_x4, min(self.current_index_x4 + self.items_per_batch * 2, self.total_items)):
            addr = QtGui.QStandardItem(format(i * 16, '08x'))
            addr.setFlags(addr.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            addr.setBackground(QtGui.QColor("#F0F8FF"))
            mem_1 = QtGui.QStandardItem('aaaaaaaa')
            mem_1.setFlags(mem_1.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_2 = QtGui.QStandardItem('aaaaaaaa')
            mem_2.setFlags(mem_2.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_3 = QtGui.QStandardItem('aaaaaaaa')
            mem_3.setFlags(mem_3.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_4 = QtGui.QStandardItem('aaaaaaaa')
            mem_4.setFlags(mem_4.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.model_4.appendRow([addr, mem_1, mem_2, mem_3, mem_4])
        self.current_index_x4 += self.items_per_batch * 2
    def load_mem_x4_byte(self):
        for i in range(self.current_index_x4_byte, min(self.current_index_x4_byte + self.items_per_batch * 2, self.total_items)):
            addr = QtGui.QStandardItem(format(i * 16, '08x'))
            addr.setFlags(addr.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            addr.setBackground(QtGui.QColor("#F0F8FF"))
            mem_1 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_1.setFlags(mem_1.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_2 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_2.setFlags(mem_2.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_3 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_3.setFlags(mem_3.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_4 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_4.setFlags(mem_4.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.model_4_byte.appendRow([addr, mem_1, mem_2, mem_3, mem_4])
        self.current_index_x4_byte += self.items_per_batch * 2
    def load_mem_x8(self):
        for i in range(self.current_index_x8, min(self.current_index_x8 + self.items_per_batch, self.total_items)):
            addr = QtGui.QStandardItem(format(i * 32, '08x'))
            addr.setFlags(addr.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            addr.setBackground(QtGui.QColor("#F0F8FF"))
            mem_1 = QtGui.QStandardItem('aaaaaaaa')
            mem_1.setFlags(mem_1.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_2 = QtGui.QStandardItem('aaaaaaaa')
            mem_2.setFlags(mem_2.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_3 = QtGui.QStandardItem('aaaaaaaa')
            mem_3.setFlags(mem_3.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_4 = QtGui.QStandardItem('aaaaaaaa')
            mem_4.setFlags(mem_4.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_5 = QtGui.QStandardItem('aaaaaaaa')
            mem_5.setFlags(mem_5.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_6 = QtGui.QStandardItem('aaaaaaaa')
            mem_6.setFlags(mem_6.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_7 = QtGui.QStandardItem('aaaaaaaa')
            mem_7.setFlags(mem_7.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_8 = QtGui.QStandardItem('aaaaaaaa')
            mem_8.setFlags(mem_8.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.model_8.appendRow([addr, mem_1, mem_2, mem_3, mem_4, mem_5, mem_6, mem_7, mem_8])
        self.current_index_x8 += self.items_per_batch
    def load_mem_x8_byte(self):
        for i in range(self.current_index_x8_byte, min(self.current_index_x8_byte + self.items_per_batch, self.total_items)):
            addr = QtGui.QStandardItem(format(i * 32, '08x'))
            addr.setFlags(addr.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            addr.setBackground(QtGui.QColor("#F0F8FF"))
            mem_1 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_1.setFlags(mem_1.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_2 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_2.setFlags(mem_2.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_3 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_3.setFlags(mem_3.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_4 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_4.setFlags(mem_4.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_5 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_5.setFlags(mem_5.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_6 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_6.setFlags(mem_6.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_7 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_7.setFlags(mem_7.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            mem_8 = QtGui.QStandardItem('aa' + " " + 'aa' + " " + 'aa' + " " + 'aa')
            mem_8.setFlags(mem_8.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.model_8_byte.appendRow([addr, mem_1, mem_2, mem_3, mem_4, mem_5, mem_6, mem_7, mem_8])
        self.current_index_x8_byte += self.items_per_batch
    def on_scroll(self, value):
        max_scroll = self.Addrr_Mem_View.verticalScrollBar().maximum()
        if value >= max_scroll and self.current_index < self.total_items:
            self.load_mem_x1()
            self.load_mem_x2()
            self.load_mem_x4()
            self.load_mem_x8()
            self.load_mem_x1_byte()
            self.load_mem_x2_byte()
            self.load_mem_x4_byte()
            self.load_mem_x8_byte()
    def search_memory(self):
        self.reset_search_memory(self.model)
        self.reset_search_memory(self.model_2)
        self.reset_search_memory(self.model_4)
        self.reset_search_memory(self.model_8)
        self.reset_search_memory(self.model_byte)
        self.reset_search_memory(self.model_2_byte)
        self.reset_search_memory(self.model_4_byte)
        self.reset_search_memory(self.model_8_byte)
        
        self.highlight_search_memory(self.model)
        self.highlight_search_memory(self.model_2)
        self.highlight_search_memory(self.model_4)
        self.highlight_search_memory(self.model_8)
        self.highlight_search_memory(self.model_byte)
        self.highlight_search_memory(self.model_2_byte)
        self.highlight_search_memory(self.model_4_byte)
        self.highlight_search_memory(self.model_8_byte)
    def reset_search_memory(self, model):
        for row in range(1, model.rowCount()):
            for col in range(1, model.columnCount()):
                if model.item(row, col):
                    model.item(row, col).setBackground(QtGui.QColor("white"))
    def highlight_search_memory(self, model):
        search_text = self.Address_search_LineEdit.text()
        if search_text:
            found = False
            search_value  = int(search_text, 16)
            while not found and self.current_index > 0:
                max_row = model.rowCount() - 1
                for row in range(1, model.rowCount()):
                    item_addr = model.item(row, 0)
                    if row != max_row:
                        item_addr_next = model.item(row + 1, 0)
                        addr_next = item_addr_next.text()
                    if item_addr:
                        addr = item_addr.text()
                    if search_value == int(addr, 16):
                        model.item(row, 1).setBackground(QtGui.QColor("yellow"))
                        self.Addrr_Mem_View.scrollTo(model.index(row, 1))
                        break
                    if addr_next and search_value > int(addr, 16) and search_value < int(addr_next, 16):
                        num = int((search_value - int(addr, 16)) / 4) + 1
                        model.item(row, num).setBackground(QtGui.QColor("yellow"))
                        self.Addrr_Mem_View.scrollTo(model.index(row, num))
                        break
                    if not addr_next and search_value > int(addr, 16):
                        num = int((search_value - int(addr, 16)) / 4) + 1
                        model.item(row, num).setBackground(QtGui.QColor("yellow"))
                        self.Addrr_Mem_View.scrollTo(model.index(row, num))
                        break
                if not found:
                    last_item_value = int(model.item(model.rowCount() - 1, 0).text(), 16)
                    if search_value < last_item_value:
                        break
                    self.load_mem_x1()
                    self.load_mem_x2()
                    self.load_mem_x4()
                    self.load_mem_x8()
                    self.load_mem_x1_byte()
                    self.load_mem_x2_byte()
                    self.load_mem_x4_byte()
                    self.load_mem_x8_byte()
                    
    def Check_Code_Assembly(self):
        text = self.CodeEditText.toPlainText()
        lines = text.split("\n")
        lines, data_lines = data.parse_data(lines)
        labels, lines_clean = parse_labels(lines)
        lines = [item for item in lines if item not in [" ", None]]
        lines = [' '.join(item.split()) for item in lines if item.strip()]
        lines_clean = [item for item in lines_clean if item not in [" ", None]]
        lines_clean = [' '.join(item.split()) for item in lines_clean if item.strip()]
        for index, line in enumerate(lines_clean, start=1):
            pc_binary = format(self.pc, '08x')
            self.address.append(pc_binary)
            self.pc += self.instruction_size
        self.data_labels, data_address, data_memory = data.process_data(data_lines, self.address)
        if data_address:
            self.address.extend(data_address)
        for index, line in enumerate(lines_clean, start=1):
            memory_line = Create_memory.check_memory(self, line, self.address, lines_clean, self.data_labels)
            if memory_line:
                int_memory_line = Decoder(memory_line)
                memory_line = format(int_memory_line, '08x')
                self.memory_current_line.append(memory_line)
            memory_line_branch = Create_memory.memory_branch(self, line, lines_clean, self.address, labels)    
            if memory_line_branch:
                int_memory_line_branch = Decoder(memory_line_branch)
                memory_line_branch = format(int_memory_line_branch, '08x')
                self.memory_current_line.append(memory_line_branch)
            memory_line_stacked = Create_memory.memory_stacked(self, line, lines_clean, self.address, labels)
            if memory_line_stacked:
                int_memory_line_stacked = Decoder(memory_line_stacked)
                memory_line_stacked = format(int_memory_line_stacked, '08x')
                self.memory_current_line.append(memory_line_stacked)
        if data_memory:
            self.memory_current_line.extend(data_memory)
        if len(self.address) != len(self.memory_current_line):
            QtWidgets.QMessageBox.critical(None, "Lỗi", "Lỗi memory")
            self.Quit()
            return True
        replace_memory(self.model, self.address, self.memory_current_line)
        replace_memory(self.model_2, self.address, self.memory_current_line)
        replace_memory(self.model_4, self.address, self.memory_current_line)
        replace_memory(self.model_8, self.address, self.memory_current_line)
        replace_memory_byte(self.model_byte, self.address, self.memory_current_line)
        replace_memory_byte(self.model_2_byte, self.address, self.memory_current_line)
        replace_memory_byte(self.model_4_byte, self.address, self.memory_current_line)
        replace_memory_byte(self.model_8_byte, self.address, self.memory_current_line)
        for i in range(len(lines_clean)):
            line = lines_clean[i]
            if line.strip():
                _, arguments, label, flag_B, _, _, _, _, flag_T = Assembly.check_assembly_line(self, lines_clean, line, self.address, self.memory_current_line, self.data_labels
                                                                                                    , self.model, self.model_2, self.model_4, self.model_8
                                                                                                    , self.model_byte, self.model_2_byte, self.model_4_byte, self.model_8_byte
                                                                                                    , self.stacked)
            if flag_B == 3:
                QtWidgets.QMessageBox.critical(None, "Lỗi", "Out of range to POP!")
                return True
            if label != None and (label not in labels) and (label not in lines_clean):
                QtWidgets.QMessageBox.critical(None, "Lỗi", "Không tìm thấy label: " + label + " ở dòng [" + line + "] trong chương trình")
                return True
            if flag_B or (arguments is None and flag_T):
                pass
            elif arguments is None:
                QtWidgets.QMessageBox.critical(None, "Lỗi", "Lệnh " + "[" + line + "]"+ " không hợp lệ")
                return True
        self.Quit()
        return False
        
    def show_code_edit(self):
        if self.thread.isRunning():
            self.worker.stop_run_code()
        self.stackedCodeWidget.setCurrentIndex(0)

    have_compile = False
    def show_code_view(self):
        text = self.CodeEditText.toPlainText()
        if not text:
            QtWidgets.QMessageBox.critical(None, "Lỗi", "Không có câu lệnh nào")
            return
        if self.have_compile:
            return
        eror = self.Check_Code_Assembly()
        if eror:
            return
        lines = text.split("\n")
        lines, data_lines = data.parse_data(lines)
        labels, lines_clean = parse_labels(lines)
        lines = [item for item in lines if item not in [" ", None]]
        lines = [' '.join(item.split()) for item in lines if item.strip()]
        lines_clean = [item for item in lines_clean if item not in [" ", None]]
        lines_clean = [' '.join(item.split()) for item in lines_clean if item.strip()]
        for index, line in enumerate(lines_clean, start=1):
            pc_binary = format(self.pc, '08x')
            self.address.append(pc_binary)
            self.pc += self.instruction_size
        self.data_labels, data_address, data_memory = data.process_data(data_lines, self.address)
        if data_address:
            self.address.extend(data_address)
        for index, line in enumerate(lines_clean, start=1):
            memory_line = Create_memory.check_memory(self, line, self.address, lines_clean, self.data_labels)
            if memory_line:
                int_memory_line = Decoder(memory_line)
                memory_line = format(int_memory_line, '08x')
                self.memory_current_line.append(memory_line)
            memory_line_branch = Create_memory.memory_branch(self, line, lines_clean, self.address, labels)
            if memory_line_branch:
                int_memory_line_branch = Decoder(memory_line_branch)
                memory_line_branch = format(int_memory_line_branch, '08x')
                self.memory_current_line.append(memory_line_branch)
            memory_line_stacked = Create_memory.memory_stacked(self, line, lines_clean, self.address, labels)
            if memory_line_stacked:
                int_memory_line_stacked = Decoder(memory_line_stacked)
                memory_line_stacked = format(int_memory_line_stacked, '08x')
                self.memory_current_line.append(memory_line_stacked)
        if data_memory:
            self.memory_current_line.extend(data_memory)
        replace_memory(self.model, self.address, self.memory_current_line)
        replace_memory(self.model_2, self.address, self.memory_current_line)
        replace_memory(self.model_4, self.address, self.memory_current_line)
        replace_memory(self.model_8, self.address, self.memory_current_line)
        replace_memory_byte(self.model_byte, self.address, self.memory_current_line)
        replace_memory_byte(self.model_2_byte, self.address, self.memory_current_line)
        replace_memory_byte(self.model_4_byte, self.address, self.memory_current_line)
        replace_memory_byte(self.model_8_byte, self.address, self.memory_current_line)
        mapping_addr_mem = {key: value for key, value in zip(self.address, self.memory_current_line)}
        temp = 0
        for i in range(len(lines)):
            line = lines[i]
            if not line.endswith(':'):
                addr_text = self.address[temp]
                temp += 1
                bkpt = QtGui.QStandardItem()
                bkpt.setCheckable(True)
                bkpt.setCheckState(QtCore.Qt.CheckState.Unchecked)
                bkpt.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                addr = QtGui.QStandardItem(addr_text)
                opcode = QtGui.QStandardItem(mapping_addr_mem.get(addr_text))
                assembly = QtGui.QStandardItem("    " + line)
            if line.endswith(':'):
                bkpt = QtGui.QStandardItem()
                bkpt.setCheckable(False)
                bkpt.setCheckState(QtCore.Qt.CheckState.Unchecked)
                bkpt.setFlags(bkpt.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                addr = QtGui.QStandardItem(" ")
                opcode = QtGui.QStandardItem(" ")
                assembly = QtGui.QStandardItem(line.upper())
            addr.setFlags(addr.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            addr.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            addr.setBackground(QtGui.QColor("#F0F8FF"))
            opcode.setFlags(opcode.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            opcode.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            opcode.setBackground(QtGui.QColor("#F0F8FF"))
            assembly.setFlags(assembly.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.model_code.appendRow([bkpt, addr, opcode, assembly])
        self.highlight_line("00000000")
        self.stackedCodeWidget.setCurrentIndex(1)
        self.have_compile = True
    
    bkpt = []
    def Code_BreakPoint(self):
        self.bkpt = []
        for row in range(1, self.model_code.rowCount()):
            item_checkbox = self.model_code.item(row, 0)
            item_line = self.model_code.item(row, 3)
            if item_checkbox.isCheckable() and item_checkbox.checkState() == QtCore.Qt.CheckState.Checked:
                line = item_line.text().strip()
                self.bkpt.append(line)
                    
    def reset_backgroud_register(self):
        self.r0_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r1_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r2_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r3_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r4_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r5_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r6_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r7_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r8_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r9_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r10_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r11_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r12_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.sp_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.lr_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.pc_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.n_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.z_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.c_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.v_LineEdit.setStyleSheet("background-color: white; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.CompileButton.setText(_translate("MainWindow", "Compile"))
        self.QuitButton.setText(_translate("MainWindow", "Quit"))
        self.StepButton.setText(_translate("MainWindow", "Step"))
        self.RunButton.setText(_translate("MainWindow", "Run"))
        self.r0_Label.setText(_translate("MainWindow", "r0"))
        self.r0_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r0_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r1_Label.setText(_translate("MainWindow", "r1"))
        self.r1_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r1_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r2_Label.setText(_translate("MainWindow", "r2"))
        self.r2_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r2_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r3_Label.setText(_translate("MainWindow", "r3"))
        self.r3_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r3_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r4_Label.setText(_translate("MainWindow", "r4"))
        self.r4_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r4_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r5_Label.setText(_translate("MainWindow", "r5"))
        self.r5_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r5_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r6_Label.setText(_translate("MainWindow", "r6"))
        self.r6_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r6_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r7_Label.setText(_translate("MainWindow", "r7"))
        self.r7_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r7_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r8_Label.setText(_translate("MainWindow", "r8"))
        self.r8_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r8_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r9_Label.setText(_translate("MainWindow", "r9"))
        self.r9_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r9_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r10_Label.setText(_translate("MainWindow", "r10"))
        self.r10_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r10_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r11_Label.setText(_translate("MainWindow", "r11"))
        self.r11_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r11_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.r12_Label.setText(_translate("MainWindow", "r12"))
        self.r12_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.r12_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.sp_Label.setText(_translate("MainWindow", "sp"))
        self.sp_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.sp_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.lr_Label.setText(_translate("MainWindow", "lr"))
        self.lr_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.lr_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.pc_Label.setText(_translate("MainWindow", "pc"))
        self.pc_LineEdit.setText(_translate("MainWindow", format(0, '08x')))
        self.pc_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.n_Label.setText(_translate("MainWindow", "N"))
        self.n_LineEdit.setText(_translate("MainWindow", "0"))
        self.n_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.z_Label.setText(_translate("MainWindow", "Z"))
        self.z_LineEdit.setText(_translate("MainWindow", "0"))
        self.z_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.c_Label.setText(_translate("MainWindow", "C"))
        self.c_LineEdit.setText(_translate("MainWindow", "0"))
        self.c_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.v_Label.setText(_translate("MainWindow", "V"))
        self.v_LineEdit.setText(_translate("MainWindow", "0"))
        self.v_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.cpsr_Label.setText(_translate("MainWindow", "cpsr"))
        self.cpsr_LineEdit.setText(_translate("MainWindow", "00000000"))
        self.cpsr_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.spsr_Label.setText(_translate("MainWindow", "spsr"))
        self.spsr_LineEdit.setText(_translate("MainWindow", "00000000"))
        self.spsr_LineEdit.setStyleSheet("font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        self.ImportButton.setText(_translate("MainWindow", "Import"))
        self.ExportButton.setText(_translate("MainWindow", "Export"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), _translate("MainWindow", "Editor"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_memory), _translate("MainWindow", "Memory"))
        self.Address_search_LineEdit.setText(_translate("MainWindow", "00000000"))
        self.GotoAddr.setText(_translate("MainWindow", "Go to Address"))
        self.groupBox.setTitle(_translate("MainWindow", "Option"))
        self.label_size_memory.setText(_translate("MainWindow", "Size\n"
"Memory:"))
        self.label_memory_words_per_row.setText(_translate("MainWindow", "Memory\n"
"words\n"
"per row:"))
        self.comboBox_memory_words_per_row.setItemText(0, _translate("MainWindow", "1"))
        self.comboBox_memory_words_per_row.setItemText(1, _translate("MainWindow", "2"))
        self.comboBox_memory_words_per_row.setItemText(2, _translate("MainWindow", "4"))
        self.comboBox_memory_words_per_row.setItemText(3, _translate("MainWindow", "8"))
        self.comboBox_memory_words_per_row.setCurrentIndex(3)
        self.comboBox_size_memory.setItemText(0, _translate("MainWindow", "Word"))
        self.comboBox_size_memory.setItemText(1, _translate("MainWindow", "Byte"))
        self.comboBox_size_memory.setCurrentIndex(0)
        self.label.setText(_translate("MainWindow", "ARMv7-M instruction set simulator"))
        
    pc = 0
    instruction_size = 4
    memory_current_line = []
    data_labels = []
    address = []
    current_line_index = 0
    row = []
    stacked = []
    def Check(self):
        global pc
        text = self.CodeEditText.toPlainText()
        lines = text.split("\n")
        lines, _ = data.parse_data(lines)
        labels, lines = parse_labels(lines)
        lines = [item for item in lines if item not in ["", None]]
        lines = [' '.join(item.split()) for item in lines if item.strip()]
        mapping = {key: value for key, value in zip(self.address, lines)}
        self.Code_BreakPoint()
        if self.current_line_index < len(lines):
            if len(self.address) == None or self.current_line_index >= len(self.address):
                return
            line = lines[self.current_line_index]
            if line.strip() in self.bkpt:
                if self.thread.isRunning():
                    self.worker.stop_run_code()
                return
            self.reset_backgroud_register()
            self.reset_highlight()
            pc_binary = self.address[self.current_line_index]
            self.pc_LineEdit.setText(pc_binary)
            if line.strip():
                reg, arguments, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T = Assembly.check_assembly_line(self, lines, line, self.address, self.memory_current_line, self.data_labels
                                                                                                      , self.model, self.model_2, self.model_4, self.model_8
                                                                                                      , self.model_byte, self.model_2_byte, self.model_4_byte, self.model_8_byte
                                                                                                      , self.stacked)
                self.current_line_index += 1
            if flag_B == 2:
                self.stacked = []
            if label in labels:
                position = lines.index(labels[label][0])
                self.current_line_index = position
            elif label in lines:
                position = lines.index(label)
                self.current_line_index = position
            if self.current_line_index >= len(lines):
                self.reset_highlight()
                for row in range(1, self.model_code.rowCount()):
                    item = self.model_code.item(row, 3)
                    if item != None:
                        item.setBackground(QtGui.QColor("#7fffd4"))
                if self.thread.isRunning():
                    self.worker.stop_run_code()
            else:
                pc_binary = self.address[self.current_line_index]
                self.highlight_line(pc_binary)
            if flag_T:
                pass
            elif arguments and len(reg) == len(arguments):
                for i in range(len(arguments)):
                    line_edit = line_edit_dict.get(reg[i])
                    result_int = int(arguments[i], 2)
                    result_str = format(result_int, '08x')
                    line_edit.setText(result_str)
                    line_edit.setStyleSheet("background-color: yellow; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
            n_edit = conditon_dict.get("n")
            z_edit = conditon_dict.get("z")
            c_edit = conditon_dict.get("c")
            v_edit = conditon_dict.get("v")
            n_edit.setText(flag_N)
            z_edit.setText(flag_Z)
            c_edit.setText(flag_C)
            v_edit.setText(flag_V)
            if flag_N == '1':
                n_edit.setStyleSheet("background-color: yellow; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
            if flag_Z == '1':
                z_edit.setStyleSheet("background-color: yellow; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
            if flag_C == '1':
                c_edit.setStyleSheet("background-color: yellow; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
            if flag_V == '1':
                v_edit.setStyleSheet("background-color: yellow; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
    def reset_highlight(self):
        for row in range(1, self.model_code.rowCount()):
            item = self.model_code.item(row, 3)
            if item != None:
                item.setBackground(QtGui.QColor("white"))
    def highlight_line(self, pc_binary):
        self.reset_highlight()
        search_value  = int(pc_binary, 16)
        for row in range(1, self.model_code.rowCount()):
            addr_line = self.model_code.item(row, 1)
            addr_line_text = addr_line.text()
            try:
                if search_value == int(addr_line_text, 16):
                    item = self.model_code.item(row, 3)
                    item.setBackground(QtGui.QColor("Yellow"))
            except ValueError:
                pass
            
    def check_next_line(self):
        if self.thread.isRunning():
            self.worker.stop_run_code()
        if self.stackedCodeWidget.currentIndex() == 0:
            QtWidgets.QMessageBox.critical(None, "Lỗi", "Vui lòng Compile code")
            self.Quit()
            return
        global current_line_index
        text = self.CodeEditText.toPlainText()
        lines = text.split("\n")
        lines, _ = data.parse_data(lines)
        labels, lines = parse_labels(lines)
        lines = [item for item in lines if item not in ["", None]]
        mapping = {key: value for key, value in zip(self.address, lines)}
        if self.current_line_index < len(lines):
            self.reset_backgroud_register()
            self.reset_highlight()
            pc_binary = self.address[self.current_line_index]
            self.pc_LineEdit.setText(pc_binary)
            current_line = lines[self.current_line_index]
            if current_line.strip():
                reg, arguments, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T = Assembly.check_assembly_line(self, lines, current_line, self.address, self.memory_current_line, self.data_labels
                                                                                                      , self.model, self.model_2, self.model_4, self.model_8
                                                                                                      , self.model_byte, self.model_2_byte, self.model_4_byte, self.model_8_byte
                                                                                                      , self.stacked)
                self.current_line_index += 1
            if flag_B == 2:
                self.stacked = []
            if label in labels:
                position = lines.index(labels[label][0])
                self.current_line_index = position
            elif label in lines:
                position = lines.index(label)
                self.current_line_index = position
            if self.current_line_index >= len(lines):
                self.reset_highlight()
                for row in range(1, self.model_code.rowCount()):
                    item = self.model_code.item(row, 3)
                    if item != None:
                        item.setBackground(QtGui.QColor("#7fffd4"))
            else:
                pc_binary = self.address[self.current_line_index]
                self.highlight_line(pc_binary)
            if flag_T:
                pass
            elif arguments and len(reg) == len(arguments):
                for i in range(len(arguments)):
                    line_edit = line_edit_dict.get(reg[i])
                    result_int = int(arguments[i], 2)
                    result_str = format(result_int, '08x')
                    line_edit.setText(result_str)
                    line_edit.setStyleSheet("background-color: yellow; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
            n_edit = conditon_dict.get("n")
            z_edit = conditon_dict.get("z")
            c_edit = conditon_dict.get("c")
            v_edit = conditon_dict.get("v")
            n_edit.setText(flag_N)
            z_edit.setText(flag_Z)
            c_edit.setText(flag_C)
            v_edit.setText(flag_V)
            if flag_N == '1':
                n_edit.setStyleSheet("background-color: yellow; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
            if flag_Z == '1':
                z_edit.setStyleSheet("background-color: yellow; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
            if flag_C == '1':
                c_edit.setStyleSheet("background-color: yellow; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
            if flag_V == '1':
                v_edit.setStyleSheet("background-color: yellow; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")

    def RunCode(self):
        thread_connected = False
        if self.stackedCodeWidget.currentIndex() == 0:
            QtWidgets.QMessageBox.critical(None, "Lỗi", "Vui lòng Compile code")
            self.Quit()
            return
        if not self.thread.isRunning():
            if not thread_connected:
                self.thread.started.connect(self.worker.start_run_code)
                thread_connected = True
            self.thread.start()
    
    def Quit(self):
        self.show_code_edit()
        self.address = []
        self.memory_current_line = []
        self.reset_backgroud_register()
        self.reset_highlight()
        self.stacked = []
        self.r0_LineEdit.setText(format(0, '08x'))
        self.r1_LineEdit.setText(format(0, '08x'))
        self.r2_LineEdit.setText(format(0, '08x'))
        self.r3_LineEdit.setText(format(0, '08x'))
        self.r4_LineEdit.setText(format(0, '08x'))
        self.r5_LineEdit.setText(format(0, '08x'))
        self.r6_LineEdit.setText(format(0, '08x'))
        self.r7_LineEdit.setText(format(0, '08x'))
        self.r8_LineEdit.setText(format(0, '08x'))
        self.r9_LineEdit.setText(format(0, '08x'))
        self.r10_LineEdit.setText(format(0, '08x'))
        self.r11_LineEdit.setText(format(0, '08x'))
        self.r12_LineEdit.setText(format(0, '08x'))
        self.sp_LineEdit.setText(format(0, '08x'))
        self.lr_LineEdit.setText(format(0, '08x'))
        self.pc_LineEdit.setText(format(0, '08x'))
        self.pc = 0
        self.current_line_index = 0
        self.n_LineEdit.setText("0")
        self.z_LineEdit.setText("0")
        self.c_LineEdit.setText("0")
        self.v_LineEdit.setText("0")
        self.current_index = 0
        self.current_index_x2 = 0
        self.current_index_x4 = 0
        self.current_index_x8 = 0
        self.current_index_byte = 0
        self.current_index_x2_byte = 0
        self.current_index_x4_byte = 0
        self.current_index_x8_byte = 0
        self.model.clear()
        self.model = self.Add_header_model_mem(self.model)
        self.model_2.clear()
        self.model_2 = self.Add_header_model_mem(self.model_2)
        self.model_4.clear()
        self.model_4 = self.Add_header_model_mem(self.model_4)
        self.model_8.clear()
        self.model_8 = self.Add_header_model_mem(self.model_8)
        self.model_byte.clear()
        self.model_byte = self.Add_header_model_mem(self.model_byte)
        self.model_2_byte.clear()
        self.model_2_byte = self.Add_header_model_mem(self.model_2_byte)
        self.model_4_byte.clear()
        self.model_4_byte = self.Add_header_model_mem(self.model_4_byte)
        self.model_8_byte.clear()
        self.model_8_byte = self.Add_header_model_mem(self.model_8_byte)
        self.load_mem_x1()
        self.load_mem_x2()
        self.load_mem_x4()
        self.load_mem_x8()
        self.load_mem_x1_byte()
        self.load_mem_x2_byte()
        self.load_mem_x4_byte()
        self.load_mem_x8_byte()
        self.Address_search_LineEdit.setText(format(0, '08x'))
        self.row = []
        self.bkpt = []
        self.have_compile = False
        self.model_code.clear()
        self.model_code = self.Add_header_model_code(self.model_code)
        
    def export(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Save File", "", "Text Files (*.txt);;Assembly Files (*.s)")
        if file_path:
            try:
                file_content = self.CodeEditText.toPlainText()
                with open(file_path, 'w') as file:
                    file.write(file_content)
                file_name = file_path.split('/')[-1]
                QtWidgets.QMessageBox.information(None, "Success", f"Đã lưu file {file_name} thành công ")
            except Exception as e:
                QtWidgets.QMessageBox.critical(None, "Error", f"Lưu file {file_path}\n{e} thất bại, vui lòng kiểm tra lại")
                self.Quit()
        
    def import_file(self):
        if self.stackedCodeWidget.currentIndex() == 1:
            QtWidgets.QMessageBox.critical(None, "Lỗi", "Vui lòng tắt Compile code")
            self.Quit()
            return
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Import File", "", "Assembly Files (*.s);;Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    file_content = file.read()
                self.CodeEditText.setPlainText(file_content)
                file_name = file_path.split('/')[-1]  
                QtWidgets.QMessageBox.information(None, "Success", f"Đã thêm file {file_name} thành công ")
            except Exception as e:
                QtWidgets.QMessageBox.critical(None, "Error", f"Mở file {file_name}\n{e} thất bại, vui lòng kiểm tra lại")
                self.Quit()
    
    def closeEvent(self, event):
        super().closeEvent(event)
        self.worker.stop_run_code()
        sys.exit(app.exec())
                    
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
