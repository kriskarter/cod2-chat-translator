import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    visible: true
    width: 1366; height: 768
    minimumWidth: 840; minimumHeight: 460
    title: "CoD2 Chat Translator" + (prototype.translationAvailable ? " — " + prototype.appVersion : prototype.demo ? " — Demo" : " — UDP Monitor")
    color: "#111313"
    property bool compact: width < 1100 || height < 620
    readonly property bool laptop: height >= 620 && height < 750
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
    onActivePageChanged: feedbackTimer.stop()
    Rectangle {
        parent: window.contentItem; z: 98; visible: feedbackTimer.running
        anchors.bottom: parent.bottom; anchors.horizontalCenter: parent.horizontalCenter; anchors.bottomMargin: 12
        width: Math.min(parent.width - 32, feedbackText.implicitWidth + 34); height: feedbackText.implicitHeight + 18
        radius: 6; color: "#202823"; border.color: "#817759"
        Text { id: feedbackText; anchors.centerIn: parent; width: parent.width - 24; wrapMode: Text.Wrap; textFormat: Text.PlainText; horizontalAlignment: Text.AlignHCenter }
        Timer { id: feedbackTimer; interval: 3500 }
        Connections {
            target: prototype
            ignoreUnknownSignals: true
            function onFeedback(page, message, error) {
                if (page && page !== window.activePage) return
                feedbackText.text = message
                feedbackText.color = error ? "#f1ac93" : "#d2e5b4"
                feedbackTimer.restart()
            }
        }
    }
    function openFriendsFromTray() { noticeTimer.stop(); friendsPanel.open() }
    FriendPanel {id:friendsPanel}
    MetalPanel {
        id:notice;objectName:"friend_notice";parent:window.contentItem;z:100
        anchors.right:parent.right;anchors.bottom:parent.bottom;anchors.margins:18
        width:Math.min(390,parent.width-36);height:noticeBody.implicitHeight+22
        visible:noticeTimer.running
        TapHandler { onTapped: window.openFriendsFromTray() }
        ColumnLayout {id:noticeBody;anchors.left:parent.left;anchors.right:parent.right;anchors.top:parent.top;anchors.margins:11
            RowLayout {Layout.fillWidth:true
                Image {source:"reference_art/friends.png";Layout.preferredWidth:22;Layout.preferredHeight:22}
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
        anchors.fill: parent; source: "reference_art/sheet.webp"
        fillMode: Image.Stretch
    }
    Image {
        objectName: "field_kit"
        anchors.left: parent.left; anchors.bottom: parent.bottom
        width: Math.min(window.width * .20, window.height * .374, window.activePage === "home" ? 400 : (systemBar.height + systemBar.Layout.bottomMargin)*310/191)
        height: width * 191 / 310
        visible: !window.compact
        enabled: false
        source: "reference_art/field_kit.webp"; fillMode: Image.PreserveAspectFit
        z: 2
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Item {
            Layout.fillWidth: true
            objectName:"command_banner"
            Layout.preferredHeight: Math.min(window.width * 198 / 1534, window.laptop ? 95 + (window.height-620)*.37 : window.height * (window.shortWindow ? .17 : .239))
            Layout.minimumHeight: Layout.preferredHeight; Layout.maximumHeight: Layout.preferredHeight
            clip: true
            Row {
                anchors.fill: parent
                Image { width: (parent.width - wordmark.width)*519/951; height: parent.height; source: "reference_art/left.webp" }
                Image { id: wordmark; objectName: "command_logo"; width: Math.min(parent.width, parent.height*583/198); height: parent.height; source: "reference_art/wordmark.webp" }
                Image { width: parent.width - wordmark.width - (parent.width-wordmark.width)*519/951; height: parent.height; source: "reference_art/right.webp" }
            }
        }
        MetalPanel {
            objectName:"command_navigation";artBorder:false;texture:"reference_art/nav.webp"
            Layout.fillWidth: true; Layout.preferredHeight: window.shortWindow ? 34 : Math.min(50,window.height*.061)
            Layout.minimumHeight:Layout.preferredHeight;Layout.maximumHeight:Layout.preferredHeight
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: window.shortWindow ? 10 : 23; anchors.rightMargin: 12; anchors.topMargin: 1; anchors.bottomMargin: 1; spacing: 1
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
                        glyph: "reference_art/" + modelData.icon + ".png"
                        glyphSize: window.shortWindow ? 17 : 26
                        font.pixelSize: window.shortWindow ? 13 : 17
                        selected: window.activePage === modelData.key || modelData.key === "settings" && ["profiles","knowledge","notifications","stats","overlay","outgoing"].indexOf(window.activePage) >= 0
                        enabled: index === 0 || prototype.demo || (prototype.serverManagementAvailable && modelData.key === "servers") || (prototype.translationAvailable && (modelData.key === "settings" || modelData.key === "history" || modelData.key === "about"))
                        Layout.preferredWidth: Math.min((window.width-40)/5,(index===3 ? 215 : 182) * Math.min(1,window.width/1450)); Layout.fillHeight: true
                        onClicked: {
                            if (prototype.translationAvailable || prototype.serverManagementAvailable) { window.navIndex = index; window.activePage = modelData.key }
                            else prototype.request("nav:" + modelData.key)
                        }
                    }
                }
                Item { Layout.fillWidth: true }
            }
        }
        RowLayout {
            visible: window.activePage === "home"
            Layout.fillWidth: true; Layout.fillHeight: true
            Layout.leftMargin: window.shortWindow ? 10 : 17; Layout.rightMargin: window.shortWindow ? 10 : 15; Layout.topMargin: window.compact ? 5 : window.laptop ? 8 : 14; Layout.bottomMargin: window.compact ? 5 : window.laptop ? 8 : 14
            spacing: window.shortWindow ? 8 : 13
            ColumnLayout {
                Layout.fillWidth: true; Layout.fillHeight: true
                Layout.preferredWidth: (window.width - 45) * .436
                Layout.minimumWidth: 0
                Layout.topMargin: window.compact ? 0 : Math.min(14,window.height*.017)
                Layout.bottomMargin: window.compact ? 0 : Math.min(60,window.height*.071)
                spacing: window.compact ? 8 : Math.min(22,window.height*.027)
                TranslationCard {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    keyName: "F8"; live: prototype.translationAvailable; liveStatus: live ? window.tr(!prototype.f8?"Выключен":prototype.logReady?"Ожидание сообщений":"Журнал не выбран") : ""; heading: (prototype.uiLanguage, prototype.trText("Входящий перевод")); description: prototype.translationAvailable ? (prototype.uiLanguage, prototype.trText("Чат → ")) + prototype.targetLanguage : (prototype.uiLanguage, prototype.trText("Чат → русский"))
                    active: prototype.f8; compact: window.compact; controlsEnabled: prototype.demo || prototype.translationAvailable
                    artwork: "reference_art/f8_plate.webp"
                    onToggled: prototype.toggle("f8")
                }
                TranslationCard {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    keyName: "F9"; live: prototype.translationAvailable; liveStatus: live ? window.tr(!prototype.f9?"Выключен":prototype.gameHotkeysReady?"Активен":"Ручной режим") : ""; onManual: window.activePage = "outgoing"; heading: (prototype.uiLanguage, prototype.trText("Исходящий перевод")); description: prototype.translationAvailable ? prototype.outgoingSource.toUpperCase() + " → " + prototype.outgoingTarget.toUpperCase() : (prototype.uiLanguage, prototype.trText("Русский → English"))
                    active: prototype.f9; compact: window.compact; controlsEnabled: prototype.demo || prototype.translationAvailable
                    artwork: "reference_art/f9_plate.webp"
                    onToggled: prototype.toggle("f9")
                }
            }
            MetalPanel {
                Layout.fillWidth: true; Layout.fillHeight: true
                objectName:"monitor_panel"
                Layout.preferredWidth: (window.width - 45) * .564
                Layout.minimumWidth: window.compact ? 400 : 420
                ColumnLayout {
                    anchors.fill: parent; anchors.leftMargin: window.shortWindow ? 8 : 13; anchors.rightMargin: anchors.leftMargin; anchors.topMargin: window.shortWindow ? 6 : 10; anchors.bottomMargin: anchors.topMargin; spacing: window.shortWindow ? 3 : 5
                    RowLayout {
                        Image { source:"reference_art/antenna.png";fillMode:Image.PreserveAspectFit; Layout.preferredWidth:window.compact?27:50; Layout.preferredHeight:window.compact?28:44 }
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 0
                            Text { text: window.tr("Мониторинг серверов"); color: window.ink; font.pixelSize: window.compact ? 17 : 24; font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
                            Text { text: "Server Monitor"; visible: !window.compact && prototype.uiLanguage !== "en"; color:"#dfc995"; font.pixelSize:16 }
                        }
                        FriendIndicator { count: prototype.friendCount;onOpenFriends:friendsPanel.open() }
                    }
                    ServerTable {
                        Layout.fillWidth: true; Layout.fillHeight: false
                        Layout.preferredHeight: Math.min(30 + Math.max(1, prototype.rows.length)*34, window.shortWindow ? 56 : 134)
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
                        MetalButton { objectName:"add_server_button"; text: (prototype.uiLanguage, prototype.trText("Добавить сервер")); glyph: "reference_art/add.png"; font.pixelSize:window.compact?12:17;glyphSize:window.compact?16:23;implicitHeight:window.compact?32:window.laptop?34:47;Layout.fillWidth: true; onClicked: { if (prototype.demo) prototype.request("add_server"); else addDialog.open() } }
                        MetalButton { text: (prototype.uiLanguage, prototype.trText("Обновить")); glyph: "reference_art/refresh.png"; font.pixelSize:window.compact?12:17;glyphSize:window.compact?16:23;implicitHeight:window.compact?32:window.laptop?34:47;Layout.fillWidth: true; onClicked: prototype.request("refresh") }
                        AmberButton { objectName:"connect_button";sizeClass:window.shortWindow?"standard":"primary"; text: (prototype.uiLanguage, prototype.trText("Подключиться")); glyph: "reference_art/connect.png"; font.pixelSize:window.compact?12:18;glyphSize:window.compact?16:23;implicitHeight:window.compact?32:window.laptop?34:47;Layout.fillWidth: true; enabled: prototype.canConnect; onClicked: prototype.request("connect") }
                    }
                }
            }
        }
        Loader {
            id:workspaceLoader; objectName:"active_workspace"; Layout.minimumHeight:0
            active: prototype.serverManagementAvailable && window.activePage === "servers" || prototype.translationAvailable && window.activePage !== "home"
            visible: active; Layout.fillWidth: true; Layout.fillHeight: true
            Layout.margins: window.shortWindow ? 7 : 12
            sourceComponent: window.activePage === "servers" ? serverPage : ["profiles","knowledge","notifications","about","stats","overlay"].indexOf(window.activePage) >= 0 ? operationsPage : translationPage
            Component { id: serverPage; ServerWorkspace { onAddRequested: addDialog.open();onOpenFriends:friendsPanel.open() } }
            Component { id: translationPage; TranslationWorkspace { page: window.activePage; onNavigate: page => window.activePage = page } }
            Component { id: operationsPage; OperationsWorkspace { page: window.activePage; onBack:window.activePage="settings" } }
        }
        MetalPanel {
            id: systemBar; objectName:"system_bar"; texture:"reference_art/sheet.webp"; rim:"reference_art/console_frame.png"

            visible:window.activePage==="home" || !window.shortWindow
            Layout.fillWidth: true; Layout.minimumHeight: window.shortWindow ? 48 : window.laptop ? 59 : Math.min(94,window.height*.113); Layout.preferredHeight: Layout.minimumHeight; Layout.maximumHeight: Layout.minimumHeight
            Layout.leftMargin: window.compact ? 12 : window.width*.187; Layout.rightMargin: 15; Layout.bottomMargin: window.compact || window.laptop ? 6 : Math.min(24,window.height*.029)
            RowLayout {
                anchors.fill: parent; anchors.margins: window.shortWindow || window.laptop ? 6 : 16; anchors.leftMargin: window.compact ? 8 : 38; anchors.rightMargin: window.compact ? 8 : 24; spacing: window.compact ? 6 : 12
                OverlayControl { Layout.fillWidth: true; onConfigure: window.activePage = "overlay"; active: prototype.overlay; controlsEnabled: prototype.demo || prototype.overlayAvailable; onToggled: prototype.toggle("overlay") }
                Rectangle { width: 1; height: 34; color: "#776345" }
                SmartEngineControl { Layout.fillWidth: true; active: prototype.smart; controlsEnabled: prototype.demo || prototype.translationAvailable; onToggled: prototype.toggle("smart") }
                Rectangle { width: 1; height: 34; color: "#776345" }
                SystemStatusPanel { Layout.fillWidth: true; statusText: prototype.translationAvailable ? prototype.translationStatus : prototype.status; ready: !prototype.demo && prototype.translationAvailable && prototype.engineReady; onConfigure: window.activePage = "settings" }
            }
        }
    }
}
