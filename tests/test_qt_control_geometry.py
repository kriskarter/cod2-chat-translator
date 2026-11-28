"""Measure the painted caption and the nine-slice center in a real Qt scene."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
pytest.importorskip("PySide6")
from PySide6.QtCore import QPointF, QSizeF, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from qt_experiment.common import ROOT


def test_compact_and_wide_buttons_have_a_center_and_a_visible_caption():
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlApplicationEngine()
    engine.loadData(b"""
        import QtQuick
        Window {
            visible: true; width: 480; height: 110
            AmberButton { id: button; objectName: "sample"; x: 10; y: 10; text: "Connect" }
        }
    """, QUrl.fromLocalFile(str(ROOT / "qt_experiment/SizeFixture.qml")))
    window = engine.rootObjects()[0]
    button = window.findChild(QQuickItem, "sample")
    caption = button.findChild(QQuickItem, "button_caption")
    try:
        for width, height in ((68, 26), (140, 36), (392, 44)):
            button.setSize(QSizeF(width, height))
            QTest.qWait(25)
            background = button.property("background")
            # Native style insets can shrink a custom surface even when its control is tall.
            surface_origin = background.mapToItem(button, QPointF())
            assert abs(surface_origin.y()) <= 1
            assert abs(background.height() - height) <= 1
            assert background.height() - 2 * button.property("slice") >= 14
            pos = caption.mapToItem(button, QPointF(0, 0))
            assert 2 <= pos.y() and pos.y() + caption.height() <= height - 2
            assert abs(pos.y() + caption.height() / 2 - height / 2) <= 1
            assert 0 <= pos.x() and pos.x() + caption.width() <= width + 1
            assert not window.grabWindow().isNull()
    finally:
        window.close()
