import QtQuick
import QtQuick.Controls
ScrollBar {
 id: root
 policy: ScrollBar.AsNeeded; implicitWidth: 9; padding: 2
 background: Rectangle { radius:4; color: "#141716" }
 contentItem: Rectangle { radius:3; color:root.pressed?"#d4b77a":root.hovered?"#ac9874":"#777366"; opacity:root.size < 1 ? 1 : 0 }
}