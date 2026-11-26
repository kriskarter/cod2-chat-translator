import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
MetalPanel {
    id: root
    objectName:keyName.toLowerCase()+"Card"
    property string keyName
    property string heading
    property string description
    property bool controlsEnabled: true
    property bool active
    property bool compact
    property url artwork
    property bool live: false
    signal manual()
    signal toggled()
    clip: true
    Image {
        anchors.fill: parent; anchors.margins: 8
        source: root.artwork; fillMode: Image.PreserveAspectCrop; opacity: .95
    }
    Rectangle {
        anchors.fill: parent; anchors.margins: 8
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "#d5171a1b" }
            GradientStop { position: .68; color: "#50171919" }
            GradientStop { position: 1; color: "#30171919" }
        }
    }
    RowLayout {
        anchors.fill: parent; anchors.margins: root.compact ? 9 : 18
        spacing: root.compact ? 5 : 17
        KeycapButton {
            objectName: root.keyName.toLowerCase() + "Key"
            text: root.keyName; active: root.active; enabled: root.controlsEnabled
            Layout.preferredWidth: root.compact ? Math.min(60, Math.max(44, root.height - 24)) : 114
            Layout.preferredHeight: width
            onClicked: root.toggled()
        }
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            Item { Layout.fillHeight: true }
            Text { text: root.heading; color: "#fff0d1"; font.pixelSize: root.compact ? 14 : 22; font.bold: true; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight; Layout.fillWidth: true }
            Text { visible: !root.live; text: root.description; color: "#e8d4b3"; font.pixelSize: root.compact ? 11 : 13; elide: Text.ElideRight; Layout.fillWidth: true }
            Loader {
                active:root.live; visible:active; Layout.fillWidth:true; Layout.minimumWidth:0
                sourceComponent: RowLayout {
                    spacing:4
                    LanguageSelector {
                        objectName:root.keyName.toLowerCase()+"Language"; model:root.keyName==="F8"?prototype.languages:prototype.outgoingLanguages
                        textRole:"label";valueRole:"code";Layout.fillWidth:true;Layout.minimumWidth:54
                        currentIndex:indexOfValue(root.keyName==="F8"?prototype.targetLanguage:prototype.outgoingSource)
                        onActivated:if(root.keyName==="F8")prototype.setTargetLanguage(currentValue);else prototype.setOutgoingRoute(currentValue,prototype.outgoingTarget)
                    }
                    Text { visible:root.keyName==="F9";text:"→";color:"#d9b477" }
                    LanguageSelector {
                        objectName:root.keyName.toLowerCase()+"Target"; visible:root.keyName==="F9";model:prototype.outgoingLanguages;textRole:"label";valueRole:"code";Layout.fillWidth:true;Layout.minimumWidth:54
                        currentIndex:indexOfValue(prototype.outgoingTarget)
                        onActivated:prototype.setOutgoingRoute(prototype.outgoingSource,currentValue)
                    }
                }
            }
            RowLayout {
                Rectangle { width: 8; height: 8; radius: 4; color: root.active ? "#b0db84" : "#847c6d" }
                Text { text: !root.controlsEnabled ? (prototype.uiLanguage, prototype.trText("Не перенесён")) : root.active ? (prototype.uiLanguage, prototype.trText("Активен")) : (prototype.uiLanguage, prototype.trText("Выключен")); color: root.active ? "#b0db84" : "#bcb09a"; font.pixelSize: 12 }
            }
            MetalButton { objectName:root.keyName==="F9"?"manual_outgoing":"unused_manual"; visible:root.live&&root.keyName==="F9";text:(prototype.uiLanguage,prototype.trText("Ручной перевод"));implicitHeight:26;Layout.minimumWidth:0;Layout.maximumWidth:parent.width;Layout.alignment:Qt.AlignLeft;onClicked:root.manual() }
            Item { Layout.fillHeight: true }
        }
        TacticalSwitch { objectName: root.keyName.toLowerCase() + "Switch"; checked: root.active; enabled: root.controlsEnabled; Accessible.name: root.heading; onClicked: root.toggled() }
    }
}
