import QtQuick
import QtQuick.Layouts
RowLayout {
    id: root
    property string statusText: "Режим сравнения"
    property bool ready: false
    spacing: 8
    Rectangle { width: 9; height: 9; radius: 5; color: root.ready ? "#b0db84" : "#d4a75e" }
    Text { text: root.statusText; color: root.ready ? "#b0db84" : "#f1d2a0"; font.bold: true; font.pixelSize: 13; elide: Text.ElideRight; Layout.fillWidth: true }
}
