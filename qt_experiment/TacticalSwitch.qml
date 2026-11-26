import QtQuick
import QtQuick.Controls
Switch {
    id: root
    implicitWidth: 52; implicitHeight: 26
    padding: 0
    indicator: Image {
        width: 52; height: 24
        anchors.centerIn: parent
        source: root.checked ? "../assets/ui_wwii/premium_switch_on.png" : "../assets/ui_wwii/premium_switch_off.png"
        fillMode: Image.PreserveAspectFit
        opacity: root.enabled ? 1 : .5
    }
    contentItem: Item {}
    background: Rectangle { color: "transparent"; radius: 5; border.color: root.activeFocus ? "#f8bb65" : "transparent" }
}
