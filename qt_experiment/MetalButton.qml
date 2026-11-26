import QtQuick
import QtQuick.Controls
Button {
 id: root
 property string surface: "metal"
 property bool selected: false
 property url glyph
 property bool gold: surface === "amber" || (surface === "nav" && selected)
 font.family: "Segoe UI"; font.pixelSize: 13; font.bold: true
 implicitHeight: 36; implicitWidth: Math.max(68, labelText.implicitWidth + (ico.visible ? 22 : 0) + 24)
 padding: 8; hoverEnabled: true; focusPolicy: Qt.StrongFocus
 contentItem: Item {
  Row {
   anchors.centerIn: parent; spacing: 6
   Image { id: ico; source: root.glyph; visible: root.glyph.toString().length > 0; width: visible ? 16 : 0; height: 16; opacity: root.enabled ? 1 : .45; anchors.verticalCenter: parent.verticalCenter }
   Text { id: labelText; text: root.text; font: root.font; color: root.enabled ? "#fff0d3" : "#999385"; width: Math.min(implicitWidth, Math.max(1,root.availableWidth-(ico.visible?22:0))); elide: Text.ElideRight; anchors.verticalCenter: parent.verticalCenter }
  }
 }
 background: Item {
  BorderImage {
   anchors.fill:parent
   source:"art/"+(root.gold?"amber_button":"metal_button")+(!root.enabled?"_disabled":root.down?"_pressed":root.activeFocus?"_focused":root.hovered?"_hover":"")+".png"
   border.left:20;border.right:20;border.top:18;border.bottom:18
  }
  Rectangle {anchors.fill:parent;anchors.margins:1;radius:4;color:"transparent";border.color:root.activeFocus?"#f0c784":"transparent"}
 }
 ToolTip.visible: hovered && labelText.truncated
 ToolTip.text: text
}
