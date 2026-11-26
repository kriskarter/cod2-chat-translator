import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

MetalPanel {
    id: root
    property string page: "history"
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 30; spacing: 12
        Text {
            text: root.page === "settings" ? "Настройки перевода" : root.page === "outgoing" ? "Исходящий перевод · ручной режим" : "История входящего перевода"
            color: "#fff0d1"; font.bold: true; font.pixelSize: 22
        }
        Text { text: prototype.translationStatus; color: "#e4c291"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        StackLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            currentIndex: root.page === "settings" ? 0 : root.page === "outgoing" ? 1 : 2
            ColumnLayout {
                Text { text: "Журнал CoD2 (console_mp.log)"; color: "#f5e7c9" }
                RowLayout {
                    Layout.fillWidth: true
                    TextField { id: logInput; text: prototype.logPath; placeholderText: "Путь к console_mp.log"; Layout.fillWidth: true; selectByMouse: true }
                    MetalButton { text: "Применить"; onClicked: prototype.setLogPath(logInput.text) }
                }
                Text { text: "Язык входящего перевода"; color: "#f5e7c9" }
                LanguageSelector {
                    model: [{label:"Русский",code:"ru"},{label:"Українська",code:"uk"},{label:"English",code:"en"},{label:"Deutsch",code:"de"},{label:"Polski",code:"pl"},{label:"Français",code:"fr"}]
                    textRole: "label"; valueRole: "code"
                    Component.onCompleted: currentIndex = indexOfValue(prototype.targetLanguage)
                    onActivated: prototype.setTargetLanguage(currentValue)
                    Layout.preferredWidth: 220
                }
                RowLayout {
                    Text { text: "Smart Engine"; color: "#f5e7c9" }
                    TacticalSwitch { checked: prototype.smart; onClicked: prototype.toggle("smart") }
                }
                Text { text: "Изменения действуют в этой сессии. Существующие файлы настроек не изменяются."; color: "#c6ae88"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Item { Layout.fillHeight: true }
            }
            ColumnLayout {
                Text { text: "Перевод текста без отправки в игру"; color: "#f5e7c9" }
                ScrollView {
                    Layout.fillWidth: true; Layout.preferredHeight: 85
                    TextArea { id: outgoingInput; placeholderText: "Введите сообщение"; wrapMode: TextEdit.Wrap; selectByMouse: true }
                }
                RowLayout {
                    LanguageSelector { id: sourceLanguage; model: ["auto","ru","uk","en","de","pl","fr"]; Layout.preferredWidth: 130 }
                    LanguageSelector { id: destLanguage; model: ["en","ru","uk","de","pl","fr"]; Layout.preferredWidth: 130 }
                    AmberButton {
                        text: prototype.outgoingBusy ? "Перевод…" : "Перевести"
                        enabled: prototype.f9 && !prototype.outgoingBusy && outgoingInput.text.trim().length > 0
                        onClicked: prototype.submitOutgoing(outgoingInput.text, sourceLanguage.currentText, destLanguage.currentText)
                    }
                }
                ScrollView {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    TextArea { text: prototype.outgoingResult; readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap }
                }
                Text {
                    text: prototype.gameHotkeysReady ? "Игровые F8/F9/F10 подключены · F9 и Enter отправляют только в активную CoD2." :
                          prototype.gameHotkeysEnabled ? "Игровой keyboard hook ещё не готов." : "Игровые клавиши выключены в этом запуске."
                    color: "#d4a75e"; wrapMode: Text.WordWrap; Layout.fillWidth: true
                }
                Text { text: "Ручной режим не отправляет сообщения в игру."; color: "#d4a75e"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            }
            ListView {
                id: history
                clip: true; model: prototype.history; spacing: 4
                ScrollBar.vertical: MetalScrollBar {}
                delegate: Rectangle {
                    required property var modelData
                    width: history.width - 15; height: entry.implicitHeight + 18
                    color: "#252726"; radius: 4
                    ColumnLayout {
                        id: entry
                        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 9
                        Text { text: modelData.nickname + " · " + modelData.elapsed + " ms"; textFormat: Text.PlainText; color: "#d4a75e"; Layout.fillWidth: true; elide: Text.ElideRight }
                        Text { text: modelData.original; textFormat: Text.PlainText; color: "#bcb09a"; Layout.fillWidth: true; wrapMode: Text.Wrap }
                        Text { text: modelData.translated || modelData.outcome; textFormat: Text.PlainText; color: "#f5e7c9"; Layout.fillWidth: true; wrapMode: Text.Wrap }
                    }
                }
                Text { anchors.centerIn: parent; visible: history.count === 0; text: "Новые сообщения появятся здесь"; color: "#bcb09a" }
            }
        }
    }
}