import QtQuick
import QtQuick.Controls
Slider {
 id:root
 implicitHeight:28
 background: Rectangle {
  x:root.leftPadding; y:root.topPadding+root.availableHeight/2-height/2; width:root.availableWidth; height:6; radius:3; color:"#111513"; border.color:"#5b5c51"
  Rectangle { width:root.visualPosition*parent.width; height:parent.height; radius:3; color:"#b28b4b" }
 }
 handle: Rectangle { x:root.leftPadding+root.visualPosition*(root.availableWidth-width); y:root.topPadding+root.availableHeight/2-height/2; width:16;height:16;radius:8;border.color:root.activeFocus?"#fff0b4":"#c7a66d"; gradient:Gradient { GradientStop {position:0;color:"#c6b89c"} GradientStop {position:1;color:"#6e6149"} } }
}