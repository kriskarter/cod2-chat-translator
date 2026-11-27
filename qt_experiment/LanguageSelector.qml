import QtQuick
import QtQuick.Controls
ComboBox {
 id:root
 property bool inlineRoute:false
 readonly property bool subtle: inlineRoute && !hovered && !activeFocus && !popup.visible
 hoverEnabled:true; font.pixelSize:inlineRoute?15:12; implicitHeight:30; implicitWidth:130; leftPadding:inlineRoute?3:9; rightPadding:inlineRoute?15:24
 palette.text:"#f5e7c9"; palette.base:"#202522"; palette.window:"#202522"; palette.highlight:"#72552d"; palette.highlightedText:"#fff1d3"
 contentItem:Text { text:root.displayText; color:"#f5e7c9"; font:root.font; verticalAlignment:Text.AlignVCenter; elide:Text.ElideRight }
 background: Rectangle {
        Image { anchors.fill: parent; anchors.margins: 2; source: "reference_art/field.webp"; fillMode: Image.Tile; opacity: .65 }
 opacity:root.subtle?0:1; radius:4; color:root.hovered?"#363a34":"#262b27"; border.color:root.activeFocus?"#e8b96c":"#746953" }
 indicator:Image { opacity:root.subtle?.5:1; x:root.width-width-6; anchors.verticalCenter:parent.verticalCenter; width:16;height:16;source:"../assets/ui_wwii/premium_combo_arrow.png" }
}