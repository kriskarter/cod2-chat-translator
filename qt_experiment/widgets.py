"""Qt Widgets/QPainter candidate. Run: python -m qt_experiment.widgets"""
from __future__ import annotations

import os
import sys

from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPen, QPixmap, QTextCharFormat, QTextDocument
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow,
                               QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from server_monitor import color_runs
from .common import ASSETS, PrototypeState, preview_state


class MetalPanel(QFrame):
    def __init__(self, image=None, parent=None):
        super().__init__(parent)
        self.image = QPixmap(str(ASSETS / image)) if image else QPixmap()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        box = self.rect().adjusted(1, 1, -2, -2)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor('#33302a'))
        g.setColorAt(.45, QColor('#191b1b'))
        g.setColorAt(1, QColor('#0b0d0d'))
        p.fillRect(box, QBrush(g))
        if not self.image.isNull():
            p.setOpacity(.47)
            p.drawPixmap(box, self.image, self.image.rect())
            p.setOpacity(1)
        p.setPen(QPen(QColor('#a58756'), 1))
        p.drawRoundedRect(box, 9, 9)
        p.setPen(QPen(QColor('#57452f'), 1))
        p.drawRoundedRect(box.adjusted(4, 4, -4, -4), 7, 7)
        p.end()


def label(text, size=12, color='#f3e7ce', bold=False):
    w = QLabel(text)
    w.setFont(QFont('Segoe UI', size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    w.setStyleSheet(f'color:{color}; background:transparent')
    return w


def button(text, callback, accent=False):
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setMinimumHeight(38)
    b.setStyleSheet('QPushButton{color:#f7e4b6;border:1px solid #af884e;border-radius:5px;'
                    'background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #87632d,stop:0.45 #46351e,stop:1 #201e1b);'
                    'padding:4px 13px;font-weight:600}'
                    'QPushButton:hover{background:#886237;border-color:#e8bd74}'
                    'QPushButton:pressed{background:#21180f;padding-top:6px}' if accent else
                    'QPushButton{color:#e8dec9;border:1px solid #806c50;border-radius:5px;'
                    'background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #44423d,stop:1 #1b1d1d);padding:4px 13px}'
                    'QPushButton:hover{background:#61543e;border-color:#d4ae70}'
                    'QPushButton:pressed{background:#181715;padding-top:6px}')
    b.clicked.connect(callback)
    return b


class Card(MetalPanel):
    def __init__(self, state, key, scene):
        super().__init__(scene)
        self.state, self.key = state, key
        self.setMinimumHeight(137)
        row = QHBoxLayout(self)
        row.setContentsMargins(9, 9, 9, 9)
        row.setSpacing(8)
        self.keycap = button(key.upper(), lambda: state.toggle(key), True)
        self.keycap.setFixedSize(72, 78)
        self.keycap.setStyleSheet(self.keycap.styleSheet() + 'QPushButton{font-size:31px;font-style:italic}')
        row.addWidget(self.keycap)
        content = QVBoxLayout()
        content.addWidget(label('Входящий перевод' if key == 'f8' else 'Исходящий перевод', 13, bold=True))
        content.addWidget(label('Чат → русский' if key == 'f8' else 'Русский → English', 10))
        content.addStretch()
        self.detail = label('', 10, '#ecc98d')
        content.addWidget(self.detail)
        row.addLayout(content, 1)
        self.toggle = button('', lambda: state.toggle(key))
        self.toggle.setFixedWidth(106)
        row.addWidget(self.toggle, alignment=Qt.AlignmentFlag.AlignTop)
        state.changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self.toggle.setText('✓  Активен' if getattr(self.state, self.key) else '○  Выключен')
        self.detail.setText('●  Активен' if getattr(self.state, self.key) else '○  Выключен')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.toggle.setVisible(self.width() >= 400)


class Monitor(MetalPanel):
    def __init__(self, state):
        super().__init__('premium_server.png')
        self.state = state
        self.setMinimumWidth(480)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        title = QHBoxLayout()
        title.addWidget(label('♙  Мониторинг серверов', 18, bold=True))
        title.addStretch()
        title.addWidget(label('Друзья в игре: 0', 10, '#a9dd86'))
        outer.addLayout(title)
        outer.addWidget(label('Сервер                         Карта              Игроки       Пинг       Статус', 10, '#b7ae9b'))
        self.servers = QVBoxLayout()
        self.servers.setSpacing(2)
        outer.addLayout(self.servers)
        outer.addWidget(label('Игроки на сервере', 11, '#ead6ac', True))
        self.players = QScrollArea()
        self.players.setWidgetResizable(True)
        self.players.setStyleSheet('QScrollArea{background:#151718;border:1px solid #554731} QScrollBar:vertical{background:#242522;width:9px}')
        outer.addWidget(self.players, 1)
        actions = QHBoxLayout()
        for title_, key in [('＋ Добавить сервер', 'add_server'), ('⟳ Обновить', 'refresh'), ('▶ Подключиться', 'connect')]:
            actions.addWidget(button(title_, lambda k=key: state.request(k), key == 'connect'))
        outer.addLayout(actions)
        state.rowsChanged.connect(self.refresh)
        state.changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        while self.servers.count():
            item = self.servers.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for row in self.state.rows:
            active = row['address'] == self.state.selected
            text = f"{'★' if active else '☆'}  {row['name'][:23]:23}  {row['map'][:13]:13}  {row['population']:7}  {row['ping']:7}  {row['state']}"
            b = button(text, lambda a=row['address']: self.state.select(a))
            b.setStyleSheet(b.styleSheet() + ('QPushButton{border-color:#e5b262;background:#594022}' if active else ''))
            self.servers.addWidget(b)
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 6, 8, 6)
        selected = next((r for r in self.state._rows.values() if r.address == self.state.selected), None)
        for raw, score, ping in (selected.players if selected else ()):
            parts = ''.join(f'<span style="color:{color}">{text}</span>' for text, color in color_runs(raw))
            layout.addWidget(label(f'{parts}                   {score if score is not None else "—"}          {ping if ping is not None else "—"} ms', 10))
        layout.addStretch()
        self.players.setWidget(panel)


class MainWindow(QMainWindow):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setWindowTitle('CoD2 Chat Translator — Qt Widgets comparison')
        self.resize(1366, 768)
        self.setMinimumSize(900, 620)
        self.setStyleSheet('QMainWindow,QWidget{background:#111313} QLabel{background:transparent}')
        center = QWidget()
        self.setCentralWidget(center)
        root = QVBoxLayout(center)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        hero = QLabel()
        hero.setFixedHeight(190)
        hero.setPixmap(QPixmap(str(ASSETS / 'premium_hero.png')))
        hero.setScaledContents(True)
        logo = QLabel(hero)
        logo.setPixmap(QPixmap(str(ASSETS / 'premium_logo.png')).scaledToHeight(125, Qt.TransformationMode.SmoothTransformation))
        logo.setStyleSheet('background:transparent')
        logo.setGeometry(350, 20, 550, 142)
        root.addWidget(hero)
        nav = QHBoxLayout()
        nav.setContentsMargins(17, 3, 17, 3)
        for title in ('⌂ Главная', '▤ Серверы', '⚙ Настройки', '▥ Логи / История', 'ⓘ О программе'):
            nav.addWidget(button(title, lambda t=title: state.request('nav:' + t)))
        nav.addStretch()
        root.addLayout(nav)
        body = QHBoxLayout()
        body.setContentsMargins(17, 12, 17, 8)
        body.setSpacing(14)
        cards = QVBoxLayout()
        cards.setSpacing(12)
        cards.addWidget(Card(state, 'f8', 'premium_hero.png'))
        cards.addWidget(Card(state, 'f9', 'premium_server.png'))
        body.addLayout(cards, 43)
        body.addWidget(Monitor(state), 57)
        root.addLayout(body, 1)
        rail = MetalPanel()
        rail.setFixedHeight(88)
        rail_layout = QHBoxLayout(rail)
        rail_layout.setContentsMargins(30, 8, 30, 8)
        self.rail_buttons = []
        for key, title in [('overlay', '◈  Оверлей'), ('smart', '▣  Smart Engine')]:
            b = button(title, lambda k=key: state.toggle(k))
            rail_layout.addWidget(b)
            self.rail_buttons.append((key, b))
        rail_layout.addWidget(label('✓  Статус системы: готова', 13, '#a9dd86', True))
        state.changed.connect(self.refresh)
        self.refresh()
        root.addWidget(rail)

    def refresh(self):
        for key, b in self.rail_buttons:
            b.setText(('●  ' if getattr(self.state, key) else '○  ') + ('Оверлей' if key == 'overlay' else 'Smart Engine'))


def main():
    app = QApplication(sys.argv)
    state = preview_state()
    state.action.connect(lambda name: print('Prototype action:', name, flush=True))
    window = MainWindow(state)
    if '--size' in sys.argv:
        width, height = map(int, sys.argv[sys.argv.index('--size') + 1].split('x'))
        window.resize(width, height)
    window.show()
    if '--screenshot' in sys.argv:
        app.processEvents()
        window.grab().save(sys.argv[sys.argv.index('--screenshot') + 1])
        return 0
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
