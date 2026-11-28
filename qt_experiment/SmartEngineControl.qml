import QtQuick
import QtQuick.Layouts
RowLayout {
    id: root
    property bool controlsEnabled: true
    property bool active
    signal toggled()
    Image { source: "reference_art/chip.png"; Layout.preferredWidth: root.width < 290 ? 26 : 42; Layout.preferredHeight: root.width < 290 ? 26 : 42; fillMode: Image.PreserveAspectFit }
    ColumnLayout {
        Layout.fillWidth: true; spacing: 2
        Text { text: "Smart Engine"; color: "#f5e7c9"; font.bold: true; font.pixelSize: root.width < 290 ? 13 : 18 }
        Text { text: (prototype.uiLanguage, prototype.trText("Адаптация игрового текста")); color: "#b7ad9b"; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
    }
    TacticalSwitch { checked: root.active; enabled: root.controlsEnabled; Accessible.name: "Smart Engine"; onClicked: root.toggled() }
}
