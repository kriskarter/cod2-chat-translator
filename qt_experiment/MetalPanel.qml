import QtQuick
Item {
    id: root
    property url texture: "../assets/ui_wwii/premium_generic_frame.png"
    BorderImage {
        anchors.fill: parent
        source: root.texture
        border { left: 42; top: 42; right: 42; bottom: 42 }
    }
}
