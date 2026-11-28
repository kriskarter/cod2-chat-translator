import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Button {
 id:root
 property int count:0
 signal openFriends()
 objectName:"friends_indicator"
 implicitWidth: content.implicitWidth+18; implicitHeight:30
 enabled:prototype.serverManagementAvailable
 hoverEnabled:true
 padding:0
 background:Rectangle {radius:5;color:root.down?"#263322":root.hovered?"#293528":"#141917";border.color:root.activeFocus?"#d9bc80":"#626b49"}
 contentItem:Item {
  RowLayout {id:content;anchors.centerIn:parent;spacing:6
   Image {source:"reference_art/friends.png";Layout.preferredWidth:19;Layout.preferredHeight:19}
   Text {text:(prototype.uiLanguage,prototype.trText("Друзья в игре: "))+root.count;color:"#b5da8c";font.pixelSize:root.height>=30?14:12;font.bold:true}
   Text {text:"⌄";color:"#d5be8c";font.pixelSize:13}
  }
 }
 onClicked:openFriends()
}