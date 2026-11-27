import QtQuick

MetalButton {
    id: root
    surface: "nav"
    font.bold: selected
    background: Item {
        BorderImage {
            anchors.fill: parent
            visible: root.selected || root.hovered || root.visualFocus
            opacity: root.selected ? 1 : .5
            source: "reference_art/nav_on.png"
            border { left: 7; right: 7; top: 7; bottom: 7 }
        }
        Rectangle { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; height: parent.height*.78; width: 1; color: "#655e50"; visible: !root.selected }
    }
}
