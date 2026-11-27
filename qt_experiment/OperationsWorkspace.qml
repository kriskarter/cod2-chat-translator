import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
MetalPanel {
    id: root
    function showEvidenceDialog(name) { if (name==="knowledge_clear_dialog") clearDialog.open(); else if (name==="game_logging_dialog") loggingDialog.open();else if(name==="update_install_dialog") updateConfirm.open() }
    clip:true; objectName:"operations_workspace"
    property string page: "profiles"
    signal back()
    property string uiLocale: prototype.uiLanguage
    function tr(s) { let l = uiLocale; return prototype.trText(s) }
    FileDialog {
        id: exportDialog; fileMode: FileDialog.SaveFile; nameFilters: ["ZIP (*.zip)"]; defaultSuffix: "zip"
        onAccepted: {
            let path = decodeURIComponent(selectedFile.toString().replace(/^file:\/\//, ""))
            if (Qt.platform.os === "windows" && path.startsWith("/")) path = path.substring(1)
            prototype.exportExperience(path)
        }
    }
    MetalDialog {
        id: clearDialog; objectName:"knowledge_clear_dialog"; title: root.tr("Очистить опыт"); anchors.centerIn: parent
        standardButtons: Dialog.NoButton
        ColumnLayout {
            Text { text: root.tr("Удалить только локальный опыт и кэш?"); color: "#f5e7c9" }
            RowLayout {
                MetalButton { text: root.tr("Отмена"); onClicked: clearDialog.close() }
                AmberButton { text: root.tr("Удалить"); onClicked: { prototype.clearExperience(); clearDialog.close() } }
            }
        }
    }
    MetalDialog {
        id: loggingDialog
        objectName:"game_logging_dialog"
        anchors.centerIn: parent
        title: root.tr("Журнал игры")
        standardButtons: Dialog.Yes | Dialog.No
        Text { width: 335; wrapMode: Text.WordWrap; color: "#f5e7c9"; text: root.tr("Включить logfile 2 в конфигурациях CoD2? Файлы запущенной игры не изменяются.") }
        onAccepted: prototype.enableGameLogging()
    }
    MetalDialog {
        id:updateConfirm;objectName:"update_install_dialog";title:root.tr("Установить обновление?");anchors.centerIn:parent;standardButtons:Dialog.NoButton
        ColumnLayout {
            Text {text:root.tr("Приложение закроется. Настройки сохранятся. Запустится проверенный установщик Qt Preview.");width:360;wrapMode:Text.WordWrap;color:"#f5e7c9";Layout.preferredWidth:360}
            Text {text:root.tr("SHA-256 проверяет целостность, но не является цифровой подписью.");wrapMode:Text.WordWrap;color:"#c6b79e";Layout.fillWidth:true}
            RowLayout {MetalButton {text:root.tr("Отмена");onClicked:updateConfirm.close()} AmberButton {text:root.tr("Установить");onClicked:{updateConfirm.close();prototype.installUpdate()}}}
        }
    }
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 14; spacing: 7
        RowLayout { Layout.fillWidth:true
        MetalButton { text:root.tr("Назад");surface:"quiet";sizeClass:"compact";visible:root.page!=="about";onClicked:root.back() }
        Text { Layout.fillWidth:true; text: root.tr(({profiles:"Профили",knowledge:"База знаний",notifications:"Уведомления",about:"О программе",stats:"Статистика",overlay:"Настройки оверлея"})[root.page] || (prototype.uiLanguage, prototype.trText("О программе"))); font.pixelSize: 23; font.bold: true; color: "#f5e7c9" }
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: "#786342" }
        StackLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight:0
            currentIndex: root.page === "profiles" ? 0 : root.page === "knowledge" ? 1 : root.page === "notifications" ? 2 : root.page === "stats" ? 4 : root.page === "overlay" ? 5 : 3
            ColumnLayout {
                RowLayout {
                    Text { text: root.tr("Автоматический выбор активного профиля"); color: "#e6d5b8"; Layout.fillWidth: true }
                    TacticalSwitch { checked: prototype.autoProfile; onClicked: prototype.setAutoProfile(checked) }
                    MetalButton { text: root.tr("Найти профили"); enabled: !prototype.maintenanceBusy; onClicked: prototype.rescanProfiles() }
                    MetalButton { text: root.tr("Журнал игры"); enabled: !prototype.maintenanceBusy; onClicked: loggingDialog.open() }
                }
                ListView {
                    id: profiles
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 6
                    model: prototype.profiles
                    Text {anchors.centerIn:parent;width:parent.width*.78;text:root.tr("Профили пока не найдены. Автоматический поиск проверяет установленные игры и журналы. Можно указать путь вручную.");wrapMode:Text.WordWrap;horizontalAlignment:Text.AlignHCenter;color:"#bdb4a2";visible:profiles.count===0}
                    ScrollBar.vertical: MetalScrollBar {}
                    delegate: Rectangle {
                        required property var modelData
                        width: profiles.width - 16; height: profileBody.implicitHeight + 20; radius: 6
                        color: prototype.logPath === modelData.path ? "#373026" : "#202524"
                        border.color: prototype.logPath === modelData.path ? "#c09958" : "#4b463b"
                        RowLayout {
                            id: profileBody
                            anchors.fill: parent; anchors.margins: 10
                            ColumnLayout {
                                Layout.fillWidth: true
                                MetalTextField { id: profileName; text: modelData.name; Layout.fillWidth: true }
                                Text { text: modelData.path; textFormat: Text.PlainText; elide: Text.ElideMiddle; Layout.fillWidth: true; color: "#b7ad9b"; font.pixelSize: 11 }
                            }
                            MetalButton { text: root.tr("Переименовать"); onClicked: prototype.renameProfile(modelData.path, profileName.text) }
                            Text { visible: prototype.logPath === modelData.path; text: "✓  " + root.tr("Активен"); color: "#b9d69b"; font.bold: true; Layout.minimumWidth: 75 }
                            MetalButton { visible: prototype.logPath !== modelData.path; text: root.tr("Выбрать"); onClicked: prototype.setLogPath(modelData.path) }
                        }
                    }
                }
                RowLayout {
                    MetalTextField { id: customPath; placeholderText: root.tr("Путь к console_mp.log"); Layout.fillWidth: true }
                    MetalButton { text: root.tr("Добавить"); enabled: customPath.text.trim().length > 0; onClicked: { prototype.setLogPath(customPath.text); customPath.clear() } }
                    AmberButton { text: root.tr("Сохранить настройки"); visible: prototype.settingsWritable; onClicked: prototype.saveSettings() }
                }
            }
            Flickable {
                id: knowledgeScroll
                clip:true;contentWidth:width;contentHeight:knowledgeScrollContent.implicitHeight+8
                boundsBehavior:Flickable.StopAtBounds
                ScrollBar.vertical:MetalScrollBar { parent:knowledgeScroll;anchors.right:knowledgeScroll.right;anchors.top:knowledgeScroll.top;anchors.bottom:knowledgeScroll.bottom }
                ColumnLayout {
                    id: knowledgeScrollContent; width: Math.min(660, knowledgeScroll.width - 16); spacing: 9
                RowLayout {
                    Text { font.bold: true; font.pixelSize: 17; text: root.tr("Локальный словарь"); color: "#e6d5b8"; Layout.fillWidth: true }
                    TacticalSwitch { checked: prototype.knowledgeEnabled; onClicked: prototype.setKnowledgeEnabled(checked) }
                }
                Text { text: root.tr("Версия") + " " + prototype.knowledgeVersion + "  ·  " + root.tr("Записи") + ": " + prototype.knowledgeCount; color: "#e4c291"; font.pixelSize: 19 }
                Text { text: root.tr("Обновления содержат только проверяемые данные словаря, без исполняемого кода."); color: "#c6b79e"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                AmberButton { text: root.tr("Обновить базу знаний"); enabled: prototype.knowledgeWritable && !prototype.maintenanceBusy; onClicked: prototype.refreshKnowledge() }
                Rectangle { Layout.fillWidth: true; height: 1; color: "#494637" }
                Text { text: root.tr("Локальный опыт"); color: "#e4c291"; font.bold: true; font.pixelSize: 17 }
                RowLayout {
                    Text { text: root.tr("Собирать примеры локально"); color: "#e6d5b8"; Layout.fillWidth: true }
                    TacticalSwitch { checked: prototype.experienceCollect; enabled: prototype.experienceAvailable; onClicked: prototype.setExperienceOption("collect", checked) }
                }
                Text { text: root.tr("Перед передачей архива проверьте его содержимое. Автоотправки нет."); color: "#c6b79e"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                RowLayout {
                    MetalButton { text: root.tr("Экспорт ZIP"); enabled: prototype.experienceAvailable; onClicked: exportDialog.open() }
                    MetalButton { text: root.tr("Очистить опыт"); enabled: prototype.experienceAvailable; onClicked: clearDialog.open() }
                }
                Rectangle { Layout.fillWidth: true; height: 1; color: "#494637" }
                Text { text: root.tr("Кэш перевода"); color:"#e4c291"; font.bold: true; font.pixelSize:17 }
                RowLayout {
                    Text { text: root.tr("Дисковый кэш на 7 дней"); color: "#e6d5b8"; Layout.fillWidth: true }
                    TacticalSwitch { checked: prototype.experienceCache; enabled: prototype.experienceAvailable; onClicked: prototype.setExperienceOption("cache", checked) }
                }


            }
            }
            ColumnLayout {
                GridLayout {
                    Layout.fillWidth:true; Layout.maximumWidth:820; columns:2; columnSpacing:32; rowSpacing:5
                    Repeater {
                        model:[{key:"friends",label:"Уведомления о друзьях"},{key:"join",label:"Друг появился"},{key:"leave",label:"Друг покинул сервер"},{key:"move",label:"Возможный переход друга"},{key:"sound",label:"Звук уведомлений"}]
                        delegate:RowLayout {
                            required property var modelData
                            Layout.fillWidth:true
                            Layout.columnSpan: modelData.key === "friends" ? 2 : 1
                            Text {opacity:modelData.key==="friends"||prototype.notifyFriends?1:.55; text:root.tr(modelData.label);color:"#e6d5b8";Layout.fillWidth:true;elide:Text.ElideRight}
                            TacticalSwitch {checked:!!prototype.friendNotificationOptions[modelData.key];enabled:modelData.key==="friends"||prototype.notifyFriends;onClicked:prototype.setFriendNotification(modelData.key,checked)}
                        }
                    }
                }
                Text {text:root.tr("Изменения подтверждаются двумя опросами. Недоступность сервера не считается выходом игрока.");color:"#bcb09a";wrapMode:Text.WordWrap;Layout.fillWidth:true}
                Text {visible:prototype.friendSaveError.length>0;text:prototype.friendSaveError;color:"#e99b83";wrapMode:Text.WordWrap;Layout.fillWidth:true}
                Rectangle { Layout.fillWidth: true; height: 1; color: "#494637" }
                Text { text: root.tr("История уведомлений"); color: "#e4c291"; font.bold: true }
                ListView {
                    id: notices
                    Layout.fillHeight: true; Layout.fillWidth: true; clip: true; spacing: 5
                    model: prototype.notifications
                    delegate: Rectangle {
                        required property string modelData
                        width: notices.width - 8; height: 38; radius: 5; color: "#262a27"
                        Text { anchors.fill: parent; anchors.margins: 9; text: modelData; textFormat: Text.PlainText; color: "#e6d5b8"; elide: Text.ElideRight }
                    }
                    Text { anchors.left: parent.left; anchors.top: parent.top; anchors.topMargin: 10; visible: notices.count === 0; text: root.tr("Новых уведомлений нет"); color: "#b7ad9b" }
                }
            }
            Flickable {
                id: aboutScroll
                clip:true;contentWidth:width;contentHeight:aboutScrollContent.implicitHeight+8
                boundsBehavior:Flickable.StopAtBounds
                ScrollBar.vertical:MetalScrollBar { parent:aboutScroll;anchors.right:aboutScroll.right;anchors.top:aboutScroll.top;anchors.bottom:aboutScroll.bottom }
                ColumnLayout {
                    id: aboutScrollContent; width:Math.min(820, aboutScroll.width-12); anchors.horizontalCenter: parent.horizontalCenter; spacing: 10
                RowLayout {
                    Layout.fillWidth:true;spacing:22
                    Image {source:"command_logo.png";Layout.preferredWidth:230;Layout.preferredHeight:100;fillMode:Image.PreserveAspectFit}
                    ColumnLayout {Layout.fillWidth:true
                        Text {text:"CoD2 Chat Translator";color:"#f5e7c9";font.pixelSize:22;font.bold:true}
                        Text {text:root.tr("Перевод игрового чата и мониторинг серверов Call of Duty 2.");wrapMode:Text.WordWrap;Layout.fillWidth:true;color:"#d6c9ae"}
                        Text {text:prototype.appVersion+" · kriskarter";color:"#d7b77d";font.pixelSize:15}
                        Text {text:root.tr("Неофициальная утилита. Copyright © 2026 kriskarter. Все права защищены.");wrapMode:Text.WordWrap;Layout.fillWidth:true;color:"#bcb09a"}
                        RowLayout {
                            MetalButton {text:"GitHub";onClicked:Qt.openUrlExternally("https://github.com/kriskarter/cod2-chat-translator")}
                            MetalButton {text:root.tr("Поддержка проекта");onClicked:Qt.openUrlExternally("https://github.com/kriskarter/cod2-chat-translator/issues")}
                            MetalButton {text:root.tr("Лицензия");onClicked:Qt.openUrlExternally("https://github.com/kriskarter/cod2-chat-translator/blob/main/COPYRIGHT.md")}
                        }
                    }
                }
                Text { text: root.tr("Изолированная тестовая версия. Стабильная установка не изменяется."); color: "#c6b79e"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Rectangle {height:1;color:"#786342";Layout.fillWidth:true}
                Text {text:root.tr("Канал обновлений")+": Qt Preview / RC · "+(prototype.buildNumber==="source"?root.tr("Из исходного кода"):prototype.buildNumber);color:"#d7b77d";wrapMode:Text.WordWrap;Layout.fillWidth:true}
                Text { text: root.tr("Обновления"); color: "#e4c291"; font.bold: true; font.pixelSize: 17 }
                RowLayout {Layout.fillWidth:true
                    MetalButton {glyph:"icons/refresh.svg";text:root.tr("Проверить обновления");enabled:!prototype.maintenanceBusy;onClicked:prototype.checkUpdates()}
                    MetalButton {text:root.tr("Открыть страницу обновления");visible:prototype.updateAvailable;onClicked:prototype.openUpdate()}
                    AmberButton {text:root.tr("Скачать и проверить");visible:prototype.updateAvailable&&prototype.updateInstallAvailable&&!prototype.updateReady;enabled:!prototype.maintenanceBusy;onClicked:prototype.downloadUpdate()}
                    AmberButton {text:root.tr("Установить");visible:prototype.updateReady;enabled:!prototype.maintenanceBusy;onClicked:updateConfirm.open()}
                    MetalButton {text:root.tr("Отмена");visible:prototype.updateAvailable&&(prototype.maintenanceBusy||prototype.updateReady);onClicked:prototype.discardUpdate()}
                }
                Text {visible:prototype.updateNotes.length>0;text:prototype.updateNotes;textFormat:Text.PlainText;wrapMode:Text.Wrap;Layout.fillWidth:true;color:"#e2d0af"}
                Text { text: prototype.updateMessage; color: "#e6d5b8"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Text { text: root.tr("Стабильный пакет не устанавливается поверх Qt Preview."); color: "#b7ad9b"; wrapMode: Text.WordWrap; Layout.fillWidth: true }

            }
            }
            ColumnLayout {
                RowLayout {
                    Layout.fillWidth: true; Layout.maximumWidth: 820
                    Text { Layout.fillWidth: true; text: root.tr("Скорость перевода"); font.pixelSize: 18; font.bold: true; color: "#e4c291" }
                    MetalButton { text: root.tr("Обновить статистику"); enabled: prototype.experienceAvailable; onClicked: prototype.refreshStats() }
                }
                Text {
                    visible: prototype.observationCount > 0
                    text: root.tr("Сообщений в локальном опыте") + "  ·  " + prototype.observationCount
                    color: "#ebd6ae"; font.pixelSize: 15
                }
                Text {
                    visible: !statsList.count
                    text: root.tr("Нет измерений. Включите локальный опыт и обновите статистику.")
                    color: "#c3bba8"; wrapMode: Text.WordWrap; Layout.fillWidth: true
                }
                ListView {
                    id: statsList; Layout.fillWidth: true; Layout.maximumWidth: 820; Layout.fillHeight: true
                    model: prototype.experienceStats; visible: count > 0; clip: true; spacing: 4
                    ScrollBar.vertical: MetalScrollBar {}
                    delegate: Rectangle {
                        required property var modelData
                        width: statsList.width - 12; height: 52; color: "#252923"; radius: 5
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 10
                            Text { text: modelData.group.split("/").map((part,index) => index === 0 ? root.tr(part) : part).join(" · "); color: "#f5e7c9"; Layout.fillWidth: true; elide: Text.ElideRight }
                            Text { text: root.tr("Замеров") + "  " + modelData.samples; color: "#d7ceb9" }
                            Text { text: root.tr("Медиана") + "  " + modelData.p50_ms + " " + root.tr("мс"); color: "#e4c291" }
                            Text { text: root.tr("95% быстрее") + "  " + modelData.p95_ms + " " + root.tr("мс"); color: "#e4c291" }
                        }
                    }
                }
                Item { visible: !statsList.count; Layout.fillHeight: true }
            }
            Flickable {
                id: hudScroll
                clip: true; contentWidth: width; contentHeight: hudContent.implicitHeight + 4
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: MetalScrollBar { parent: hudScroll; anchors.right: hudScroll.right; anchors.top: hudScroll.top; anchors.bottom: hudScroll.bottom }
                ColumnLayout {
                    id: hudContent; width: hudScroll.width - 15; spacing: 8
                    RowLayout {
                        Text { text: root.tr("Оверлей"); color: "#e4c291"; font.bold: true; Layout.fillWidth: true }
                        TacticalSwitch { checked: prototype.overlay; enabled: prototype.overlayAvailable; onClicked: prototype.toggle("overlay") }
                        MetalButton { text: root.tr("Тест оверлея"); enabled: prototype.overlayAvailable; onClicked: prototype.testHud() }
                        MetalButton { text: root.tr("Очистить"); onClicked: prototype.clearHud() }
                    }
                    Rectangle {
                        id:hudStage
                        Layout.fillWidth:true;Layout.preferredHeight:Math.min(200, Math.max(132, root.height * .38));radius:6;color:"#151b19";border.color:"#686b59";clip:true
                        Image {anchors.fill:parent;source:"art/hud_village.jpg";fillMode:Image.PreserveAspectCrop;opacity:.85;clip:true}
                        Text {anchors.right:parent.right;anchors.top:parent.top;anchors.margins:6;text:root.tr("Перетащите тестовый HUD");style:Text.Outline;styleColor:"#322c23";color:"#fff0d3";font.pixelSize:11}
                        Rectangle {
                            id:hudSample
                            property real editX:0
                            property real editY:0
                            width:Math.max(110,Math.min(parent.width-12,parent.width*prototype.hudPosition.width));height:Math.max(34,Math.min(parent.height-8,parent.height*prototype.hudPosition.height))
                            x:dragArea.pressed?editX:prototype.hudPosition.x*Math.max(0,parent.width-width)
                            y:dragArea.pressed?editY:prototype.hudPosition.y*Math.max(0,parent.height-height)
                            color:Qt.rgba(0,0,0,prototype.preferences.opacity);radius:4;border.color:"#d0af72"
                            Text {anchors.centerIn:parent;text:root.tr("Тест · Сообщение команды");style:Text.Outline;styleColor:"#252722";color:"#f0e7d4";font.pixelSize:Math.min(16,prototype.preferences.font+1);width:parent.width-8;elide:Text.ElideRight;horizontalAlignment:Text.AlignHCenter}
                            MouseArea {
                                id:dragArea;anchors.fill:parent;cursorShape:Qt.SizeAllCursor
                                property real dx
                                property real dy
                                onPressed:mouse=>{hudSample.editX=prototype.hudPosition.x*Math.max(0,hudStage.width-hudSample.width);hudSample.editY=prototype.hudPosition.y*Math.max(0,hudStage.height-hudSample.height);dx=mouse.x;dy=mouse.y}
                                onPositionChanged:mouse=>{if(pressed){hudSample.editX=Math.max(0,Math.min(hudStage.width-hudSample.width,hudSample.editX+mouse.x-dx));hudSample.editY=Math.max(0,Math.min(hudStage.height-hudSample.height,hudSample.editY+mouse.y-dy))}}
                                onReleased:prototype.setHudPositionNormalized(hudSample.editX/Math.max(1,hudStage.width-hudSample.width),hudSample.editY/Math.max(1,hudStage.height-hudSample.height))
                            }
                        }
                    }
                    GridLayout {
                        columns: 3; Layout.alignment: Qt.AlignLeft
                        MetalButton { text: root.tr("Только текст"); selected: prototype.hudPreset === "text"; onClicked: prototype.applyHudPreset("text") }
                        MetalButton { text: root.tr("Минимальный"); selected: prototype.hudPreset === "minimal"; onClicked: prototype.applyHudPreset("minimal") }
                        MetalButton { text: root.tr("Читаемый"); selected: prototype.hudPreset === "readable"; onClicked: prototype.applyHudPreset("readable") }
                    }
                    GridLayout {
                        Layout.fillWidth: true; columns: hudContent.width < 760 ? 1 : 2; columnSpacing: 18; rowSpacing: 4
                        Repeater {
                            model: [{k:"font",label:"Размер текста",lo:8,hi:20,step:1},{k:"ttl",label:"Время показа",lo:1,hi:120,step:1},{k:"opacity",label:"Прозрачность фона",lo:0,hi:.9,step:.05},{k:"messages",label:"Количество сообщений",lo:1,hi:10,step:1},{k:"width",label:"Ширина",lo:200,hi:1200,step:10},{k:"height",label:"Высота",lo:46,hi:600,step:10}]
                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Text { text: root.tr(modelData.label); color: "#f5e7c9"; Layout.preferredWidth: 150; Layout.minimumWidth: 120; elide: Text.ElideRight }
                                MetalSlider { from: modelData.lo; to: modelData.hi; stepSize: modelData.step; value: prototype.preferences[modelData.k]; Layout.fillWidth: true; onMoved: prototype.setHudValue(modelData.k,value) }
                                Text { text: modelData.k === "opacity" ? Math.round(prototype.preferences.opacity*100)+"%" : Math.round(prototype.preferences[modelData.k]) + (modelData.k === "ttl" ? " " + root.tr("с") : ""); color: "#e4c291"; Layout.preferredWidth: 42 }
                            }
                        }
                        Repeater {
                            model: [{k:"fade",label:"Плавное исчезновение"},{k:"compact",label:"Компактный фон"},{k:"onlyMessages",label:"Фон только с сообщениями"},{k:"autoHeight",label:"Автоматическая высота"}]
                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Text { text: root.tr(modelData.label); color: "#f5e7c9"; Layout.fillWidth: true; elide: Text.ElideRight }
                                TacticalSwitch { checked: !!prototype.preferences[modelData.k]; onClicked: prototype.setPreference(modelData.k,checked) }
                            }
                        }
                    }
                    RowLayout {
                        Text { text: "X"; color: "#e4c291" }
                        MetalTextField { id: hudX; text: String(prototype.preferences.x); Layout.preferredWidth: 90; validator: IntValidator { bottom: -6000; top: 6000 } }
                        Text { text: "Y"; color: "#e4c291" }
                        MetalTextField { id: hudY; text: String(prototype.preferences.y); Layout.preferredWidth: 90; validator: IntValidator { bottom: -6000; top: 6000 } }
                        MetalButton { text: root.tr("Применить"); enabled: hudX.acceptableInput && hudY.acceptableInput; onClicked: { prototype.setHudValue("x",Number(hudX.text)); prototype.setHudValue("y",Number(hudY.text)) } }
                        MetalButton { text: root.tr("Сбросить позицию"); onClicked: prototype.resetHudPosition() }
                        Item { Layout.fillWidth: true }

                    }
                }
            }
        }
        RowLayout {visible:["overlay","knowledge","notifications"].indexOf(root.page)>=0&&prototype.settingsWritable;Layout.fillWidth:true;Item {Layout.fillWidth:true} AmberButton {text:root.tr("Сохранить настройки");onClicked:prototype.saveSettings()} }
        
    }
}
