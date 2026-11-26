import QtQuick
import QtQuick.Controls
Dialog {
    id: root
    modal: true
    padding: 20
    palette.windowText: "#f5e7c9"
    palette.text: "#f5e7c9"
    background: BorderImage {
        source: "command_frame.png"
        border { left: 18; right: 18; top: 18; bottom: 18 }
    }
}
