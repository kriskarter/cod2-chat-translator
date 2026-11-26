import QtQuick
import QtQuick.Layouts
RowLayout {
    id: root
    property bool controlsEnabled: true
    property bool active
    signal toggled()
    Image { source: "icons/chip.svg"; Layout.preferredWidth: 30; Layout.preferredHeight: 30; fillMode: Image.PreserveAspectFit }
    ColumnLayout {
        Layout.fillWidth: true; spacing: 2
        Text { text: "Smart Engine"; color: "#f5e7c9"; font.bold: true; font.pixelSize: 14 }
        Text { text: (prototype.uiLanguage, prototype.trText("Адаптация игрового текста")); color: "#b7ad9b"; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
    }
    TacticalSwitch { checked: root.active; enabled: root.controlsEnabled; Accessible.name: "Smart Engine"; onClicked: root.toggled() }
}
