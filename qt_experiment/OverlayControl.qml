import QtQuick
import QtQuick.Layouts
RowLayout {
    id: root
    property bool controlsEnabled: true
    property bool active
    signal toggled()
    Image { source: "../assets/ui_wwii/nav_overlay.png"; Layout.preferredWidth: 24; Layout.preferredHeight: 24; fillMode: Image.PreserveAspectFit }
    ColumnLayout {
        Layout.fillWidth: true; spacing: 2
        Text { text: (prototype.uiLanguage, prototype.trText("Оверлей")); color: "#f5e7c9"; font.bold: true; font.pixelSize: 14 }
        Text { text: (prototype.uiLanguage, prototype.trText("Отображение перевода в игре")); color: "#b7ad9b"; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
    }
    TacticalSwitch { objectName: "overlaySwitch"; checked: root.active; enabled: root.controlsEnabled; Accessible.name: (prototype.uiLanguage, prototype.trText("Оверлей")); onClicked: root.toggled() }
}
