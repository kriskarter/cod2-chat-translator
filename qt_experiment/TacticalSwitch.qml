import QtQuick
import QtQuick.Controls
Switch {
    id: root
    implicitWidth: 66; implicitHeight: 30; padding: 0
    indicator: Rectangle {
        width: 62; height: 24
        anchors.centerIn: parent; radius: 12
        gradient: Gradient { GradientStop {position:0;color:root.checked?"#384e2d":"#373a34"} GradientStop {position:1;color:root.checked?"#192b19":"#1a1d1b"} }
        border.color: root.hovered ? "#c5b47e" : root.checked ? "#749650" : "#625d51"
        Image {anchors.fill:parent;anchors.margins:3;source:"metal_grain.png";fillMode:Image.Tile;opacity:.085}
        opacity: root.enabled ? 1 : .5
        Text {
            anchors.verticalCenter: parent.verticalCenter
            x: root.checked ? 7 : 24
            text: root.checked ? (prototype.uiLanguage, prototype.trText("Вкл")) : (prototype.uiLanguage, prototype.trText("Выкл"))
            font.pixelSize: 10; font.bold: true
            color: root.checked ? "#b8df87" : "#beb3a1"
        }
        Rectangle {
            x: root.checked ? parent.width - width - 4 : 4
            anchors.verticalCenter: parent.verticalCenter
            width: 15; height: 15; radius: 8
            gradient: Gradient { GradientStop {position:0;color:root.checked?"#d6eeaf":"#ccc7b7"} GradientStop {position:1;color:root.checked?"#7fa74d":"#77776a"} }
            border.color: root.checked ? "#d0eeb3" : "#b2ada0"
            Behavior on x { NumberAnimation { duration: 100 } }
        }
    }
    contentItem: Item {}
    background: Rectangle { color: "transparent"; radius: 5; border.color: root.activeFocus ? "#f8bb65" : "transparent" }
}
