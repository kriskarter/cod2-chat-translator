import QtQuick
import QtQuick.Controls

ToolTip {
    id: root
    objectName: "metalTooltip"
    delay: 400
    timeout: 8000
    padding: 8
    width: Math.min(420, Math.max(80, label.implicitWidth + leftPadding + rightPadding))
    font.pixelSize: 13
    contentItem: Text {
        id: label
        text: root.text
        textFormat: Text.PlainText
        color: "#f5e7c9"
        font: root.font
        wrapMode: Text.WrapAnywhere
    }
    background: Rectangle {
        color: "#202321"
        border.color: "#9b7948"
        radius: 4
    }
}
