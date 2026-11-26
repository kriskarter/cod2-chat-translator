import QtQuick
MetalButton {
 id:root
 surface:"nav"
 font.bold:selected
 background:Item {
  Rectangle {anchors.fill:parent;radius:4;visible:root.selected||root.hovered||root.activeFocus;color:root.selected?"#79552a":root.down?"#383a33":"#343630";border.color:root.activeFocus?"#e1ba78":root.selected?"#c69a55":"#6e6452"}
  BorderImage {anchors.fill:parent;anchors.margins:1;source:"../assets/ui_wwii/premium_nav_active.png";border.left:8;border.right:8;border.top:5;border.bottom:5;opacity:root.selected?.92:0}
  Rectangle {anchors.bottom:parent.bottom;anchors.left:parent.left;anchors.right:parent.right;anchors.margins:3;height:2;color:"#e8b765";visible:root.selected}
  Rectangle {anchors.right:parent.right;anchors.verticalCenter:parent.verticalCenter;height:parent.height*.66;width:1;color:"#686052";opacity:root.selected?0:.55}
 }
}
