import QtQuick
import QtQuick.Controls
Button {
    id: root
    property string surface: "metal"
    property bool selected: false
    property url glyph
    font.family: "Segoe UI"
    font.pixelSize: 13
    font.bold: true
    implicitHeight: 36
    implicitWidth: Math.max(74, buttonLabel.implicitWidth + (icon.visible ? 22 : 0) + 2 * padding + 6)
    padding: 8
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    contentItem: Item {
        Row {
            anchors.centerIn: parent
            spacing: 6
            Image {
                id: icon
                source: root.glyph
                visible: root.glyph.toString().length > 0
                width: visible ? 16 : 0; height: 16
                anchors.verticalCenter: parent.verticalCenter
                fillMode: Image.PreserveAspectFit
                opacity: root.enabled ? 1 : .45
            }
            Text {
                id: buttonLabel
                text: root.text; font: root.font
                color: root.enabled ? "#fff0d1" : "#a4977e"
                width: Math.min(implicitWidth, Math.max(0, root.availableWidth - (icon.visible ? 22 : 0)))
                elide: Text.ElideRight
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
    background: BorderImage {
        source: "../assets/ui_wwii/premium_" + root.surface + "_" +
                (root.surface === "nav" ? (root.down ? "pressed" : root.selected ? "active" : root.hovered ? "hover" : "normal") :
                 !root.enabled ? "disabled" : root.down ? "pressed" : root.hovered ? "hover" : "normal") + ".png"
        border { left: root.surface === "nav" ? 8 : 13; right: root.surface === "nav" ? 8 : 13; top: root.surface === "nav" ? 5 : 12; bottom: root.surface === "nav" ? 5 : 12 }
        Rectangle {
            anchors.fill: parent; anchors.margins: 2
            color: "transparent"; border.color: "#f8bb65"; radius: 3
            visible: root.activeFocus
        }
    }
}
