import QtQuick
import QtQuick.Controls

ComboBox {
    id: root
    property bool inlineRoute: false
    readonly property bool subtle: inlineRoute && !hovered && !activeFocus && !popup.visible
    hoverEnabled: true
    font.pixelSize: inlineRoute ? 15 : 13
    implicitHeight: 32
    implicitWidth: 130
    leftPadding: inlineRoute ? 4 : 9
    rightPadding: 21
    contentItem: Text {
        text: root.displayText; textFormat: Text.PlainText
        color: root.enabled ? "#f5e7c9" : "#a39d91"
        font: root.font; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight
    }
    background: Rectangle {
        opacity: root.subtle ? .58 : 1
        radius: 4; color: "#252521"
        border.color: root.activeFocus ? "#e8b96c" : "#736854"
        Image { anchors.fill: parent; anchors.margins: 2; source: "reference_art/inset.webp" }
    }
    indicator: Text {
        x: root.width - width - 6; anchors.verticalCenter: parent.verticalCenter
        text: root.popup.visible ? "▴" : "▾"; font.pixelSize: 17; color: "#e4be7d"
    }
    delegate: ItemDelegate {
        id: option
        required property int index
        width: root.popup.availableWidth
        height: 32; leftPadding: 10; rightPadding: 15
        highlighted: root.highlightedIndex === index
        hoverEnabled: true
        contentItem: Text {
            text: root.textAt(option.index); textFormat: Text.PlainText
            color: option.enabled ? "#f4e7ce" : "#9d978c"; font: root.font
            elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 3
            color: option.highlighted || option.hovered ? "#56422a" : option.index === root.currentIndex ? "#383024" : "transparent"
            border.color: option.highlighted || option.visualFocus ? "#ba965b" : "transparent"
        }
    }
    popup: Popup {
        y: root.height + 2
        width: Math.max(root.width, 132)
        margins: 6; padding: 5
        implicitHeight: Math.min(268, list.contentHeight + 2 * padding)
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        background: MetalPanel {}
        contentItem: ListView {
            id: list
            clip: true; model: root.popup.visible ? root.delegateModel : null
            currentIndex: root.highlightedIndex
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: MetalScrollBar {}
        }
    }
}
