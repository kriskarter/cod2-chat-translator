import QtQuick
import QtQuick.Controls
TextField {
    id: root
    color: "#f5e7c9"
    placeholderTextColor: "#a79c88"
    selectionColor: "#88622d"
    selectedTextColor: "#fff1cd"
    font.pixelSize: 14
    padding: 9
    implicitHeight: 38
    background: Rectangle {
        Image { anchors.fill: parent; anchors.margins: 2; source: "reference_art/inset.webp"; fillMode: Image.Stretch; opacity: .65 }

        radius: 5
        color: root.enabled ? "#171b1c" : "#272a29"
        border.color: root.activeFocus ? "#d7a65d" : "#645b49"
    }
}
