import QtQuick
import QtQuick.Controls
ComboBox {
 id:root
 font.pixelSize:12; implicitHeight:30; implicitWidth:130; leftPadding:9; rightPadding:24
 palette.text:"#f5e7c9"; palette.base:"#202522"; palette.window:"#202522"; palette.highlight:"#72552d"; palette.highlightedText:"#fff1d3"
 contentItem:Text { text:root.displayText; color:"#f5e7c9"; font:root.font; verticalAlignment:Text.AlignVCenter; elide:Text.ElideRight }
 background:Rectangle { radius:4; color:root.hovered?"#363a34":"#262b27"; border.color:root.activeFocus?"#e8b96c":"#746953" }
 indicator:Image { x:root.width-width-6; anchors.verticalCenter:parent.verticalCenter; width:16;height:16;source:"../assets/ui_wwii/premium_combo_arrow.png" }
}