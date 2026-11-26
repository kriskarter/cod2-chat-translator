import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    visible: true
    width: 1366; height: 768
    minimumWidth: 900; minimumHeight: 620
    title: "CoD2 Chat Translator — " + (prototype.demo ? "демонстрация" : "UDP Monitor · разработка")
    color: "#111313"
    property bool compact: width < 1100
    property color ink: "#f5e7c9"
    property int navIndex: 0
    MetalDialog {
        id: addDialog
        anchors.centerIn: parent
        title: "Добавить сервер (до закрытия)"
        standardButtons: Dialog.NoButton
        width: 390
        ColumnLayout {
            anchors.fill: parent
            TextField { id: addressField; placeholderText: "host:28960"; Layout.fillWidth: true }
            TextField { id: labelField; placeholderText: "Название"; Layout.fillWidth: true }
            Text { text: prototype.status; color: "#e4c291"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            RowLayout {
                MetalButton { text: "Отмена"; onClicked: addDialog.close() }
                AmberButton { text: "Добавить"; onClicked: if (prototype.addServer(addressField.text, labelField.text)) addDialog.close() }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(window.width / 7.4, window.height * .26)
            clip: true
            Rectangle { anchors.fill: parent; color: "#25251e" }
            Image {
                anchors.fill: parent
                source: "../assets/ui_premium/command_panorama.jpg"
                fillMode: Image.PreserveAspectFit
            }
            Image {
                anchors.centerIn: parent
                height: parent.height * .80; width: height * 3
                source: "../assets/ui_wwii/premium_logo.png"
                fillMode: Image.PreserveAspectFit
            }
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 2; color: "#a27c49" }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 44
            color: "#191b1a"; border.color: "#68573c"
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 17; anchors.rightMargin: 17; anchors.topMargin: 3; anchors.bottomMargin: 3; spacing: 6
                Repeater {
                    model: [
                        {name:"Главная", icon:"home", key:"home"},
                        {name:"Серверы", icon:"servers", key:"servers"},
                        {name:"Настройки", icon:"settings", key:"settings"},
                        {name:"История", icon:"history", key:"history"},
                        {name:"О программе", icon:"about", key:"about"}
                    ]
                    delegate: NavigationTab {
                        required property var modelData
                        required property int index
                        text: modelData.name
                        glyph: "icons/" + modelData.icon + ".svg"
                        selected: index === window.navIndex
                        enabled: index === 0 || prototype.demo
                        Layout.fillWidth: true; Layout.fillHeight: true
                        onClicked: {
                            // Only Home is implemented in this comparison entry point.
                            prototype.request("nav:" + modelData.key)
                        }
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            Layout.leftMargin: 17; Layout.rightMargin: 17; Layout.topMargin: 10; Layout.bottomMargin: 8
            spacing: 12
            ColumnLayout {
                Layout.fillWidth: true; Layout.fillHeight: true
                Layout.horizontalStretchFactor: 43
                spacing: 10
                TranslationCard {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    keyName: "F8"; heading: "Входящий перевод"; description: "Чат → русский"
                    active: prototype.f8; compact: window.compact; controlsEnabled: prototype.demo
                    artwork: "../assets/ui_premium/translation_card_source.jpg"
                    onToggled: prototype.toggle("f8")
                }
                TranslationCard {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    keyName: "F9"; heading: "Исходящий перевод"; description: "Русский → English"
                    active: prototype.f9; compact: window.compact; controlsEnabled: prototype.demo
                    artwork: "../assets/ui_premium/tank_card.png"
                    onToggled: prototype.toggle("f9")
                }
            }
            MetalPanel {
                Layout.fillWidth: true; Layout.fillHeight: true
                Layout.horizontalStretchFactor: 57
                Layout.minimumWidth: 420
                ColumnLayout {
                    anchors.fill: parent; anchors.leftMargin: 23; anchors.rightMargin: 23; anchors.topMargin: 24; anchors.bottomMargin: 20; spacing: 8
                    RowLayout {
                        Text { text: "Мониторинг серверов"; color: ink; font.pixelSize: window.compact ? 17 : 21; font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
                        FriendIndicator { count: prototype.friendCount }
                    }
                    ServerTable {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        Layout.minimumHeight: 82
                        rows: prototype.rows; selected: prototype.selected
                        onChosen: address => prototype.select(address)
                    }
                    PlayerRoster {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        Layout.minimumHeight: 70
                        players: prototype.players
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        MetalButton { text: "Добавить сервер"; glyph: "icons/add.svg"; Layout.fillWidth: true; onClicked: { if (prototype.demo) prototype.request("add_server"); else addDialog.open() } }
                        MetalButton { text: "Обновить"; glyph: "icons/refresh.svg"; Layout.fillWidth: true; onClicked: prototype.request("refresh") }
                        AmberButton { text: "Подключиться"; glyph: "icons/connect.svg"; Layout.fillWidth: true; enabled: prototype.canConnect; onClicked: prototype.request("connect") }
                    }
                }
            }
        }
        MetalPanel {
            Layout.fillWidth: true; Layout.preferredHeight: 74
            Layout.leftMargin: 17; Layout.rightMargin: 17; Layout.bottomMargin: 8
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 34; anchors.rightMargin: 34; spacing: 24
                OverlayControl { Layout.fillWidth: true; active: prototype.overlay; controlsEnabled: prototype.demo; onToggled: prototype.toggle("overlay") }
                Rectangle { width: 1; height: 34; color: "#776345" }
                SmartEngineControl { Layout.fillWidth: true; active: prototype.smart; controlsEnabled: prototype.demo; onToggled: prototype.toggle("smart") }
                Rectangle { width: 1; height: 34; color: "#776345" }
                SystemStatusPanel { Layout.fillWidth: true; statusText: prototype.status; ready: false }
            }
        }
    }
}
