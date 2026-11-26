import QtQuick
import QtQuick.Layouts
RowLayout {
    id: root
    property int count: 0
    Rectangle { width: 8; height: 8; radius: 4; color: "#b4de82" }
    Text { text: "Друзья в игре: " + root.count; color: "#b4de82"; font.pixelSize: 12 }
}
