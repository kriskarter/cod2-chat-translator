import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
ColumnLayout {
    id: root
    property var rows: []
    property string selected: ""
    signal chosen(string address)
    spacing: 2
    component Cells: RowLayout {
        property var values
        property bool header: false
        property bool online: false
        property bool favorite: false
        spacing: 7
        Image { source: "icons/favorite.svg"; opacity: favorite ? 1 : 0; Layout.preferredWidth: 14; Layout.preferredHeight: 14 }
        Text { text: values[0]; Layout.fillWidth: true; Layout.minimumWidth: 55; color: header ? "#bcb09a" : "#f5e7c9"; elide: Text.ElideRight; font.pixelSize: header ? 11 : 13 }
        Text { text: values[1]; Layout.preferredWidth: 86; color: header ? "#bcb09a" : "#f5e7c9"; elide: Text.ElideRight; font.pixelSize: 12 }
        Text { text: values[2]; Layout.preferredWidth: 55; color: header ? "#bcb09a" : "#f5e7c9"; font.pixelSize: 12 }
        Text { text: values[3]; Layout.preferredWidth: 53; color: header ? "#bcb09a" : "#add880"; font.pixelSize: 12 }
        Text { text: values[4]; Layout.preferredWidth: 58; color: header ? "#bcb09a" : online ? "#a9d978" : "#bcb8ad"; font.pixelSize: 12 }
    }
    Item {
        Layout.fillWidth: true; Layout.preferredHeight: 24
        Cells { anchors.fill: parent; anchors.leftMargin: 9; anchors.rightMargin: 21; header: true; values: [(prototype.uiLanguage, prototype.trText("Сервер")), (prototype.uiLanguage, prototype.trText("Карта")), (prototype.uiLanguage, prototype.trText("Игроки")), (prototype.uiLanguage, prototype.trText("Пинг")), (prototype.uiLanguage, prototype.trText("Статус"))] }
    }
    ListView {
        id: table
        Layout.fillWidth: true; Layout.fillHeight: true
        clip: true; spacing: 2
        model: root.rows
        ScrollBar.vertical: MetalScrollBar {}
        delegate: Item {
            id: line
            required property var modelData
            width: table.width - 12; height: 33
            BorderImage {
                anchors.fill: parent
                source: root.selected === line.modelData.address ? "../assets/ui_wwii/premium_selection.png" : "../assets/ui_wwii/premium_selection_clear.png"
                border { left: 10; right: 10; top: 8; bottom: 8 }
            }
            Rectangle {
                anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
                anchors.margins: 3; width: 3; radius: 1
                color: "#e5b875"; visible: root.selected === line.modelData.address
            }
            Cells {
                anchors.fill: parent; anchors.leftMargin: 9; anchors.rightMargin: 9
                values: [line.modelData.name, line.modelData.map, line.modelData.population, line.modelData.ping, (prototype.uiLanguage, prototype.trText(line.modelData.state))]
                favorite: !!line.modelData.favorite
                online: line.modelData.state === "online"
            }
            TapHandler { onTapped: root.chosen(line.modelData.address) }
        }
    }
}
