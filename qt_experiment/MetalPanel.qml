import QtQuick
Item {
    id: root
    property url texture: "command_frame.png"
    implicitHeight: 64
    Rectangle {
        anchors.fill: parent; anchors.margins: 3; radius: 8
        gradient: Gradient {
            GradientStop { position: 0; color: "#2a2d2a" }
            GradientStop { position: 1; color: "#171a19" }
        }
        border.color: "#61543d"
    }
    BorderImage {
        anchors.fill: parent; source: root.texture
        border { left: 18; top: 18; right: 18; bottom: 18 }
        opacity: .86
    }
}
