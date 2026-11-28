import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
RowLayout {
    id: root
    property bool controlsEnabled: true
    property bool active
    signal configure()
    signal toggled()
    Image { source: "reference_art/hud.png"; Layout.preferredWidth: root.width < 290 ? 26 : 42; Layout.preferredHeight: root.width < 290 ? 26 : 42; fillMode: Image.PreserveAspectFit }
    ColumnLayout {
        Layout.fillWidth: true; spacing: 2
        Text { text: (prototype.uiLanguage, prototype.trText("Оверлей")); color: "#f5e7c9"; font.bold: true; font.pixelSize: root.width < 290 ? 13 : 18 }
        Text { text: (prototype.uiLanguage, prototype.trText("Отображение перевода в игре")); color: "#b7ad9b"; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
    }
    MetalButton { visible:prototype.translationAvailable; glyph:"icons/settings.svg";text:"";sizeClass:"icon"; implicitWidth:30; Accessible.name:(prototype.uiLanguage,prototype.trText("Настройки оверлея"));onClicked:root.configure();hintText:(prototype.uiLanguage,prototype.trText("Настройки оверлея")) }
    TacticalSwitch { objectName: "overlaySwitch"; checked: root.active; attention:prototype.gamePrivilegeMismatch || prototype.startupElevationDenied; enabled: root.controlsEnabled; Accessible.name: (prototype.uiLanguage, prototype.trText("Оверлей")); onClicked: root.toggled() }
}
