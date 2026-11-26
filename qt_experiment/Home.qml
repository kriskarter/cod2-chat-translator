import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    visible: true
    width: 1366; height: 768
    minimumWidth: 900; minimumHeight: 620
    title: "CoD2 Chat Translator — Qt Quick comparison"
    color: "#111313"
    property color ink: "#f5e7c9"
    property color amber: "#d4a75e"
    property bool compact: width < 1100

    component SteelPanel: Rectangle {
        radius: 9
        color: "#1a1c1b"
        border.width: 1
        border.color: "#aa8854"
        Rectangle { anchors.fill: parent; anchors.margins: 4; radius: 7; color: "transparent"; border.color: "#51432f" }
    }
    component MetalButton: Button {
        id: btn
        font.family: "Segoe UI"
        font.pixelSize: 14
        font.bold: true
        palette.buttonText: "#f2dcaf"
        background: Rectangle {
            radius: 5
            border.width: 1
            border.color: btn.hovered ? "#efc47e" : "#91724a"
            gradient: Gradient {
                GradientStop { position: 0; color: btn.down ? "#342718" : btn.hovered ? "#9d7040" : "#554735" }
                GradientStop { position: 1; color: btn.down ? "#161616" : "#1b1d1c" }
            }
        }
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Item {
            Layout.fillWidth: true; Layout.preferredHeight: Math.max(135, Math.min(190, window.height * .245))
            Image { anchors.fill: parent; source: "../assets/ui_wwii/premium_hero.png"; fillMode: Image.PreserveAspectCrop; cache: true }
            Image { anchors.centerIn: parent; height: parent.height * .77; width: height * 3.2; source: "../assets/ui_wwii/premium_logo.png"; fillMode: Image.PreserveAspectFit; cache: true }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 48
            color: "#191b1a"; border.color: "#68573c"
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 20; spacing: 8
                Repeater {
                    model: ["⌂  Главная", "▤  Серверы", "⚙  Настройки", "▥  Логи / История", "ⓘ  О программе"]
                    delegate: MetalButton { text: modelData; Layout.preferredWidth: index === 3 ? 175 : 145; Layout.fillHeight: true; onClicked: prototype.request("nav:" + modelData) }
                }
                Item { Layout.fillWidth: true }
            }
        }
        RowLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            Layout.leftMargin: 17; Layout.rightMargin: 17; Layout.topMargin: 12; Layout.bottomMargin: 8
            spacing: 14
            ColumnLayout {
                Layout.fillWidth: true; Layout.fillHeight: true
                Layout.horizontalStretchFactor: 43
                spacing: 12
                Repeater {
                    model: ["f8", "f9"]
                    delegate: SteelPanel {
                        id: card
                        required property string modelData
                        Layout.fillWidth: true; Layout.fillHeight: true
                        clip: true
                        Image { anchors.fill: parent; anchors.margins: 5; source: card.modelData === "f8" ? "../assets/ui_premium/translation_card_source.jpg" : "../assets/ui_premium/tank_card.png"; fillMode: Image.PreserveAspectCrop; opacity: .46 }
                        RowLayout {
                            anchors.fill: parent; anchors.margins: window.compact ? 8 : 17; spacing: window.compact ? 7 : 16
                            MetalButton {
                                text: card.modelData.toUpperCase(); font.pixelSize: 29; font.italic: true
                                Layout.preferredWidth: window.compact ? 72 : 94; Layout.preferredHeight: window.compact ? 72 : 90
                                onClicked: prototype.toggle(card.modelData)
                            }
                            ColumnLayout {
                                Layout.fillWidth: true; Layout.fillHeight: true
                                Text { text: card.modelData === "f8" ? "Входящий перевод" : "Исходящий перевод"; color: ink; font.pixelSize: window.compact ? 13 : 21; font.bold: true; elide: Text.ElideRight; Layout.fillWidth: true }
                                Text { text: card.modelData === "f8" ? "Чат → русский" : "Русский → English"; color: "#e8d4b3"; font.pixelSize: window.compact ? 11 : 13 }
                                Item { Layout.fillHeight: true }
                                Text { text: (card.modelData === "f8" ? prototype.f8 : prototype.f9) ? "●  Активен" : "○  Выкл"; color: amber; font.pixelSize: window.compact ? 11 : 13 }
                            }
                            MetalButton {
                                text: (card.modelData === "f8" ? prototype.f8 : prototype.f9) ? "✓ Активен" : "○ Выкл"
                                visible: !window.compact
                                Layout.preferredWidth: window.compact ? 80 : 105
                                onClicked: prototype.toggle(card.modelData)
                            }
                        }
                    }
                }
            }
            SteelPanel {
                Layout.fillWidth: true; Layout.fillHeight: true
                Layout.horizontalStretchFactor: 57
                Layout.minimumWidth: 450
                Image { anchors.fill: parent; anchors.margins: 4; source: "../assets/ui_wwii/premium_server.png"; fillMode: Image.Stretch; opacity: .27 }
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 15; spacing: 5
                    RowLayout {
                        Text { text: "♙  Мониторинг серверов"; color: ink; font.pixelSize: 21; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Text { text: "Друзья в игре: 0"; color: "#b4de82"; font.pixelSize: 13 }
                    }
                    Text { text: "Сервер                                  Карта               Игроки       Пинг       Статус"; color: "#bcb09a"; font.pixelSize: 11 }
                    Repeater {
                        model: prototype.rows
                        delegate: Rectangle {
                            id: serverRow
                            required property var modelData
                            Layout.fillWidth: true; Layout.preferredHeight: 35
                            color: prototype.selected === modelData.address ? "#594126" : "#1b1d1d"
                            border.color: prototype.selected === modelData.address ? "#dcb16b" : "#4d4539"
                            RowLayout {
                                anchors.fill: parent; anchors.leftMargin: 9; anchors.rightMargin: 9; spacing: 7
                                Text { text: "★  " + serverRow.modelData.name; Layout.fillWidth: true; color: ink; elide: Text.ElideRight; font.pixelSize: 13 }
                                Text { text: serverRow.modelData.map; Layout.preferredWidth: 90; color: ink; font.pixelSize: 12; elide: Text.ElideRight }
                                Text { text: serverRow.modelData.population; Layout.preferredWidth: 55; color: ink; font.pixelSize: 12 }
                                Text { text: serverRow.modelData.ping; Layout.preferredWidth: 55; color: "#add880"; font.pixelSize: 12 }
                                Text { text: serverRow.modelData.state; Layout.preferredWidth: 58; color: serverRow.modelData.state === "online" ? "#a9d978" : "#bcb8ad"; font.pixelSize: 12 }
                            }
                            MouseArea { anchors.fill: parent; onClicked: prototype.select(serverRow.modelData.address) }
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight: 75
                        color: "#151717"; border.color: "#68573c"; radius: 4
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 6; spacing: 3
                            Text { text: "♟  Игроки на сервере"; color: amber; font.pixelSize: 13 }
                            ListView {
                                Layout.fillWidth: true; Layout.fillHeight: true
                                clip: true; model: prototype.players
                                delegate: Rectangle {
                                    id: playerRow
                                    required property int index
                                    required property var modelData
                                    width: ListView.view.width; height: 23
                                    color: index % 2 ? "#171919" : "#202221"
                                    RowLayout {
                                        anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10
                                        Text { text: playerRow.modelData.richName; textFormat: Text.RichText; color: "#efcf9b"; Layout.fillWidth: true; font.pixelSize: 12 }
                                        Text { text: playerRow.modelData.score; color: ink; Layout.preferredWidth: 65; font.pixelSize: 12 }
                                        Text { text: playerRow.modelData.ping; color: "#b8dc89"; Layout.preferredWidth: 55; font.pixelSize: 12 }
                                    }
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        MetalButton { text: "＋ Добавить сервер"; Layout.fillWidth: true; onClicked: prototype.request("add_server") }
                        MetalButton { text: "⟳ Обновить"; Layout.fillWidth: true; onClicked: prototype.request("refresh") }
                        MetalButton { text: "▶ Подключиться"; Layout.fillWidth: true; onClicked: prototype.request("connect") }
                    }
                }
            }
        }
        SteelPanel {
            Layout.fillWidth: true; Layout.preferredHeight: 82
            Layout.leftMargin: 17; Layout.rightMargin: 17; Layout.bottomMargin: 8
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 25; anchors.rightMargin: 25; spacing: 22
                MetalButton { text: (prototype.overlay ? "● " : "○ ") + "Оверлей"; Layout.fillWidth: true; onClicked: prototype.toggle("overlay") }
                MetalButton { text: (prototype.smart ? "● " : "○ ") + "Smart Engine"; Layout.fillWidth: true; onClicked: prototype.toggle("smart") }
                Text { text: "✓  Статус системы: готова"; color: "#b0db84"; font.bold: true; font.pixelSize: 15; Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter }
            }
        }
    }
}
