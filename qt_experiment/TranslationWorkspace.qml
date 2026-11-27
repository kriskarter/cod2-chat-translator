import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

MetalPanel {
    id: root
    function showEvidenceDialog(name) {
        if (name==="history_clear_dialog") historyClear.open()
        else if (name==="outgoing_hud_dialog") root.configureHud()
    }
    objectName:"translation_workspace"; clip:true
    property string page: "history"
    signal navigate(string page)
    signal configureHud()
    property string uiLocale: prototype.uiLanguage
    function tr(s) { let l = uiLocale; return prototype.trText(s) }
    FileDialog {
        id:historyExport;fileMode:FileDialog.SaveFile;nameFilters:["TXT (*.txt)", "JSON (*.json)"];defaultSuffix:selectedNameFilter.index === 1 ? "json" : "txt"
        onAccepted:{let path=decodeURIComponent(selectedFile.toString().replace(/^file:\/\//,""));if(Qt.platform.os==="windows"&&path.startsWith("/"))path=path.substring(1);prototype.exportHistory(path)}
    }
    MetalDialog {
        id:historyClear;objectName:"history_clear_dialog";title:root.tr("Очистить историю?");anchors.centerIn:parent;standardButtons:Dialog.Yes|Dialog.No
        Text {text:root.tr("Удаляются только сообщения текущей сессии.");color:"#f5e7c9"}
        onAccepted:prototype.clearHistory()
    }
    MetalDialog {
        id: elevationConfirm; title: root.tr("Перезапустить от имени администратора?")
        anchors.centerIn: parent; standardButtons: Dialog.Yes | Dialog.No
        Text { width: 340; wrapMode: Text.WordWrap; color: "#f5e7c9"; text: root.tr("Настройки сохранятся. Windows запросит подтверждение UAC. Следующий запуск будет запрашивать права администратора.") }
        onAccepted: prototype.restartElevated()
    }
    ColumnLayout {
        anchors.fill: parent; anchors.margins: root.height < 350 ? 10 : 16; spacing: 8
        Text {
            text: root.page === "settings" ? (prototype.uiLanguage, prototype.trText("Настройки перевода")) : root.page === "outgoing" ? (prototype.uiLanguage, prototype.trText("Исходящий перевод · ручной режим")) : (prototype.uiLanguage, prototype.trText("История игрового чата"))
            color: "#fff0d1"; font.bold: true; font.pixelSize: 22
        }
        RowLayout {
            visible:root.page==="history";Layout.fillWidth:true
            Text {text:root.tr("История текущей сессии · экспорт содержит никнеймы и текст");color:"#bcb09a";wrapMode:Text.WordWrap;Layout.fillWidth:true}
            MetalTextField { id: search; placeholderText:root.tr("Ник или текст"); Layout.preferredWidth:165; Layout.minimumWidth:80; Layout.fillWidth:true }
            LanguageSelector { id:direction; textRole:"label"; valueRole:"code"; model:[{label:root.tr("Все"),code:""},{label:root.tr("Входящие"),code:"in"},{label:root.tr("Исходящие"),code:"out"}];currentIndex:0 }
            TacticalSwitch { checked:prototype.historyEnabled; Accessible.name:root.tr("Запись истории"); onClicked:prototype.setHistoryEnabled(checked) }
            MetalButton {text:root.tr("Экспорт");enabled:prototype.history.length>0;onClicked:historyExport.open()}
            MetalButton {text:root.tr("Очистить");enabled:prototype.history.length>0;onClicked:historyClear.open()}
        }
        
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
                    RowLayout {
                        visible:prototype.showShortcutHint
                        Text { text:root.tr("F8 — входящий перевод · F9 — ваше сообщение · F10 — снимок экрана"); color:"#e6d5b8"; Layout.fillWidth:true; wrapMode:Text.Wrap }
                        MetalButton { text:"×"; sizeClass:"compact"; onClicked:prototype.dismissShortcutHint() }
                    }
                    RowLayout {
                        Text { text:root.tr("Запрашивать права администратора при запуске"); color:"#e6d5b8" }
                        TacticalSwitch { checked:prototype.alwaysAdmin; onClicked:prototype.setAlwaysAdmin(checked) }
                    }
                    GridLayout {
                        Layout.fillWidth: true
                        Layout.maximumWidth: 780
                        columns: settingsScroll.width < 800 ? 3 : 5
                        columnSpacing: 6; rowSpacing: 6
                        MetalButton { objectName:"manual_outgoing"; text:root.tr("Ручной перевод"); Layout.fillWidth:true; onClicked:root.navigate("outgoing") }
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
                            artBorder: false
                            Layout.fillWidth: true
                            Layout.preferredHeight: inputForm.implicitHeight + 32
                            ColumnLayout {
                                id: inputForm
                                anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 16
                                spacing: 8
                                Text { text: root.tr("Язык интерфейса"); color: "#e4c291"; font.bold: true }
                                LanguageSelector {
                                    objectName: "uiLocaleSelector"
                                    model: [{label:"Русский",code:"ru"},{label:"Українська",code:"uk"},{label:"English",code:"en"}]
                                    textRole: "label"; valueRole: "code"
                                    Component.onCompleted: currentIndex = indexOfValue(prototype.uiLanguage)
                                    onActivated: prototype.setUiLanguage(currentValue)
                                    Layout.fillWidth: true
                                }
                                Text { text: root.tr("Журнал CoD2 (console_mp.log)"); color: "#e4c291"; font.bold: true }
                                RowLayout {
                                    Layout.fillWidth: true
                                    MetalTextField { id: logInput; objectName:"logPathInput"; text: prototype.logPath; placeholderText: root.tr("Путь к console_mp.log"); Layout.fillWidth: true; selectByMouse: true }
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
                            artBorder: false
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
                                        objectName: "styleSelector"
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
                    text: prototype.gameHotkeysReady ? (prototype.uiLanguage, prototype.trText("Перехватчик установлен. Ожидание игровых нажатий.")) :
                          prototype.gameHotkeysEnabled ? (prototype.uiLanguage, prototype.trText("Игровой keyboard hook ещё не готов.")) : (prototype.uiLanguage, prototype.trText("Игровые клавиши выключены в этом запуске."))
                    color: "#d4a75e"; wrapMode: Text.WordWrap; Layout.fillWidth: true
                }

                MetalButton { objectName: "outgoingHudSettingsButton"; text: root.tr("Настройки игрового окна F9"); onClicked: root.configureHud() }
                Text { visible: prototype.gamePrivilegeMismatch; color: "#f1ac93"; wrapMode: Text.WordWrap; Layout.fillWidth: true
                    text: root.tr("CoD2 запущена от администратора, а переводчик — нет. Игровые клавиши и отправка могут не работать. По возможности запустите обе программы без повышения прав.") }
                MetalButton { visible: prototype.gamePrivilegeMismatch && prototype.settingsWritable; text: root.tr("Перезапустить переводчик от имени администратора"); onClicked: elevationConfirm.open() }
                Text { visible: prototype.gameHotkeysEnabled; text: root.tr(prototype.gameRunning ? "Игра запущена" : "Игра не запущена"); color: "#bcb09a" }
                MetalButton { visible: prototype.gameHotkeysEnabled; text: (prototype.uiLanguage, prototype.trText("Открыть журнал клавиш")); onClicked: prototype.openShortcutLog() }
                Text { visible: prototype.gameHotkeyDetail.length > 0; text: prototype.gameHotkeyDetail; color: "#e4c291"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Text { text: (prototype.uiLanguage, prototype.trText("Ручной режим не отправляет сообщения в игру.")); color: "#d4a75e"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            }
            }
            ListView {
                id: history
                clip: true; model: prototype.history.filter(row => {
                    let query=search.text.trim().toLocaleLowerCase()
                    return (!direction.currentValue || row.direction === direction.currentValue) &&
                        [row.nickname,row.original,row.translated].some(v => String(v || "").toLocaleLowerCase().includes(query))
                }); spacing: 4
                ScrollBar.vertical: MetalScrollBar {}
                delegate: Rectangle {
                    required property var modelData
                    width: history.width - 15; height: entry.implicitHeight + 18
                    color: "#252726"; radius: 4
                    ColumnLayout {
                        id: entry
                        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 9
                        RowLayout {
                            Layout.fillWidth:true
                            Text { text:(modelData.received || "—")+" · "+root.tr(modelData.direction==="out"?"Исходящие":"Входящие")+" · "+modelData.nickname; textFormat:Text.PlainText; color:"#d4a75e";Layout.fillWidth:true;elide:Text.ElideRight }
                            MetalButton { text:root.tr("Копировать");sizeClass:"compact";onClicked:prototype.copyMessage(modelData.nickname+" · "+modelData.original+"\n"+modelData.translated) }
                        }
                        Text { text: modelData.original; textFormat: Text.PlainText; color: "#bcb09a"; Layout.fillWidth: true; wrapMode: Text.Wrap }
                        Text { text: modelData.translated || root.tr(modelData.outcome); textFormat: Text.PlainText; color: "#f5e7c9"; Layout.fillWidth: true; wrapMode: Text.Wrap }
                    }
                }
                ColumnLayout {anchors.centerIn:parent;width:Math.min(parent.width-24,490);visible:history.count===0 && !search.text && !direction.currentValue;spacing:8
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