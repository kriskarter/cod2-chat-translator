import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    visible: true
    width: 1366; height: 768
    minimumWidth: 840; minimumHeight: 460
    title: "CoD2 Chat Translator — " + (prototype.demo ? (prototype.uiLanguage, prototype.trText("демонстрация")) : prototype.translationAvailable ? (prototype.uiLanguage, prototype.trText("Translation · разработка")) : (prototype.uiLanguage, prototype.trText("UDP Monitor · разработка")))
    color: "#111313"
    property bool compact: width < 1100 || height < 620
    property bool shortWindow: height < 620
    property color ink: "#f5e7c9"
    property int navIndex: 0
    property string activePage: "home"
    property string evidenceDialog: ""
    onEvidenceDialogChanged: {
        if (evidenceDialog === "friends_panel") friendsPanel.open()
        else if (evidenceDialog === "add_server_dialog") addDialog.open()
        else if (workspaceLoader.item && workspaceLoader.item.showEvidenceDialog) workspaceLoader.item.showEvidenceDialog(evidenceDialog)
    }
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
    FriendPanel {id:friendsPanel}
    Rectangle {
        id:notice;objectName:"friend_notice";parent:window.contentItem;z:100
        anchors.right:parent.right;anchors.bottom:parent.bottom;anchors.margins:18
        width:Math.min(390,parent.width-36);height:noticeBody.implicitHeight+22
        radius:7;color:"#252d24";border.color:"#b09862";visible:noticeTimer.running
        ColumnLayout {id:noticeBody;anchors.left:parent.left;anchors.right:parent.right;anchors.top:parent.top;anchors.margins:11
            RowLayout {Layout.fillWidth:true
                Image {source:"icons/friends.svg";Layout.preferredWidth:22;Layout.preferredHeight:22}
                Text {id:noticeTitle;color:"#d6e9aa";font.bold:true;Layout.fillWidth:true;wrapMode:Text.WordWrap}
                MetalButton {text:"×";implicitWidth:28;implicitHeight:26;onClicked:noticeTimer.stop()}
            }
            Text {id:noticeDetail;textFormat:Text.PlainText;color:"#e5d5b5";Layout.fillWidth:true;wrapMode:Text.WordWrap}
        }
        Timer {id:noticeTimer;interval:5500;repeat:false}
        Connections {target:prototype;function onFriendNotice(title,detail){noticeTitle.text=title;noticeDetail.text=detail;noticeTimer.restart()}}
    }
    MetalDialog {
        id: addDialog
        objectName:"add_server_dialog"
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
            Layout.preferredHeight: window.activePage !== "home" ? Math.min(94, window.height * .16) : Math.min(window.width / 6.9, window.height * (window.shortWindow ? .20 : .25))
            clip: true
            Rectangle { anchors.fill: parent; color: "#25251e" }
            Image {
                anchors.fill: parent
                source: "../assets/ui_premium/command_panorama.jpg"
                fillMode: Image.PreserveAspectCrop
            }
            Image {
                anchors.horizontalCenter: parent.horizontalCenter; anchors.verticalCenter: parent.verticalCenter
                height: parent.height * .78; width: Math.min(parent.width * .54, height * 4.2)
                anchors.verticalCenterOffset: -parent.height * .055
                source: "command_logo.png"
                fillMode: Image.PreserveAspectFit
            }
            Row {
                visible:window.activePage==="home"; anchors.horizontalCenter: parent.horizontalCenter; y: parent.height * .19
                spacing: Math.min(parent.width*.26,parent.height*1.7)
                Repeater { model: 2; Image { source:"icons/star.svg"; width:Math.max(16,Math.min(30,window.height*.035)); height:width } }
            }
            Rectangle { anchors.horizontalCenter: parent.horizontalCenter; y:parent.height*.80; width:Math.min(parent.width*.38, parent.height*3.0); height:1; color:"#d0a45d" }
            Text { anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: window.activePage === "home" ? 7 : 3; text: "Intelligent Gaming Companion"; font.pixelSize: window.compact || window.activePage !== "home" ? 10 : 14; font.letterSpacing: 3; font.italic: true; color: "#ead7ad" }
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#a27c49" }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: window.shortWindow ? 36 : 44
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
                        selected: window.activePage === modelData.key || modelData.key === "settings" && ["profiles","knowledge","notifications","stats","overlay","outgoing"].indexOf(window.activePage) >= 0
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
            Layout.leftMargin: 12; Layout.rightMargin: 12; Layout.topMargin: window.shortWindow ? 5 : 10; Layout.bottomMargin: 5
            spacing: 12
            ColumnLayout {
                Layout.fillWidth: true; Layout.fillHeight: true
                Layout.horizontalStretchFactor: 43
                spacing: 10
                TranslationCard {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    keyName: "F8"; live: prototype.translationAvailable; liveStatus: live ? window.tr(!prototype.f8?"Выключен":prototype.logReady?"Ожидание сообщений":"Журнал не выбран") : ""; heading: (prototype.uiLanguage, prototype.trText("Входящий перевод")); description: prototype.translationAvailable ? (prototype.uiLanguage, prototype.trText("Чат → ")) + prototype.targetLanguage : (prototype.uiLanguage, prototype.trText("Чат → русский"))
                    active: prototype.f8; compact: window.compact; controlsEnabled: prototype.demo || prototype.translationAvailable
                    artwork: "../assets/ui_premium/translation_card_source.jpg"
                    onToggled: prototype.toggle("f8")
                }
                TranslationCard {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    keyName: "F9"; live: prototype.translationAvailable; liveStatus: live ? window.tr(!prototype.f9?"Выключен":prototype.gameHotkeysReady?"Активен":"Ручной режим") : ""; onManual: window.activePage = "outgoing"; heading: (prototype.uiLanguage, prototype.trText("Исходящий перевод")); description: prototype.translationAvailable ? prototype.outgoingSource.toUpperCase() + " → " + prototype.outgoingTarget.toUpperCase() : (prototype.uiLanguage, prototype.trText("Русский → English"))
                    active: prototype.f9; compact: window.compact; controlsEnabled: prototype.demo || prototype.translationAvailable
                    artwork: "../assets/ui_premium/tank_card.png"
                    onToggled: prototype.toggle("f9")
                }
            }
            MetalPanel {
                Layout.fillWidth: true; Layout.fillHeight: true
                Layout.horizontalStretchFactor: 57
                Layout.minimumWidth: window.compact ? 400 : 420
                ColumnLayout {
                    anchors.fill: parent; anchors.leftMargin: window.shortWindow ? 10 : 18; anchors.rightMargin: anchors.leftMargin; anchors.topMargin: window.shortWindow ? 9 : 18; anchors.bottomMargin: anchors.topMargin; spacing: window.shortWindow ? 3 : 7
                    RowLayout {
                        Image { source:"icons/antenna.svg"; Layout.preferredWidth:32; Layout.preferredHeight:32 }
                        Text { text: (prototype.uiLanguage, prototype.trText("Мониторинг серверов")); color: ink; font.pixelSize: window.compact ? 17 : 21; font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
                        FriendIndicator { count: prototype.friendCount;onOpenFriends:friendsPanel.open() }
                    }
                    ServerTable {
                        Layout.fillWidth: true; Layout.fillHeight: false
                        Layout.preferredHeight: Math.min(30 + Math.max(1, prototype.rows.length)*30, window.shortWindow ? 80 : 135)
                        Layout.minimumHeight: 48
                        rows: prototype.rows; selected: prototype.selected
                        onChosen: address => prototype.select(address)
                    }
                    PlayerRoster {
                        objectName:"home_roster"; population: prototype.selectedPopulation
                        Layout.fillWidth: true; Layout.fillHeight: true
                        Layout.minimumHeight: window.shortWindow ? 45 : 70
                        players: prototype.players
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        MetalButton { objectName:"add_server_button"; text: (prototype.uiLanguage, prototype.trText("Добавить сервер")); glyph: "icons/add.svg"; Layout.fillWidth: true; onClicked: { if (prototype.demo) prototype.request("add_server"); else addDialog.open() } }
                        MetalButton { text: (prototype.uiLanguage, prototype.trText("Обновить")); glyph: "icons/refresh.svg"; Layout.fillWidth: true; onClicked: prototype.request("refresh") }
                        AmberButton { objectName:"connect_button"; text: (prototype.uiLanguage, prototype.trText("Подключиться")); glyph: "icons/connect.svg"; Layout.fillWidth: true; enabled: prototype.canConnect; onClicked: prototype.request("connect") }
                    }
                }
            }
        }
        Loader {
            id:workspaceLoader; objectName:"active_workspace"; Layout.minimumHeight:0
            active: prototype.serverManagementAvailable && window.activePage === "servers" || prototype.translationAvailable && window.activePage !== "home"
            visible: active; Layout.fillWidth: true; Layout.fillHeight: true
            Layout.margins: 17
            sourceComponent: window.activePage === "servers" ? serverPage : ["profiles","knowledge","notifications","about","stats","overlay"].indexOf(window.activePage) >= 0 ? operationsPage : translationPage
            Component { id: serverPage; ServerWorkspace { onAddRequested: addDialog.open();onOpenFriends:friendsPanel.open() } }
            Component { id: translationPage; TranslationWorkspace { page: window.activePage; onNavigate: page => window.activePage = page } }
            Component { id: operationsPage; OperationsWorkspace { page: window.activePage; onBack:window.activePage="settings" } }
        }
        MetalPanel {
            objectName:"system_bar"
            visible:window.activePage==="home" || !window.shortWindow
            Layout.fillWidth: true; Layout.minimumHeight: window.shortWindow ? 52 : 78; Layout.preferredHeight: Layout.minimumHeight; Layout.maximumHeight: Layout.minimumHeight
            Layout.leftMargin: 17; Layout.rightMargin: 17; Layout.bottomMargin: 8
            RowLayout {
                anchors.fill: parent; anchors.margins: window.shortWindow ? 8 : 14; spacing: 10
                OverlayControl { Layout.fillWidth: true; onConfigure: window.activePage = "overlay"; active: prototype.overlay; controlsEnabled: prototype.demo || prototype.overlayAvailable; onToggled: prototype.toggle("overlay") }
                Rectangle { width: 1; height: 34; color: "#776345" }
                SmartEngineControl { Layout.fillWidth: true; active: prototype.smart; controlsEnabled: prototype.demo || prototype.translationAvailable; onToggled: prototype.toggle("smart") }
                Rectangle { width: 1; height: 34; color: "#776345" }
                SystemStatusPanel { Layout.fillWidth: true; statusText: prototype.translationAvailable ? prototype.translationStatus : prototype.status; ready: !prototype.demo && prototype.translationAvailable && prototype.engineReady && prototype.logReady; onConfigure: window.activePage = "settings" }
            }
        }
    }
}
