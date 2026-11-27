import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

MetalPanel {
    id: root
    function showEvidenceDialog(name) { if (name==="server_remove_dialog") { removeDialog.address=selectedAddress; removeDialog.open() } }
    clip:true;objectName:"server_workspace"
    readonly property bool compactEditor: height < 420
    signal addRequested()
    signal openFriends()
    property string selectedAddress: prototype.selected
    property var record: prototype.serverRecords.find(r => r.address === selectedAddress)
    property string editingAddress: ""
    property var selectedRow: prototype.rows.find(r=>r.address===selectedAddress)
    function loadEditor() {
        editingAddress = selectedAddress
        let fields = prototype.serverAddressFields(selectedAddress)
        hostInput.text = fields.host || ""
        portInput.text = fields.port || "28960"
        editorError.text = ""
        // selectedAddressChanged can fire before the record binding refreshes.
        // Resolve the exact selected record now, never the previous row.
        let selectedRecord = prototype.serverRecords.find(r => r.address === selectedAddress)
        labelInput.text = selectedRecord ? selectedRecord.label : ""
        favoriteInput.checked = selectedRecord ? selectedRecord.favorite : false
    }
    onSelectedAddressChanged: loadEditor()
    Component.onCompleted: loadEditor()

    MetalDialog {
        id: removeDialog
        objectName:"server_remove_dialog"
        title: (prototype.uiLanguage, prototype.trText("Удаление сервера"))
        anchors.centerIn: parent
        property string address
        standardButtons: Dialog.Yes | Dialog.No
        Text { text: (prototype.uiLanguage, prototype.trText("Удалить выбранный сервер из списка?")); color: "#f5e7c9" }
        onAccepted: { if (!prototype.removeServer(address)) editorError.text = prototype.serverSaveError }
    }
    ColumnLayout {
        anchors.fill:parent;anchors.margins:14;spacing:5
        RowLayout {
            Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumHeight:0;spacing:12
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumWidth: 350; Layout.minimumHeight:0
            RowLayout {
                Text { text: (prototype.uiLanguage, prototype.trText("Серверы CoD2")); font.bold: true; font.pixelSize: 22; color: "#fff0d1"; Layout.fillWidth: true }
                FriendIndicator { count: prototype.friendCount;onOpenFriends:root.openFriends() }
            }
            Text { text: prototype.status; color: "#d4a75e"; Layout.fillWidth: true; elide: Text.ElideRight }
            ServerTable { rows: prototype.rows; selected: prototype.selected; onChosen: address => prototype.select(address); Layout.fillWidth: true; Layout.fillHeight:false; Layout.minimumHeight:48; Layout.maximumHeight:Layout.preferredHeight; Layout.preferredHeight: Math.min(108, 26 + 34*Math.max(1,prototype.rows.length)) }
            PlayerRoster { objectName:"server_roster";Layout.minimumHeight:40;population:prototype.selectedPopulation; players: prototype.players; Layout.fillWidth: true; Layout.fillHeight: true }
            RowLayout {
                MetalButton { objectName:"server_add";text: (prototype.uiLanguage, prototype.trText("Добавить")); glyph: "icons/add.svg"; Layout.fillWidth: true; onClicked: root.addRequested() }
                MetalButton { objectName:"server_refresh";text: (prototype.uiLanguage, prototype.trText("Обновить")); glyph: "icons/refresh.svg"; Layout.fillWidth: true; onClicked: prototype.request("refresh") }
                AmberButton { objectName:"server_connect";text: (prototype.uiLanguage, prototype.trText("Подключиться")); enabled: prototype.canConnect && root.selectedAddress.length > 0; Layout.fillWidth: true; onClicked: prototype.request("connect") }
            }
        }
        Flickable {
            id:editorScroll;objectName:"server_editor_scroll"
            Layout.preferredWidth:Math.min(400,root.width*.40);Layout.minimumWidth:270;Layout.fillHeight:true;Layout.minimumHeight:0
            clip:true;contentWidth:width;contentHeight:editorBody.implicitHeight+8;boundsBehavior:Flickable.StopAtBounds
            ScrollBar.vertical:MetalScrollBar {}
        ColumnLayout {
            id:editorBody;width:editorScroll.width-12;height:implicitHeight;spacing:root.compactEditor?3:4
            Text { text: (prototype.uiLanguage, prototype.trText("Настройки сервера")); color: "#f5e7c9"; font.pixelSize: 17; font.bold: true }
            Text { text: root.selectedAddress || (prototype.uiLanguage, prototype.trText("Выберите сервер")); color: "#bcb09a"; Layout.fillWidth: true; elide: Text.ElideRight }
            Rectangle { visible:!!root.selectedRow;Layout.fillWidth:true;Layout.preferredHeight:root.compactEditor?40:46;radius:5;color:"#202621";border.color:"#675a44"
                ColumnLayout { anchors.fill:parent;anchors.margins:root.compactEditor?4:7
                    Text {text:root.selectedRow?root.selectedRow.name:"";textFormat:Text.PlainText;elide:Text.ElideRight;Layout.fillWidth:true;font.bold:true;color:"#e9d5ae"}
                    Text {text:root.selectedRow?root.selectedRow.map+" · "+root.selectedRow.population+" · "+root.selectedRow.ping:"";color:"#bcb09a";elide:Text.ElideRight;Layout.fillWidth:true}
                }
            }
            Text { text: (prototype.uiLanguage, prototype.trText("IP-адрес или домен")); color: "#f5e7c9" }
            MetalTextField { id: hostInput; objectName: "editServerHost"; Layout.preferredHeight:root.compactEditor?32:38; padding:root.compactEditor?6:9; enabled: !!root.record; Layout.fillWidth: true
                onEditingFinished: {
                    let fields = prototype.pastedServerFields(text, portInput.text)
                    if (fields.host !== undefined) { text = fields.host; portInput.text = fields.port }
                }
            }
            Text { text: (prototype.uiLanguage, prototype.trText("Порт")); color: "#f5e7c9" }
            MetalTextField { id: portInput; objectName: "editServerPort"; Layout.preferredHeight:root.compactEditor?32:38; padding:root.compactEditor?6:9; enabled: !!root.record; Layout.fillWidth: true; inputMethodHints: Qt.ImhDigitsOnly }
            Text { id: editorError; visible: text.length > 0; color: "#e99b83"; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            MetalTextField { id: labelInput; objectName:"serverLabelInput"; Layout.preferredHeight:root.compactEditor?32:38; padding:root.compactEditor?6:9; enabled: !!root.record; placeholderText: (prototype.uiLanguage, prototype.trText("Название сервера")); Layout.fillWidth: true }
            RowLayout {
                Text { text: (prototype.uiLanguage, prototype.trText("Избранный сервер")); color: "#f5e7c9"; Layout.fillWidth: true }
                TacticalSwitch { id: favoriteInput; objectName: "serverFavoriteInput"; enabled: !!root.record }
            }
            RowLayout {
                MetalButton { text: (prototype.uiLanguage, prototype.trText("Применить")); enabled: !!root.record; Layout.fillWidth: true; onClicked: {
                    let address = prototype.serverAddressPreview(hostInput.text, portInput.text)
                    if (!address || !prototype.editServerAddress(root.editingAddress, address, labelInput.text, favoriteInput.checked))
                        editorError.text = prototype.serverSaveError || (prototype.uiLanguage, prototype.trText("Неверный адрес, повтор или достигнут лимит"))
                    else root.loadEditor()
                } }
                MetalButton { text: (prototype.uiLanguage, prototype.trText("Удалить")); enabled: !!root.record; Layout.fillWidth: true; onClicked: { removeDialog.address = root.editingAddress; removeDialog.open() } }
            }
            Rectangle { color: "#6d5837"; height: 1; Layout.fillWidth: true }
            Text { text: (prototype.uiLanguage, prototype.trText("Избранные игроки")); color: "#f5e7c9"; font.pixelSize: 17; font.bold: true }
            RowLayout {
                MetalTextField { id: friendInput; placeholderText: (prototype.uiLanguage, prototype.trText("Ник игрока")); Layout.fillWidth: true }
                MetalButton { text: (prototype.uiLanguage, prototype.trText("Добавить")); glyph: "icons/add.svg"; enabled: friendInput.text.trim().length > 0; onClicked: if (prototype.addFriend(friendInput.text)) friendInput.clear() }
            }
            Text {visible:prototype.friendSaveError.length>0;text:prototype.friendSaveError;color:"#e99b83";wrapMode:Text.WordWrap;Layout.fillWidth:true}
            ListView {
                id: friendList
                Layout.fillWidth: true; Layout.preferredHeight:Math.max(42,Math.min(160,prototype.friends.length*38));
                model: prototype.friends; clip: true; spacing: 3
                ScrollBar.vertical: MetalScrollBar {}
                delegate: RowLayout {
                    required property string modelData
                    width: friendList.width - 12
                    Text { text: prototype.friendDisplayName(modelData); textFormat: Text.PlainText; color: "#f5e7c9"; Layout.fillWidth: true; elide: Text.ElideRight }
                    MetalButton { text: (prototype.uiLanguage, prototype.trText("Убрать")); onClicked: prototype.removeFriend(modelData) }
                }
            }

            Text { visible: !prototype.settingsWritable; text: (prototype.uiLanguage, prototype.trText("Изменения только в этой сессии")); color: "#c6ae88"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }
        }
        RowLayout {visible:prototype.settingsWritable;Layout.fillWidth:true
            Item {Layout.fillWidth:true}
            AmberButton {objectName:"server_save";text:(prototype.uiLanguage,prototype.trText("Сохранить настройки"));onClicked:prototype.saveSettings()}
        }
    }
}
