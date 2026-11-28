import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Dialog {
    id: root
    modal: true
    width: 390
    padding: 20
    palette.windowText: "#f5e7c9"
    palette.text: "#f5e7c9"
    background: MetalPanel {}
    header: Text {
        text: root.title; textFormat: Text.PlainText; color: "#eedcba"
        font.pixelSize: 19; font.bold: true; wrapMode: Text.WordWrap
        leftPadding: 20; rightPadding: 20; topPadding: 16; bottomPadding: 3
    }
    footer: Item {
        visible: root.standardButtons !== Dialog.NoButton
        implicitHeight: visible ? 52 : 0
        RowLayout {
            anchors.right: parent.right; anchors.top: parent.top; anchors.rightMargin: 16; spacing: 8
            MetalButton {
                visible: (root.standardButtons & Dialog.No) !== 0
                text: (prototype.uiLanguage, prototype.trText("Нет"))
                onClicked: root.reject()
            }
            AmberButton {
                visible: (root.standardButtons & Dialog.Yes) !== 0
                text: (prototype.uiLanguage, prototype.trText("Да"))
                onClicked: root.accept()
            }
            MetalButton {
                visible: (root.standardButtons & Dialog.Close) !== 0
                text: (prototype.uiLanguage, prototype.trText("Закрыть"))
                onClicked: root.reject()
            }
        }
    }
    palette.button: "#343730"
    palette.buttonText:"#f5e7c9"
}
