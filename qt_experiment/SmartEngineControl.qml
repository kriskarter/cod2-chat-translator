import QtQuick
import QtQuick.Layouts
RowLayout {
    id: root
    property bool controlsEnabled: true
    property bool active
    signal toggled()
    Text { text: "Smart Engine"; color: "#f5e7c9"; font.bold: true; font.pixelSize: 14; Layout.fillWidth: true }
    TacticalSwitch { checked: root.active; enabled: root.controlsEnabled; Accessible.name: "Smart Engine"; onClicked: root.toggled() }
}
