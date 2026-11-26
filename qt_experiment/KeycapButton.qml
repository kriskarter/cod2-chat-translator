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
            source: "art/keycap" + (!root.enabled ? "_disabled" : root.down ? "_pressed" : root.activeFocus ? "_focused" : root.hovered || root.active ? "_hover" : "") + ".png"
            fillMode: Image.PreserveAspectFit
            opacity: root.down ? .73 : root.enabled ? 1 : .55
        }
    }
}
