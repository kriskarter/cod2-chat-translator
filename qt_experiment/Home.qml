import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    visible: true
    width: 1366; height: 768
    minimumWidth: 900; minimumHeight: 620
    title: "CoD2 Chat Translator — " + (prototype.demo ? (prototype.uiLanguage, prototype.trText("демонстрация")) : prototype.translationAvailable ? (prototype.uiLanguage, prototype.trText("Translation · разработка")) : (prototype.uiLanguage, prototype.trText("UDP Monitor · разработка")))
    color: "#111313"
    property bool compact: width < 1100
    property color ink: "#f5e7c9"
    property int navIndex: 0
    property string activePage: "home"
    property string uiLocale: prototype.uiLanguage
    function tr(s) { let l = uiLocale; return prototype.trText(s) }
    palette.window: "#171b1c"
    palette.base: "#171b1c"
    palette.text: "#f5e7c9"
    palette.windowText: "#f5e7c9"
    palette.button: "#30312b"
    palette.buttonText: "#f5e7c9"
    palette.highlight: "#88622d"
    palette.highlightedText: "#fff1cd"
    MetalDialog {
        id: addDialog
        anchors.centerIn: parent
        title: (prototype.uiLanguage, prototype.trText("Добавить сервер"))
        standardButtons: Dialog.NoButton
        width: 390
        ColumnLayout {
            anchors.fill: parent
            MetalTextField { id: addressField; placeholderText: "host:28960"; Layout.fillWidth: true }
            MetalTextField { id: labelField; placeholderText: (prototype.uiLanguage, prototype.trText("Название")); Layout.fillWidth: true }
            Text { text: prototype.status; color: "#e4c291"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            RowLayout {
                MetalButton { text: (prototype.uiLanguage, prototype.trText("Отмена")); onClicked: addDialog.close() }
                AmberButton { text: (prototype.uiLanguage, prototype.trText("Добавить")); onClicked: if (prototype.addServer(addressField.text, labelField.text)) addDialog.close() }
            }
        }
    }

    Image {
        anchors.fill: parent; source: "../assets/ui_wwii/body_backdrop.png"
        fillMode: Image.PreserveAspectCrop; opacity: .28
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
                anchors.horizontalCenter: parent.horizontalCenter; anchors.verticalCenter: parent.verticalCenter
                height: parent.height * .78; width: Math.min(parent.width * .54, height * 4.2)
                anchors.verticalCenterOffset: -parent.height * .055
                source: "command_logo.png"
                fillMode: Image.PreserveAspectFit
            }
            Text { anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 8; text: "Intelligent Gaming Companion"; font.pixelSize: window.compact ? 10 : 14; font.letterSpacing: 3; font.italic: true; color: "#ead7ad" }
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#a27c49" }
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
                        objectName: "nav_" + modelData.key
                        text: window.tr(modelData.name)
                        glyph: "icons/" + modelData.icon + ".svg"
                        selected: index === window.navIndex
                        enabled: index === 0 || prototype.demo || (prototype.serverManagementAvailable && modelData.key === "servers") || (prototype.translationAvailable && (modelData.key === "settings" || modelData.key === "history" || modelData.key === "about"))
                        Layout.fillWidth: true; Layout.fillHeight: true
                        onClicked: {
                            if (prototype.translationAvailable || prototype.serverManagementAvailable) { window.navIndex = index; window.activePage = modelData.key }
                            else prototype.request("nav:" + modelData.key)
                        }
                    }
                }
            }
        }
        RowLayout {
            visible: window.activePage === "home"
            Layout.fillWidth: true; Layout.fillHeight: true
            Layout.leftMargin: 17; Layout.rightMargin: 17; Layout.topMargin: 10; Layout.bottomMargin: 8
            spacing: 12
            ColumnLayout {
                Layout.fillWidth: true; Layout.fillHeight: true
                Layout.horizontalStretchFactor: 43
                spacing: 10
                TranslationCard {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    keyName: "F8"; heading: (prototype.uiLanguage, prototype.trText("Входящий перевод")); description: prototype.translationAvailable ? (prototype.uiLanguage, prototype.trText("Чат → ")) + prototype.targetLanguage : (prototype.uiLanguage, prototype.trText("Чат → русский"))
                    active: prototype.f8; compact: window.compact; controlsEnabled: prototype.demo || prototype.translationAvailable
                    artwork: "../assets/ui_premium/translation_card_source.jpg"
                    onToggled: prototype.toggle("f8")
                }
                MetalButton {
                    objectName: "manual_outgoing"
                    visible: prototype.translationAvailable; Layout.fillWidth: true
                    text: (prototype.uiLanguage, prototype.trText("Открыть ручной перевод")); onClicked: { window.activePage = "outgoing"; window.navIndex = -1 }
                }
                TranslationCard {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    keyName: "F9"; heading: (prototype.uiLanguage, prototype.trText("Исходящий перевод")); description: prototype.translationAvailable ? (prototype.uiLanguage, prototype.trText("Ручной перевод текста")) : (prototype.uiLanguage, prototype.trText("Русский → English"))
                    active: prototype.f9; compact: window.compact; controlsEnabled: prototype.demo || prototype.translationAvailable
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
                        Text { text: (prototype.uiLanguage, prototype.trText("Мониторинг серверов")); color: ink; font.pixelSize: window.compact ? 17 : 21; font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
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
                        MetalButton { text: (prototype.uiLanguage, prototype.trText("Добавить сервер")); glyph: "icons/add.svg"; Layout.fillWidth: true; onClicked: { if (prototype.demo) prototype.request("add_server"); else addDialog.open() } }
                        MetalButton { text: (prototype.uiLanguage, prototype.trText("Обновить")); glyph: "icons/refresh.svg"; Layout.fillWidth: true; onClicked: prototype.request("refresh") }
                        AmberButton { text: (prototype.uiLanguage, prototype.trText("Подключиться")); glyph: "icons/connect.svg"; Layout.fillWidth: true; enabled: prototype.canConnect; onClicked: prototype.request("connect") }
                    }
                }
            }
        }
        Loader {
            active: prototype.serverManagementAvailable && window.activePage === "servers" || prototype.translationAvailable && window.activePage !== "home"
            visible: active; Layout.fillWidth: true; Layout.fillHeight: true
            Layout.margins: 17
            sourceComponent: window.activePage === "servers" ? serverPage : ["profiles","knowledge","notifications","about","stats","overlay"].indexOf(window.activePage) >= 0 ? operationsPage : translationPage
            Component { id: serverPage; ServerWorkspace { onAddRequested: addDialog.open() } }
            Component { id: translationPage; TranslationWorkspace { page: window.activePage; onNavigate: page => window.activePage = page } }
            Component { id: operationsPage; OperationsWorkspace { page: window.activePage } }
        }
        MetalPanel {
            Layout.fillWidth: true; Layout.minimumHeight: 66; Layout.preferredHeight: 66; Layout.maximumHeight: 66
            Layout.leftMargin: 17; Layout.rightMargin: 17; Layout.bottomMargin: 8
            RowLayout {
                anchors.fill: parent; anchors.margins: 14; spacing: 14
                OverlayControl { Layout.fillWidth: true; active: prototype.overlay; controlsEnabled: prototype.demo || prototype.overlayAvailable; onToggled: prototype.toggle("overlay") }
                Rectangle { width: 1; height: 34; color: "#776345" }
                SmartEngineControl { Layout.fillWidth: true; active: prototype.smart; controlsEnabled: prototype.demo || prototype.translationAvailable; onToggled: prototype.toggle("smart") }
                Rectangle { width: 1; height: 34; color: "#776345" }
                SystemStatusPanel { Layout.fillWidth: true; statusText: prototype.translationAvailable ? prototype.translationStatus : prototype.status; ready: !prototype.demo && prototype.translationAvailable && prototype.gameHotkeysReady }
            }
        }
    }
}
