import QtQuick
import QtQuick.Controls
Dialog {
    id: root
    modal: true
    padding: 20
    palette.windowText: "#f5e7c9"
    palette.text: "#f5e7c9"
    background: BorderImage {
        source: "../assets/ui_wwii/premium_generic_frame.png"
        border { left: 42; right: 42; top: 42; bottom: 42 }
    }
}
