import QtQuick
import QtQuick.Controls
Button {
    id: root
    property bool active: false
    implicitWidth: 94; implicitHeight: 94
    hoverEnabled: true
    padding: 0
    font.family: "Bahnschrift SemiCondensed"
    font.pixelSize: Math.max(22, Math.min(34, width * .35))
    font.bold: true
    contentItem: Text {
        text: root.text; font: root.font
        color: root.active ? "#ffe0a2" : "#c0b6a3"
        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
    }
    background: Item {
        Image {
            anchors.fill: parent
            source: "../assets/ui_wwii/premium_keycap.png"
            fillMode: Image.PreserveAspectFit
            opacity: root.down ? .73 : root.enabled ? 1 : .55
        }
        Rectangle {
            anchors.fill: parent; anchors.margins: 7; radius: 8
            color: root.hovered ? "#22efbd77" : "transparent"
            border.color: root.activeFocus ? "#f8bb65" : "transparent"
        }
    }
}
