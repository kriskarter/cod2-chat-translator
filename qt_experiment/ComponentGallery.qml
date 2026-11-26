import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ApplicationWindow {
    id: window
    visible: true
    width: 1000; height: 650
    title: "Qt component gallery — development only"
    color: "#161818"
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 20; spacing: 12
        Text { text: "Компоненты: визуальная проверка"; color: "#f5e7c9"; font.bold: true; font.pixelSize: 24 }
        MetalPanel {
            Layout.fillWidth: true; Layout.preferredHeight: 110
            RowLayout {
                anchors.fill: parent; anchors.margins: 24
                MetalButton { text: "MetalButton"; Layout.fillWidth: true }
                AmberButton { text: "AmberButton"; Layout.fillWidth: true }
                NavigationTab { text: "NavigationTab"; selected: true; glyph: "icons/home.svg"; Layout.fillWidth: true }
                LanguageSelector { model: ["Русский", "Українська", "English"]; Layout.preferredWidth: 150 }
            }
        }
        RowLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            TranslationCard {
                keyName: "F8"; heading: "TranslationCard"; description: "KeycapButton · TacticalSwitch"
                artwork: "../assets/ui_premium/translation_card_source.jpg"; active: true
                Layout.fillWidth: true; Layout.fillHeight: true
            }
            MetalPanel {
                Layout.fillWidth: true; Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 22
                    ServerTable { Layout.fillWidth: true; Layout.fillHeight: true; rows: prototype.rows; selected: prototype.selected }
                    PlayerRoster { Layout.fillWidth: true; Layout.fillHeight: true; players: prototype.players }
                    FriendIndicator { count: 0 }
                }
            }
        }
        MetalPanel {
            Layout.fillWidth: true; Layout.preferredHeight: 75
            RowLayout {
                anchors.fill: parent; anchors.margins: 24
                OverlayControl { active: true; Layout.fillWidth: true }
                SmartEngineControl { active: false; Layout.fillWidth: true }
                SystemStatusPanel { statusText: "Gallery"; Layout.fillWidth: true }
                MetalButton { text: "MetalDialog"; onClicked: sample.open() }
            }
        }
    }
    MetalDialog {
        id: sample
        anchors.centerIn: parent
        width: 360
        title: "MetalDialog"
        standardButtons: Dialog.Close
        Text { text: "Отдельная проверка диалога"; color: "#f5e7c9" }
    }
    Component.onCompleted: sample.open()
}
