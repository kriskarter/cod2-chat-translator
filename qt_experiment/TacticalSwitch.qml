import QtQuick
import QtQuick.Controls

Switch {
    id: root
    property bool attention:false
    property bool error:false
    readonly property bool warning: checked && (attention || error)
    readonly property color indicatorColor: !checked ? "#a6a296" : error ? "#ee957d" : attention ? "#e7be77" : "#d7e7a8"
    property bool cardStyle: false
    implicitWidth: cardStyle ? 124 : 76; implicitHeight: cardStyle ? 38 : 31
    padding: 0; hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    readonly property string stateText: (prototype.uiLanguage, prototype.trText(
        cardStyle ? (checked ? "Вкл" : "Выключен") : (checked ? "Вкл" : "Выкл")))
    indicator: Item {
        anchors.centerIn: parent
        width: parent.width; height: Math.min(parent.height,root.cardStyle ? 38 : 29)
        opacity: root.enabled ? 1 : .48
        BorderImage {
            anchors.fill: parent
            visible: !root.warning
            source: root.cardStyle ? "reference_art/badge.png" : "reference_art/toggle.png"
            border { left: 9; right: 9; top: 7; bottom: 7 }
        }
        Rectangle {
            anchors.fill: parent; anchors.margins: 1; radius: root.cardStyle ? 7 : height / 2
            visible: root.warning || !root.checked || root.visualFocus || root.hovered
            color: root.warning ? (root.error ? "#392322" : "#382c1d") : root.checked ? "transparent" : "#d4252622"
            border.color: root.warning ? root.indicatorColor : root.visualFocus ? "#f4c675" : root.hovered ? "#b7a474" : "#69675d"
        }
        Row {
            anchors.centerIn: parent; spacing: root.cardStyle ? 6 : 4
            Image {
                visible: root.cardStyle && root.checked && !root.warning
                source: "reference_art/check.png"
                width: root.height*.66; height: width
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: root.stateText; color: root.indicatorColor
                font.pixelSize: root.cardStyle ? Math.max(10,Math.min(16,root.width*.132)) : 12
                font.bold: true; anchors.verticalCenter: parent.verticalCenter
            }
            Rectangle {
                visible: !root.cardStyle; width: 14; height: 14; radius: 7
                anchors.verticalCenter: parent.verticalCenter
                color: root.warning ? root.indicatorColor : root.checked ? "#9cda61" : "#65635b"
                Image { anchors.fill: parent; source:"reference_art/green_lamp.png";visible:root.checked && !root.warning }
            }
        }
    }
    contentItem: Item {}
    background: Item {}
}
