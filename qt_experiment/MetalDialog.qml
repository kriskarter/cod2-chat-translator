import QtQuick
import QtQuick.Controls
Dialog {
    id: root
    modal: true
    width: 390
    padding: 20
    palette.windowText: "#f5e7c9"
    palette.text: "#f5e7c9"
    background: Item {
        Rectangle { anchors.fill: parent; anchors.margins: 5; color: "#20221f"; radius: 5 }
        ArtFrame { anchors.fill: parent }
    }
    palette.button: "#343730"
    palette.buttonText:"#f5e7c9"
}
