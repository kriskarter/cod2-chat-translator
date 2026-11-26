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
        anchors.fill: parent; anchors.margins: 8
        source: root.artwork; fillMode: Image.PreserveAspectCrop; opacity: .72
    }
    Rectangle {
        anchors.fill: parent; anchors.margins: 8
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "#bb171a1b" }
            GradientStop { position: .68; color: "#70171919" }
            GradientStop { position: 1; color: "#99171919" }
        }
    }
    RowLayout {
        anchors.fill: parent; anchors.margins: root.compact ? 9 : 18
        spacing: root.compact ? 9 : 17
        KeycapButton {
            objectName: root.keyName.toLowerCase() + "Key"
            text: root.keyName; active: root.active; enabled: root.controlsEnabled
            Layout.preferredWidth: root.compact ? Math.min(74, Math.max(44, root.height - 24)) : 114
            Layout.preferredHeight: width
            onClicked: root.toggled()
        }
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            Item { Layout.fillHeight: true }
            Text { text: root.heading; color: "#fff0d1"; font.pixelSize: root.compact ? 14 : 22; font.bold: true; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight; Layout.fillWidth: true }
            Text { text: root.description; color: "#e8d4b3"; font.pixelSize: root.compact ? 11 : 13; elide: Text.ElideRight; Layout.fillWidth: true }
            RowLayout {
                Rectangle { width: 8; height: 8; radius: 4; color: root.active ? "#b0db84" : "#847c6d" }
                Text { text: !root.controlsEnabled ? (prototype.uiLanguage, prototype.trText("Не перенесён")) : root.active ? (prototype.uiLanguage, prototype.trText("Активен")) : (prototype.uiLanguage, prototype.trText("Выключен")); color: root.active ? "#b0db84" : "#bcb09a"; font.pixelSize: 12 }
            }
            Item { Layout.fillHeight: true }
        }
        TacticalSwitch { objectName: root.keyName.toLowerCase() + "Switch"; checked: root.active; enabled: root.controlsEnabled; Accessible.name: root.heading; onClicked: root.toggled() }
    }
}
