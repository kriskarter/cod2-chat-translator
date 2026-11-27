import QtQuick

Item {
    id: root
    property url texture: "reference_art/panel.webp"
    property url rim: "reference_art/frame.png"
    property bool artBorder: true
    implicitHeight: 64
    Rectangle { anchors.fill: parent; color: "#1c1b19"; radius: 6 }
    Image {
        anchors.fill: parent; anchors.margins: root.artBorder ? 4 : 1
        source: root.texture; fillMode: Image.Tile; opacity: root.artBorder ? 1 : .62
    }
    ArtFrame { anchors.fill: parent; source: root.rim; visible: root.artBorder }
}
