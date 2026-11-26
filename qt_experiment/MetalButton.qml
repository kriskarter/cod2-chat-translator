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
 background: Rectangle {
  radius: 5; border.width: 1; border.color: root.activeFocus ? "#f3cd8b" : root.gold && root.enabled ? "#cda35e" : root.hovered ? "#a28b66" : "#777064"
  gradient: Gradient {
   GradientStop { position: 0; color: !root.enabled ? "#353631" : root.gold ? (root.down ? "#73501e" : "#b28746") : root.down ? "#252826" : root.hovered ? "#575750" : "#444640" }
   GradientStop { position: .47; color: !root.enabled ? "#282b29" : root.gold ? "#775122" : "#343632" }
   GradientStop { position: 1; color: root.gold && root.enabled ? "#392a18" : "#202321" }
  }
  Rectangle { x: 5; y: 2; width: Math.max(0,parent.width-10); height: 1; color: root.gold ? "#e8bc73" : "#77776a"; opacity: root.enabled ? .65 : .2 }
 }
 ToolTip.visible: hovered && labelText.truncated
 ToolTip.text: text
}