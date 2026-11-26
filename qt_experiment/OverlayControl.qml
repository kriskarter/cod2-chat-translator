import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
RowLayout {
    id: root
    property bool controlsEnabled: true
    property bool active
    signal configure()
    signal toggled()
    Image { source: "icons/hud.svg"; Layout.preferredWidth: 30; Layout.preferredHeight: 30; fillMode: Image.PreserveAspectFit }
    ColumnLayout {
        Layout.fillWidth: true; spacing: 2
        Text { text: (prototype.uiLanguage, prototype.trText("Оверлей")); color: "#f5e7c9"; font.bold: true; font.pixelSize: 14 }
        Text { text: (prototype.uiLanguage, prototype.trText("Отображение перевода в игре")); color: "#b7ad9b"; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
    }
    MetalButton { visible:prototype.translationAvailable; glyph:"icons/settings.svg";text:"";implicitWidth:30;implicitHeight:30;onClicked:root.configure();ToolTip.visible:hovered;ToolTip.text:(prototype.uiLanguage,prototype.trText("Настройки оверлея")) }
    TacticalSwitch { objectName: "overlaySwitch"; checked: root.active; enabled: root.controlsEnabled; Accessible.name: (prototype.uiLanguage, prototype.trText("Оверлей")); onClicked: root.toggled() }
}
