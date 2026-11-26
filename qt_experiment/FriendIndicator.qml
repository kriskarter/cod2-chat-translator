import QtQuick
import QtQuick.Layouts
Rectangle {
 id:root
 property int count:0
 implicitWidth: content.implicitWidth+18; implicitHeight:30; radius:5; color:"#141917";border.color:"#626b49"
 RowLayout { id:content;anchors.centerIn:parent;spacing:6
  Image { source:"icons/friends.svg";Layout.preferredWidth:19;Layout.preferredHeight:19 }
  Text { text:(prototype.uiLanguage,prototype.trText("Друзья в игре: "))+root.count;color:"#b5da8c";font.pixelSize:12;font.bold:true }
 }
}