import QtQuick
import QtQuick.Controls

Button {
    id: root
    property string surface: "metal"
    property bool selected: false
    property string sizeClass: text.length ? "standard" : "icon"
    property url glyph
    readonly property bool gold: surface === "amber" || selected
    readonly property bool hasGlyph: glyph.toString().length > 0
    readonly property int slice: 6
    font.family: "Segoe UI"
    font.pixelSize: 13
    font.bold: true
    implicitHeight: sizeClass === "primary" ? 40 : sizeClass === "compact" ? 28 : sizeClass === "icon" ? 30 : 36
    implicitWidth: Math.max(text.length ? 56 : 30, caption.implicitWidth + (hasGlyph ? 16 : 0) + row.spacing + leftPadding + rightPadding)
    leftPadding: sizeClass === "icon" ? 4 : sizeClass === "compact" ? 8 : 12
    rightPadding: leftPadding
    topInset: 0; bottomInset: 0
    leftInset: 0; rightInset: 0
    topPadding: 3
    bottomPadding: 3
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    contentItem: Item {
        Row {
            id: row
            anchors.centerIn: parent
            spacing: root.hasGlyph && root.text.length ? 6 : 0
            Image {
                visible: root.hasGlyph
                source: root.glyph
                width: 16; height: 16
                anchors.verticalCenter: parent.verticalCenter
                fillMode: Image.PreserveAspectFit
            }
            Text {
                id: caption
                objectName: "button_caption"
                text: root.text
                textFormat: Text.PlainText
                font: root.font
                color: root.enabled ? "#fff0d3" : "#b4b1a6"
                width: Math.min(implicitWidth, Math.max(0, root.availableWidth - (root.hasGlyph ? 16 + row.spacing : 0)))
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
            }
        }
    }
    background: BorderImage {
        source: "art/" + (root.gold ? "amber_button" : "metal_button")
                + (!root.enabled ? "_disabled" : root.down ? "_pressed" : root.activeFocus ? "_focused" : root.hovered ? "_hover" : "") + ".png"
        opacity: root.surface === "quiet" && !root.hovered && !root.visualFocus && !root.down ? .35 : 1
        border { left: root.slice; right: root.slice; top: root.slice; bottom: root.slice }
        Rectangle {
            anchors.fill: parent; anchors.margins: 2
            color: "transparent"; radius: 3
            border.color: "#efd19a"; visible: root.visualFocus
        }
    }
    ToolTip.visible: hovered && caption.truncated
    ToolTip.text: text
}
