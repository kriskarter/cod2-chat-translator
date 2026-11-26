import QtQuick
import QtQuick.Controls
MenuItem {
 id:root
 implicitHeight:34
 padding:8
 font.pixelSize:13
 contentItem:Text {text:root.text;font:root.font;color:root.enabled?"#e9d8b7":"#817e74";verticalAlignment:Text.AlignVCenter;elide:Text.ElideRight}
 background:Rectangle {radius:3;color:root.highlighted&&root.enabled?"#594529":"transparent";border.color:root.highlighted&&root.enabled?"#ad8951":"transparent"}
}