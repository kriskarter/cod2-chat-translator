import QtQuick
import QtQuick.Controls

Button {
    id: root
    property bool active: false
    implicitWidth: 140; implicitHeight: 135
    padding: 0; hoverEnabled: true
    Accessible.name: text
    contentItem: Item {}
    background: Item {
        Image {
            anchors.fill: parent
            source: root.text === "F9" ? "reference_art/f9_cap.png" : "reference_art/f8_cap.png"
            fillMode: Image.PreserveAspectFit
            opacity: !root.enabled ? .44 : root.active || root.hovered ? 1 : .76
            scale: root.down ? .965 : 1
        }
        Rectangle { anchors.fill: parent; radius: 9; color: "transparent"; border.color: "#e3bd78"; visible: root.visualFocus }
    }
}
