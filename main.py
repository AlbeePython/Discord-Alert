import sys
import requests
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QTextEdit, QPushButton, QLabel, 
                             QScrollArea, QFrame, QColorDialog)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor

# Чистый, современный темный стиль (Android Dark)
STYLE_SHEET = """
QWidget {
    background-color: #0E1015;
    color: #FFFFFF;
    font-family: 'Segoe UI', Roboto, sans-serif;
}

QFrame#left_panel {
    background-color: #161920;
    border-right: 1px solid #232730;
}

QLineEdit, QTextEdit {
    background-color: #1C2029;
    border: 1px solid #2D333F;
    border-radius: 8px;
    padding: 10px;
    color: #F0F0F0;
}

QLineEdit:focus { border: 1px solid #5865F2; }

QPushButton#main_btn {
    background-color: #5865F2;
    color: white;
    border-radius: 8px;
    font-weight: bold;
    font-size: 14px;
}
QPushButton#main_btn:hover { background-color: #4752C4; }

QFrame#embed_card {
    background-color: #1C2029;
    border-radius: 12px;
    border: 1px solid #2D333F;
}
"""

class EmbedBlock(QFrame):
    """Виджет отдельного Embed-блока"""
    def __init__(self, delete_callback):
        super().__init__()
        self.setObjectName("embed_card")
        self.delete_callback = delete_callback
        self.hex_color = "#5865F2" # Цвет по умолчанию
        
        # Основной лейаут карточки
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Шапка (Заголовок + Удалить)
        header = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Заголовок Embed")
        
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(30, 30)
        del_btn.setStyleSheet("background: #ED4245; border-radius: 6px; font-weight: bold;")
        del_btn.clicked.connect(lambda: self.delete_callback(self))
        
        header.addWidget(self.title_input)
        header.addWidget(del_btn)
        
        # Описание
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Описание блока...")
        self.desc_input.setMaximumHeight(60)
        
        # Индикатор и кнопка выбора цвета
        color_layout = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(20, 20)
        self.color_preview.setStyleSheet(f"background-color: {self.hex_color}; border-radius: 4px;")
        
        self.btn_color = QPushButton("ВЫБРАТЬ ЦВЕТ")
        self.btn_color.setStyleSheet("background: #2D333F; font-size: 10px; padding: 5px;")
        self.btn_color.clicked.connect(self.open_color_picker)
        
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.btn_color)
        color_layout.addStretch()

        layout.addLayout(header)
        layout.addWidget(self.desc_input)
        layout.addLayout(color_layout)

    def open_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.hex_color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.hex_color}; border-radius: 4px;")

class DiscordAlertPro(QWidget):
    def __init__(self):
        super().__init__()
        self.embed_list = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Discord Alert")
        self.resize(1000, 600)
        self.setStyleSheet(STYLE_SHEET)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- ЛЕВАЯ ПАНЕЛЬ (ВВОД) ---
        left_panel = QFrame()
        left_panel.setObjectName("left_panel")
        left_panel.setFixedWidth(360)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(30, 40, 30, 40)
        left_layout.setSpacing(20)

        left_layout.addWidget(QLabel("URL ВЕБХУКА"))
        self.url_in = QLineEdit()
        self.url_in.setPlaceholderText("https://discord.com...")
        left_layout.addWidget(self.url_in)

        left_layout.addWidget(QLabel("ВРЕМЯ (HH:MM)"))
        self.time_in = QLineEdit()
        self.time_in.setPlaceholderText("Пусто = сейчас")
        left_layout.addWidget(self.time_in)

        left_layout.addWidget(QLabel("ОСНОВНОЕ СООБЩЕНИЕ"))
        self.msg_in = QTextEdit()
        self.msg_in.setPlaceholderText("Текст над Embed-блоками...")
        left_layout.addWidget(self.msg_in)

        self.btn_send = QPushButton("ОТПРАВИТЬ")
        self.btn_send.setObjectName("main_btn")
        self.btn_send.setFixedHeight(50)
        self.btn_send.clicked.connect(self.send_to_discord)
        left_layout.addStretch()
        left_layout.addWidget(self.btn_send)

        # --- ПРАВАЯ ПАНЕЛЬ (EMBEDS) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(25, 25, 25, 25)

        right_layout.addWidget(QLabel("КОНСТРУКТОР EMBED БЛОКОВ"))
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_widget = QWidget()
        self.embed_container = QVBoxLayout(self.scroll_widget)
        self.embed_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_widget)
        right_layout.addWidget(self.scroll)

        self.btn_add = QPushButton("+ ДОБАВИТЬ EMBED")
        self.btn_add.setFixedHeight(45)
        self.btn_add.setStyleSheet("border: 2px dashed #2D333F; background: transparent; color: #5865F2;")
        self.btn_add.clicked.connect(self.add_embed_card)
        right_layout.addWidget(self.btn_add)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

    def add_embed_card(self):
        new_card = EmbedBlock(self.remove_embed_card)
        self.embed_list.append(new_card)
        self.embed_container.addWidget(new_card)
        
        # Плавное появление
        new_card.setMaximumHeight(0)
        anim = QPropertyAnimation(new_card, b"maximumHeight")
        anim.setDuration(300)
        anim.setStartValue(0)
        anim.setEndValue(220)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.start()
        self._anim = anim # Чтобы не удалился объект анимации

    def remove_embed_card(self, card):
        self.embed_list.remove(card)
        card.deleteLater()

    def send_to_discord(self):
        url = self.url_in.text().strip()
        if not url:
            self.url_in.setStyleSheet("border: 1px solid #ED4245;")
            return

        embeds = []
        for card in self.embed_list:
            title = card.title_input.text().strip()
            desc = card.desc_input.toPlainText().strip()
            # Конвертация цвета из HEX в Integer для Discord
            color_int = int(card.hex_color.lstrip('#'), 16)
            
            if title or desc:
                embeds.append({
                    "title": title,
                    "description": desc,
                    "color": color_int
                })

        payload = {
            "content": self.msg_in.toPlainText().strip() or None,
            "embeds": embeds if embeds else None
        }

        # Очистка от пустых значений
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            r = requests.post(url, json=payload)
            if r.status_code == 204:
                self.btn_send.setText("ОТПРАВЛЕНО!")
                self.btn_send.setStyleSheet("background-color: #43B581; color: white; border-radius: 8px;")
            else:
                self.btn_send.setText(f"ОШИБКА: {r.status_code}")
        except Exception as e:
            self.btn_send.setText("ОШИБКА СЕТИ")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiscordAlertPro()
    window.show()
    sys.exit(app.exec())
