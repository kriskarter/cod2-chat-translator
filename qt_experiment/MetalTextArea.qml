import QtQuick
import QtQuick.Controls
TextArea {
    id: root
    color: "#f5e7c9"; placeholderTextColor: "#a79c88"
    selectionColor: "#88622d"; selectedTextColor: "#fff1cd"
    font.pixelSize: 14; padding: 10
    background: Rectangle {
        Image { anchors.fill: parent; anchors.margins: 2; source: "reference_art/field.webp"; fillMode: Image.Tile; opacity: .65 }

        color: "#171b1c"; radius: 5
        border.color: root.activeFocus ? "#d7a65d" : "#645b49"
    }
}
