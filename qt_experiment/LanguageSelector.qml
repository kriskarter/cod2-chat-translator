import QtQuick
import QtQuick.Controls
ComboBox {
    id: root
    font.pixelSize: 13
    palette.text: "#f5e7c9"
    palette.base: "#242a2c"
    palette.window: "#242a2c"
    background: BorderImage {
        source: "../assets/ui_wwii/premium_metal_normal.png"
        border { left: 13; right: 13; top: 12; bottom: 12 }
    }
    indicator: Image {
        x: root.width - width - 5; anchors.verticalCenter: parent.verticalCenter
        width: 18; height: 18; source: "../assets/ui_wwii/premium_combo_arrow.png"
    }
}
