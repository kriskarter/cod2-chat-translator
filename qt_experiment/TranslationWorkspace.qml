import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

MetalPanel {
    id: root
    function showEvidenceDialog(name) { if (name==="history_clear_dialog") historyClear.open() }
    objectName:"translation_workspace"; clip:true
    property string page: "history"
    signal navigate(string page)
    property string uiLocale: prototype.uiLanguage
    function tr(s) { let l = uiLocale; return prototype.trText(s) }
    FileDialog {
        id:historyExport;fileMode:FileDialog.SaveFile;nameFilters:["JSON (*.json)"];defaultSuffix:"json"
        onAccepted:{let path=decodeURIComponent(selectedFile.toString().replace(/^file:\/\//,""));if(Qt.platform.os==="windows"&&path.startsWith("/"))path=path.substring(1);prototype.exportHistory(path)}
    }
    MetalDialog {
        id:historyClear;objectName:"history_clear_dialog";title:root.tr("Очистить историю?");anchors.centerIn:parent;standardButtons:Dialog.Yes|Dialog.No
        Text {text:root.tr("Удаляются только сообщения текущей сессии.");color:"#f5e7c9"}
        onAccepted:prototype.clearHistory()
    }
    ColumnLayout {
        anchors.fill: parent; anchors.margins: root.height < 350 ? 10 : 16; spacing: 8
        Text {
            text: root.page === "settings" ? (prototype.uiLanguage, prototype.trText("Настройки перевода")) : root.page === "outgoing" ? (prototype.uiLanguage, prototype.trText("Исходящий перевод · ручной режим")) : (prototype.uiLanguage, prototype.trText("История входящего перевода"))
            color: "#fff0d1"; font.bold: true; font.pixelSize: 22
        }
        RowLayout {
            visible:root.page==="history";Layout.fillWidth:true
            Text {text:root.tr("История текущей сессии · экспорт содержит никнеймы и текст");color:"#bcb09a";wrapMode:Text.WordWrap;Layout.fillWidth:true}
            MetalButton {text:root.tr("Экспорт JSON");enabled:prototype.history.length>0;onClicked:historyExport.open()}
            MetalButton {text:root.tr("Очистить");enabled:prototype.history.length>0;onClicked:historyClear.open()}
        }
        Text { visible:root.page!=="history";text: prototype.translationStatus; color: "#e4c291"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        StackLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight:0
            currentIndex: root.page === "settings" ? 0 : root.page === "outgoing" ? 1 : 2
            Flickable {
                id: settingsScroll;objectName:"settings_scroll"
                clip: true
                contentWidth: width
                contentHeight: settingsContent.height + 12
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: MetalScrollBar {
                    parent: settingsScroll
                    anchors.right: settingsScroll.right
                    anchors.top: settingsScroll.top
                    anchors.bottom: settingsScroll.bottom
                    policy: ScrollBar.AsNeeded
                }
                ColumnLayout {
                    id: settingsContent
                    width: settingsScroll.width - 15; height:implicitHeight
                    spacing: 10
                    GridLayout {
                        Layout.fillWidth: true
                        columns: width < 800 ? 3 : 5
                        columnSpacing: 6; rowSpacing: 6
                        MetalButton { glyph:"icons/servers.svg";text: root.tr("Профили"); Layout.fillWidth: true; onClicked: root.navigate("profiles") }
                        MetalButton { glyph:"icons/chip.svg";text: root.tr("База знаний"); Layout.fillWidth: true; onClicked: root.navigate("knowledge") }
                        MetalButton { glyph:"icons/friends.svg";text: root.tr("Уведомления"); Layout.fillWidth: true; onClicked: root.navigate("notifications") }
                        MetalButton { glyph:"icons/history.svg";text: root.tr("Статистика"); Layout.fillWidth: true; onClicked: root.navigate("stats") }
                        MetalButton { glyph:"icons/hud.svg";text: root.tr("Оверлей"); Layout.fillWidth: true; onClicked: root.navigate("overlay") }
                    }
                    GridLayout {
                        columns: width < 680 ? 1 : 2
                        Layout.fillWidth: true; columnSpacing: 12; rowSpacing: 12
                        MetalPanel {
                            Layout.fillWidth: true
                            Layout.preferredHeight: inputForm.implicitHeight + 32
                            ColumnLayout {
                                id: inputForm
                                anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 16
                                spacing: 8
                                Text { text: root.tr("Язык интерфейса"); color: "#e4c291"; font.bold: true }
                                LanguageSelector {
                                    model: [{label:"Русский",code:"ru"},{label:"Українська",code:"uk"},{label:"English",code:"en"}]
                                    textRole: "label"; valueRole: "code"
                                    Component.onCompleted: currentIndex = indexOfValue(prototype.uiLanguage)
                                    onActivated: prototype.setUiLanguage(currentValue)
                                    Layout.fillWidth: true
                                }
                                Text { text: root.tr("Журнал CoD2 (console_mp.log)"); color: "#e4c291"; font.bold: true }
                                RowLayout {
                                    Layout.fillWidth: true
                                    MetalTextField { id: logInput; text: prototype.logPath; placeholderText: root.tr("Путь к console_mp.log"); Layout.fillWidth: true; selectByMouse: true }
                                    MetalButton { text: root.tr("Применить"); onClicked: prototype.setLogPath(logInput.text) }
                                }
                                Text { text: root.tr("Язык входящего перевода"); color: "#e4c291"; font.bold: true }
                                LanguageSelector {
                                    model: prototype.languages
                                    textRole: "label"; valueRole: "code"
                                    Component.onCompleted: currentIndex = indexOfValue(prototype.targetLanguage)
                                    onActivated: prototype.setTargetLanguage(currentValue)
                                    Layout.fillWidth: true
                                }
                            }
                        }
                        MetalPanel {
                            Layout.fillWidth: true
                            Layout.preferredHeight: engineForm.implicitHeight + 32
                            ColumnLayout {
                                id: engineForm
                                anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 16
                                spacing: 7
                                RowLayout {
                                    Text { text: "Smart Engine"; color: "#e4c291"; font.bold: true; Layout.fillWidth: true }
                                    TacticalSwitch { checked: prototype.smart; onClicked: prototype.toggle("smart") }
                                }
                                RowLayout {
                                    Text { text: root.tr("Стили перевода"); color: "#f5e7c9"; Layout.fillWidth: true }
                                    LanguageSelector {
                                        model: [{label:root.tr("Понятный"),code:"clear"},{label:root.tr("Живой"),code:"live"},{label:root.tr("Без цензуры"),code:"raw"}]
                                        textRole:"label";valueRole:"code"
                                        Component.onCompleted: currentIndex = indexOfValue(prototype.preferences.style)
                                        onActivated: prototype.setSlangStyle(currentValue)
                                        Layout.preferredWidth: 120
                                    }
                                }
                                Repeater {
                                    model: [{key:"original", label:"Показывать оригинал"}, {key:"hide", label:"Скрывать выбранный язык"}, {key:"slang", label:"Игровой сленг"}, {key:"dedupe", label:"Убирать повторы"}]
                                    delegate: RowLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        Text { text: root.tr(modelData.label); color: "#f5e7c9"; Layout.fillWidth: true; elide: Text.ElideRight }
                                        TacticalSwitch { checked: !!prototype.preferences[modelData.key]; onClicked: prototype.setPreference(modelData.key, checked) }
                                    }
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { objectName:"settings_last";text: prototype.settingsWritable ? root.tr("Настройки сохраняются в отдельном Qt-файле.") : root.tr("Изменения действуют в этой сессии. Существующие файлы настроек не изменяются."); color: "#c6ae88"; wrapMode: Text.WordWrap; Layout.fillWidth: true }

                    }
                }
            }
            Flickable {
                id:outgoingScroll
                clip:true;contentWidth:width;contentHeight:outgoingContent.implicitHeight+8
                boundsBehavior:Flickable.StopAtBounds
                ScrollBar.vertical:MetalScrollBar {parent:outgoingScroll;anchors.top:outgoingScroll.top;anchors.bottom:outgoingScroll.bottom;anchors.right:outgoingScroll.right}
                ColumnLayout {
                    id:outgoingContent; width:outgoingScroll.width-12
                Text { text: (prototype.uiLanguage, prototype.trText("Перевод текста без отправки в игру")); color: "#f5e7c9" }
                ScrollView {
                    Layout.fillWidth: true; Layout.preferredHeight: 85
                    MetalTextArea { id: outgoingInput; placeholderText: (prototype.uiLanguage, prototype.trText("Введите сообщение")); wrapMode: TextEdit.Wrap; selectByMouse: true }
                }
                RowLayout {
                    LanguageSelector {
                        id: sourceLanguage; model: prototype.outgoingLanguages; textRole: "label"; valueRole: "code"
                        Component.onCompleted: currentIndex = indexOfValue(prototype.outgoingSource)
                        Layout.preferredWidth: 170
                        onActivated: prototype.setOutgoingRoute(currentValue, prototype.outgoingTarget)
                    }
                    LanguageSelector {
                        id: destLanguage; model: prototype.outgoingLanguages; textRole: "label"; valueRole: "code"
                        Component.onCompleted: currentIndex = indexOfValue(prototype.outgoingTarget)
                        Layout.preferredWidth: 170
                        onActivated: prototype.setOutgoingRoute(prototype.outgoingSource, currentValue)
                    }
                    AmberButton {
                        text: prototype.outgoingBusy ? (prototype.uiLanguage, prototype.trText("Перевод…")) : (prototype.uiLanguage, prototype.trText("Перевести"))
                        enabled: prototype.f9 && !prototype.outgoingBusy && outgoingInput.text.trim().length > 0
                        onClicked: prototype.submitOutgoing(outgoingInput.text, sourceLanguage.currentValue, destLanguage.currentValue)
                    }
                }
                ScrollView {
                    Layout.fillWidth: true; Layout.preferredHeight:100
                    MetalTextArea { text: prototype.outgoingResult; readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap }
                }
                Text {
                    text: prototype.gameHotkeysReady ? (prototype.uiLanguage, prototype.trText("Игровые F8/F9/F10 подключены · F9 и Enter отправляют только в активную CoD2.")) :
                          prototype.gameHotkeysEnabled ? (prototype.uiLanguage, prototype.trText("Игровой keyboard hook ещё не готов.")) : (prototype.uiLanguage, prototype.trText("Игровые клавиши выключены в этом запуске."))
                    color: "#d4a75e"; wrapMode: Text.WordWrap; Layout.fillWidth: true
                }

                Text { text: (prototype.uiLanguage, prototype.trText("Ручной режим не отправляет сообщения в игру.")); color: "#d4a75e"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            }
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
                        Text { text: (modelData.received || "—") + " · " + modelData.nickname + " · " + modelData.elapsed + " ms"; textFormat: Text.PlainText; color: "#d4a75e"; Layout.fillWidth: true; elide: Text.ElideRight }
                        Text { text: modelData.original; textFormat: Text.PlainText; color: "#bcb09a"; Layout.fillWidth: true; wrapMode: Text.Wrap }
                        Text { text: modelData.translated || modelData.outcome; textFormat: Text.PlainText; color: "#f5e7c9"; Layout.fillWidth: true; wrapMode: Text.Wrap }
                    }
                }
                ColumnLayout {anchors.centerIn:parent;width:Math.min(parent.width-24,490);visible:history.count===0;spacing:8
                    Image {source:"icons/history.svg";Layout.alignment:Qt.AlignHCenter;Layout.preferredWidth:36;Layout.preferredHeight:36}
                    Text {text:root.tr(prototype.logReady?"Журнал подключён":"Журнал не выбран");color:"#e4c291";font.bold:true;font.pixelSize:16;Layout.alignment:Qt.AlignHCenter}
                    Text {text:root.tr(!prototype.logReady?"Выберите игровой журнал в настройках.":!prototype.f8?"Входящий перевод выключен.":"Ожидание новых сообщений в игре.");color:"#bcb09a";wrapMode:Text.WordWrap;Layout.fillWidth:true;horizontalAlignment:Text.AlignHCenter}
                    Text {text:root.tr("История хранится только до закрытия приложения.");color:"#a49c8d";wrapMode:Text.WordWrap;Layout.fillWidth:true;horizontalAlignment:Text.AlignHCenter}
                }
            }
        }
        RowLayout {
            visible:(root.page==="settings"||root.page==="outgoing")&&prototype.settingsWritable
            Layout.fillWidth:true
            Item { Layout.fillWidth:true }
            AmberButton {objectName:"save_settings";text:root.tr("Сохранить настройки");onClicked:prototype.saveSettings()}
        }
    }
}