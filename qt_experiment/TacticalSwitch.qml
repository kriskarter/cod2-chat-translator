import QtQuick
import QtQuick.Controls

Switch {
    id: root
    implicitWidth: 68
    implicitHeight: 30
    padding: 0
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    indicator: Item {
        anchors.centerIn: parent
        width: Math.min(root.width, 66); height: 24
        opacity: root.enabled ? 1 : .45
        Rectangle {
            anchors.fill: parent; radius: 4
            color: "#131813"
            border.color: root.visualFocus ? "#f2c578" : root.hovered ? "#af9e7b" : "#675f4b"
        }
        Image {
            anchors.fill: parent; anchors.margins: 3
            source: root.checked ? "art/switch_face.png" : "art/switch_off.png"
        }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            x: root.checked ? 6 : 24
            width: parent.width - 30
            horizontalAlignment: Text.AlignHCenter
            text: (prototype.uiLanguage, prototype.trText(root.checked ? "Вкл" : "Выкл"))
            font.pixelSize: 10; font.bold: true
            color: root.checked ? "#d1e7ad" : "#ccc8ba"
        }
        Rectangle {
            x: root.checked ? parent.width - width - 4 : 4
            anchors.verticalCenter: parent.verticalCenter
            width: 16; height: 16; radius: 3
            gradient: Gradient {
                GradientStop { position: 0; color: "#998f75" }
                GradientStop { position: .38; color: "#696959" }
                GradientStop { position: 1; color: "#383b32" }
            }
            border.color: "#b0a388"
            Rectangle {
                anchors.centerIn: parent; width: 8; height: 3; radius: 1
                color: root.checked ? "#c4e89b" : "#42453c"
            }
            Behavior on x { NumberAnimation { duration: 100 } }
        }
    }
    contentItem: Item {}
    background: Item {}
}
