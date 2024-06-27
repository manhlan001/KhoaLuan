from PyQt6.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QHeaderView
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt

class CustomTreeView(QTableView):
    def __init__(self):
        super().__init__()
        self.setShowGrid(False)  # Tắt lưới mặc định của QTreeView

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setPen(QColor(Qt.GlobalColor.darkGray))  # Màu của đường lưới

        # Vẽ các đường lưới dọc cho từng cột
        for column in range(self.model().columnCount()):
            x = self.columnViewportPosition(column) + self.columnWidth(column)
            painter.drawLine(x, 0, x, self.viewport().height())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Custom Grid Example")

        # Tạo QTreeView tùy chỉnh
        self.tree_view = CustomTreeView()

        # Thiết lập layout và hiển thị trong QMainWindow
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tree_view)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Điền dữ liệu mẫu vào QTreeView
        self.fill_data()

    def fill_data(self):
        # Code điền dữ liệu mẫu vào QTreeView ở đây
        pass

# Khởi tạo ứng dụng và chạy MainWindow
app = QApplication([])
window = MainWindow()
window.show()
app.exec()