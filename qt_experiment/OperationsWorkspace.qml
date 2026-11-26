import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
MetalPanel {
    id: root
    property string page: "profiles"
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
        id: clearDialog; title: root.tr("Очистить опыт"); anchors.centerIn: parent
        standardButtons: Dialog.NoButton
        ColumnLayout {
            Text { text: root.tr("Удалить только локальный опыт и кэш?"); color: "#f5e7c9" }
            RowLayout {
                MetalButton { text: root.tr("Отмена"); onClicked: clearDialog.close() }
                AmberButton { text: root.tr("Удалить"); onClicked: { prototype.clearExperience(); clearDialog.close() } }
            }
        }
    }
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 24; spacing: 10
        Text { text: root.tr(({profiles:"Профили",knowledge:"База знаний",notifications:"Уведомления",about:"О программе",stats:"Статистика",overlay:"Настройки оверлея"})[root.page] || (prototype.uiLanguage, prototype.trText("О программе"))); font.pixelSize: 23; font.bold: true; color: "#f5e7c9" }
        Rectangle { Layout.fillWidth: true; height: 1; color: "#786342" }
        StackLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            currentIndex: root.page === "profiles" ? 0 : root.page === "knowledge" ? 1 : root.page === "notifications" ? 2 : root.page === "stats" ? 4 : root.page === "overlay" ? 5 : 3
            ColumnLayout {
                RowLayout {
                    Text { text: root.tr("Автоматический выбор активного профиля"); color: "#e6d5b8"; Layout.fillWidth: true }
                    TacticalSwitch { checked: prototype.autoProfile; onClicked: prototype.setAutoProfile(checked) }
                    MetalButton { text: root.tr("Найти профили"); enabled: !prototype.maintenanceBusy; onClicked: prototype.rescanProfiles() }
                }
                ListView {
                    id: profiles
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 6
                    model: prototype.profiles
                    ScrollBar.vertical: MetalScrollBar {}
                    delegate: Rectangle {
                        required property var modelData
                        width: profiles.width - 16; height: 62; radius: 6
                        color: prototype.logPath === modelData.path ? "#373026" : "#202524"
                        border.color: prototype.logPath === modelData.path ? "#c09958" : "#4b463b"
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 8
                            ColumnLayout {
                                Layout.fillWidth: true
                                MetalTextField { id: profileName; text: modelData.name; Layout.fillWidth: true }
                                Text { text: modelData.path; textFormat: Text.PlainText; elide: Text.ElideMiddle; Layout.fillWidth: true; color: "#b7ad9b"; font.pixelSize: 11 }
                            }
                            MetalButton { text: root.tr("Переименовать"); onClicked: prototype.renameProfile(modelData.path, profileName.text) }
                            AmberButton { text: root.tr("Выбрать"); onClicked: prototype.setLogPath(modelData.path) }
                        }
                    }
                }
                RowLayout {
                    MetalTextField { id: customPath; placeholderText: root.tr("Путь к console_mp.log"); Layout.fillWidth: true }
                    MetalButton { text: root.tr("Добавить"); enabled: customPath.text.trim().length > 0; onClicked: { prototype.setLogPath(customPath.text); customPath.clear() } }
                    AmberButton { text: root.tr("Сохранить настройки"); visible: prototype.settingsWritable; onClicked: prototype.saveSettings() }
                }
            }
            ColumnLayout {
                RowLayout {
                    Text { text: root.tr("Локальный словарь"); color: "#e6d5b8"; Layout.fillWidth: true }
                    TacticalSwitch { checked: prototype.knowledgeEnabled; onClicked: prototype.setKnowledgeEnabled(checked) }
                }
                Text { text: root.tr("Версия") + " " + prototype.knowledgeVersion + "  ·  " + root.tr("Записи") + ": " + prototype.knowledgeCount; color: "#e4c291"; font.pixelSize: 19 }
                Text { text: root.tr("Обновления содержат только проверяемые данные словаря, без исполняемого кода."); color: "#c6b79e"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                AmberButton { text: root.tr("Обновить базу знаний"); enabled: prototype.knowledgeWritable && !prototype.maintenanceBusy; onClicked: prototype.refreshKnowledge() }
                Text { text: root.tr("Локальный опыт"); color: "#e4c291"; font.bold: true; font.pixelSize: 17 }
                RowLayout {
                    Text { text: root.tr("Собирать примеры локально"); color: "#e6d5b8"; Layout.fillWidth: true }
                    TacticalSwitch { checked: prototype.experienceCollect; enabled: prototype.experienceAvailable; onClicked: prototype.setExperienceOption("collect", checked) }
                }
                RowLayout {
                    Text { text: root.tr("Дисковый кэш на 7 дней"); color: "#e6d5b8"; Layout.fillWidth: true }
                    TacticalSwitch { checked: prototype.experienceCache; enabled: prototype.experienceAvailable; onClicked: prototype.setExperienceOption("cache", checked) }
                }
                Text { text: root.tr("Перед передачей архива проверьте его содержимое. Автоотправки нет."); color: "#c6b79e"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                RowLayout {
                    MetalButton { text: root.tr("Экспорт ZIP"); enabled: prototype.experienceAvailable; onClicked: exportDialog.open() }
                    MetalButton { text: root.tr("Очистить опыт"); enabled: prototype.experienceAvailable; onClicked: clearDialog.open() }
                }
                Item { Layout.fillHeight: true }
            }
            ColumnLayout {
                RowLayout {
                    Text { text: root.tr("Сообщать о появлении друзей в игре"); color: "#e6d5b8"; Layout.fillWidth: true }
                    TacticalSwitch { checked: prototype.notifyFriends; onClicked: prototype.setNotifyFriends(checked) }
                }
                ListView {
                    id: notices
                    Layout.fillHeight: true; Layout.fillWidth: true; clip: true; spacing: 5
                    model: prototype.notifications
                    delegate: Rectangle {
                        required property string modelData
                        width: notices.width - 8; height: 38; radius: 5; color: "#262a27"
                        Text { anchors.fill: parent; anchors.margins: 9; text: modelData; textFormat: Text.PlainText; color: "#e6d5b8"; elide: Text.ElideRight }
                    }
                    Text { anchors.centerIn: parent; visible: notices.count === 0; text: root.tr("Новых уведомлений нет"); color: "#b7ad9b" }
                }
            }
            ColumnLayout {
                Text { text: "CoD2 Chat Translator · Qt Preview"; color: "#f5e7c9"; font.pixelSize: 20; font.bold: true }
                Text { text: root.tr("Изолированная тестовая версия. Стабильная установка не изменяется."); color: "#c6b79e"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Text { text: root.tr("Обновления"); color: "#e4c291"; font.bold: true; font.pixelSize: 17 }
                MetalButton { text: root.tr("Проверить обновления"); enabled: !prototype.maintenanceBusy; onClicked: prototype.checkUpdates() }
                AmberButton { text: root.tr("Открыть страницу обновления"); visible: prototype.updateAvailable; onClicked: prototype.openUpdate() }
                Text { text: prototype.updateMessage; color: "#e6d5b8"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Text { text: root.tr("Стабильный пакет не устанавливается поверх Qt Preview."); color: "#b7ad9b"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Item { Layout.fillHeight: true }
            }
            ColumnLayout {
                MetalButton { text: root.tr("Обновить статистику"); enabled: prototype.experienceAvailable; onClicked: prototype.refreshStats() }
                ListView {
                    id: statsList; Layout.fillWidth: true; Layout.fillHeight: true; model: prototype.experienceStats; clip: true
                    delegate: Rectangle {
                        required property var modelData
                        width: statsList.width; height: 40; color: "#232725"; radius: 4
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 8
                            Text { text: modelData.group; color: "#f5e7c9"; Layout.fillWidth: true }
                            Text { text: "n=" + modelData.samples + " · p50 " + modelData.p50_ms + " ms · p95 " + modelData.p95_ms + " ms"; color: "#d4a75e" }
                        }
                    }
                }
            }
            ColumnLayout {
                RowLayout {
                    Text { text: root.tr("Оверлей"); color: "#f5e7c9"; Layout.fillWidth: true }
                    TacticalSwitch { checked: prototype.overlay; enabled: prototype.overlayAvailable; onClicked: prototype.toggle("overlay") }
                }
                RowLayout {
                    Text { text: root.tr("Размер текста"); color: "#f5e7c9"; Layout.preferredWidth: 180 }
                    Slider { from: 8; to: 28; stepSize: 1; value: prototype.preferences.font; Layout.fillWidth: true; onMoved: prototype.setHudValue("font", value) }
                    Text { text: prototype.preferences.font; color: "#e4c291" }
                }
                RowLayout {
                    Text { text: root.tr("Время показа"); color: "#f5e7c9"; Layout.preferredWidth: 180 }
                    Slider { from: 1; to: 120; stepSize: 1; value: prototype.preferences.ttl; Layout.fillWidth: true; onMoved: prototype.setHudValue("ttl", value) }
                    Text { text: prototype.preferences.ttl + " s"; color: "#e4c291" }
                }
                RowLayout {
                    Text { text: root.tr("Прозрачность фона"); color: "#f5e7c9"; Layout.preferredWidth: 180 }
                    Slider { from: 0; to: .9; stepSize: .05; value: prototype.preferences.opacity; Layout.fillWidth: true; onMoved: prototype.setHudValue("opacity", value) }
                    Text { text: Math.round(prototype.preferences.opacity * 100) + "%"; color: "#e4c291" }
                }
                AmberButton { text: root.tr("Сохранить настройки"); visible: prototype.settingsWritable; onClicked: prototype.saveSettings() }
                Item { Layout.fillHeight: true }
            }
        }
        Text { text: prototype.translationStatus; color: "#d4a75e"; elide: Text.ElideRight; Layout.fillWidth: true }
    }
}
