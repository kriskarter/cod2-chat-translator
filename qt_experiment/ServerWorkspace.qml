import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

MetalPanel {
    id: root
    signal addRequested()
    property string selectedAddress: prototype.selected
    property var record: prototype.serverRecords.find(r => r.address === selectedAddress)
    property string editingAddress: ""
    function loadEditor() {
        editingAddress = selectedAddress
        labelInput.text = record ? record.label : ""
        favoriteInput.checked = record ? record.favorite : false
    }
    onSelectedAddressChanged: loadEditor()
    Component.onCompleted: loadEditor()

    MetalDialog {
        id: removeDialog
        title: "Удаление сервера"
        anchors.centerIn: parent
        property string address
        standardButtons: Dialog.Yes | Dialog.No
        Text { text: "Удалить выбранный сервер из списка?"; color: "#f5e7c9" }
        onAccepted: prototype.removeServer(address)
    }
    RowLayout {
        anchors.fill: parent; anchors.margins: 26; spacing: 16
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumWidth: 390
            RowLayout {
                Text { text: "Серверы CoD2"; font.bold: true; font.pixelSize: 22; color: "#fff0d1"; Layout.fillWidth: true }
                FriendIndicator { count: prototype.friendCount }
            }
            Text { text: prototype.status; color: "#d4a75e"; Layout.fillWidth: true; elide: Text.ElideRight }
            ServerTable { rows: prototype.rows; selected: prototype.selected; onChosen: address => prototype.select(address); Layout.fillWidth: true; Layout.fillHeight: true }
            PlayerRoster { players: prototype.players; Layout.fillWidth: true; Layout.fillHeight: true }
            RowLayout {
                MetalButton { text: "Добавить"; glyph: "icons/add.svg"; Layout.fillWidth: true; onClicked: root.addRequested() }
                MetalButton { text: "Обновить"; glyph: "icons/refresh.svg"; Layout.fillWidth: true; onClicked: prototype.request("refresh") }
                AmberButton { text: "Подключиться"; enabled: prototype.canConnect && root.selectedAddress.length > 0; Layout.fillWidth: true; onClicked: prototype.request("connect") }
            }
        }
        ColumnLayout {
            Layout.preferredWidth: Math.min(330, root.width * .35); Layout.fillHeight: true; spacing: 8
            Text { text: "Настройки сервера"; color: "#f5e7c9"; font.pixelSize: 17; font.bold: true }
            Text { text: root.selectedAddress || "Выберите сервер"; color: "#bcb09a"; Layout.fillWidth: true; elide: Text.ElideRight }
            TextField { id: labelInput; enabled: !!root.record; placeholderText: "Название сервера"; Layout.fillWidth: true }
            RowLayout {
                Text { text: "Избранный сервер"; color: "#f5e7c9"; Layout.fillWidth: true }
                TacticalSwitch { id: favoriteInput; enabled: !!root.record }
            }
            RowLayout {
                MetalButton { text: "Применить"; enabled: !!root.record; Layout.fillWidth: true; onClicked: prototype.editServer(root.editingAddress, labelInput.text, favoriteInput.checked) }
                MetalButton { text: "Удалить"; enabled: !!root.record; Layout.fillWidth: true; onClicked: { removeDialog.address = root.editingAddress; removeDialog.open() } }
            }
            Rectangle { color: "#6d5837"; height: 1; Layout.fillWidth: true }
            Text { text: "Избранные игроки"; color: "#f5e7c9"; font.pixelSize: 17; font.bold: true }
            RowLayout {
                TextField { id: friendInput; placeholderText: "Ник игрока"; Layout.fillWidth: true }
                MetalButton { text: "+"; Layout.preferredWidth: 36; onClicked: if (prototype.addFriend(friendInput.text)) friendInput.clear() }
            }
            ListView {
                id: friendList
                Layout.fillWidth: true; Layout.fillHeight: true
                model: prototype.friends; clip: true; spacing: 3
                ScrollBar.vertical: MetalScrollBar {}
                delegate: RowLayout {
                    required property string modelData
                    width: friendList.width - 12
                    Text { text: modelData; textFormat: Text.PlainText; color: "#f5e7c9"; Layout.fillWidth: true; elide: Text.ElideRight }
                    MetalButton { text: "Убрать"; onClicked: prototype.removeFriend(modelData) }
                }
            }
            AmberButton { text: "Сохранить настройки"; visible: prototype.settingsWritable; Layout.fillWidth: true; onClicked: prototype.saveSettings() }
            Text { visible: !prototype.settingsWritable; text: "Изменения только в этой сессии"; color: "#c6ae88"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }
}
