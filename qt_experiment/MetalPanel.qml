import QtQuick
Item {
 id: root
 property url texture: "command_frame.png"
 implicitHeight: 64
 Rectangle { anchors.fill: parent; anchors.topMargin: 2; color: "#0b0d0d"; radius: 8 }
 Rectangle {
  anchors.fill: parent; anchors.bottomMargin: 2; radius: 7; border.color: "#82745c"; border.width: 1
  gradient: Gradient { GradientStop {position:0;color:"#30322e"} GradientStop {position:.23;color:"#222522"} GradientStop {position:1;color:"#191c1b"} }
 }
 Image { anchors.fill: parent; anchors.margins: 3; source:"../assets/ui_wwii/body_backdrop.png"; sourceSize.width:640; fillMode: Image.PreserveAspectCrop; opacity:.10; clip:true }
 Rectangle { x:7; y:2; width:Math.max(0,parent.width-14); height:1; color:"#c0ac83"; opacity:.35 }
}