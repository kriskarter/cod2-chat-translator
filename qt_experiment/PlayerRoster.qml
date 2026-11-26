import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
MetalPanel {
    id: root
    property var players: []
    ColumnLayout {
        anchors.fill: parent; anchors.leftMargin: 19; anchors.rightMargin: 19; anchors.topMargin: 20; anchors.bottomMargin: 17; spacing: 5
        Text { text: "Игроки на сервере"; color: "#d4a75e"; font.pixelSize: 13; font.bold: true }
        ListView {
            id: roster
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            model: root.players
            ScrollBar.vertical: MetalScrollBar {}
            delegate: Rectangle {
                id: row
                required property int index
                required property var modelData
                width: roster.width - 12; height: 23
                color: index % 2 ? "#171919" : "#202221"
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 8; anchors.rightMargin: 8
                    Text { text: row.modelData.richName; textFormat: Text.RichText; color: "#efcf9b"; Layout.fillWidth: true; elide: Text.ElideRight; font.pixelSize: 12 }
                    Text { text: row.modelData.score; color: "#f5e7c9"; Layout.preferredWidth: 65; font.pixelSize: 12 }
                    Text { text: row.modelData.ping; color: "#b8dc89"; Layout.preferredWidth: 55; font.pixelSize: 12 }
                }
            }
        }
    }
}
