import QtQuick
import QtQuick.Layouts
MetalPanel {
    id: root
    property string keyName
    property string heading
    property string description
    property bool controlsEnabled: true
    property bool active
    property bool compact
    property url artwork
    signal toggled()
    clip: true
    Image {
        anchors.fill: parent; anchors.margins: 18
        source: root.artwork; fillMode: Image.PreserveAspectCrop; opacity: .57
    }
    Rectangle {
        anchors.fill: parent; anchors.margins: 18
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "#bb171a1b" }
            GradientStop { position: .68; color: "#70171919" }
            GradientStop { position: 1; color: "#99171919" }
        }
    }
    RowLayout {
        anchors.fill: parent; anchors.margins: root.compact ? 17 : 25
        spacing: root.compact ? 9 : 17
        KeycapButton {
            objectName: root.keyName.toLowerCase() + "Key"
            text: root.keyName; active: root.active; enabled: root.controlsEnabled
            Layout.preferredWidth: root.compact ? 78 : 108
            Layout.preferredHeight: width
            onClicked: root.toggled()
        }
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            Item { Layout.fillHeight: true }
            Text { text: root.heading; color: "#fff0d1"; font.pixelSize: root.compact ? 14 : 21; font.bold: true; elide: Text.ElideRight; Layout.fillWidth: true }
            Text { text: root.description; color: "#e8d4b3"; font.pixelSize: root.compact ? 11 : 13; elide: Text.ElideRight; Layout.fillWidth: true }
            RowLayout {
                Rectangle { width: 8; height: 8; radius: 4; color: root.active ? "#b0db84" : "#847c6d" }
                Text { text: !root.controlsEnabled ? "Не перенесён" : root.active ? "Активен" : "Выключен"; color: root.active ? "#b0db84" : "#bcb09a"; font.pixelSize: 12 }
            }
            Item { Layout.fillHeight: true }
        }
        TacticalSwitch { objectName: root.keyName.toLowerCase() + "Switch"; checked: root.active; enabled: root.controlsEnabled; Accessible.name: root.heading; onClicked: root.toggled() }
    }
}
