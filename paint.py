from PyQt6 import QtWidgets, QtGui, QtCore

class CustomCheckBoxDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.data(QtCore.Qt.ItemDataRole.CheckStateRole) is not None:
            self.drawSquare(painter, option, index)
        else:
            super().paint(painter, option, index)

    def drawSquare(self, painter, option, index):
        checked = index.data(QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked
        rect = option.rect
        
        size = min(rect.width(), rect.height()) // 2
        square_rect = QtCore.QRect(
            rect.left() + (rect.width() - size) // 2,
            rect.top() + (rect.height() - size) // 2,
            size,
            size
        )

        # Draw the background color if checked
        if checked:
            painter.fillRect(square_rect, QtGui.QColor('red'))

        # Draw the square border
        painter.setPen(QtGui.QPen(QtGui.QColor('black'), 2))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRect(square_rect)

        # Optionally, you can fill the square with a different color when unchecked
        if not checked:
            painter.setBrush(QtGui.QColor('white'))
            painter.drawRect(square_rect)

    def editorEvent(self, event, model, option, index):
        if event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            if index.flags() & QtCore.Qt.ItemFlag.ItemIsEnabled and index.flags() & QtCore.Qt.ItemFlag.ItemIsUserCheckable:
                current_value = index.data(QtCore.Qt.ItemDataRole.CheckStateRole)
                new_value = QtCore.Qt.CheckState.Checked if current_value == QtCore.Qt.CheckState.Unchecked else QtCore.Qt.CheckState.Unchecked
                model.setData(index, new_value, QtCore.Qt.ItemDataRole.CheckStateRole)
                return True
        return super().editorEvent(event, model, option, index)