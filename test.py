from PyQt6 import QtWidgets
import sys

class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Popup Example")

        # Tạo nút để hiển thị pop-up message
        self.button = QtWidgets.QPushButton("Show Message", self)
        self.button.clicked.connect(self.show_popup)
        
        # Thiết lập bố cục
        self.setCentralWidget(self.button)

    def show_popup(self):
        """Hiển thị một pop-up message"""
        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowTitle("Message Box Example")
        message_box.setText("This is a pop-up message!")
        message_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel)

        # Hiển thị hộp thoại và lấy phản hồi từ người dùng
        response = message_box.exec()

        if response == QtWidgets.QMessageBox.StandardButton.Ok:
            print("User clicked OK")
        elif response == QtWidgets.QMessageBox.StandardButton.Cancel:
            print("User clicked Cancel")

# Khởi tạo ứng dụng PyQt6
app = QtWidgets.QApplication(sys.argv)
window = MyWindow()
window.show()
sys.exit(app.exec())
