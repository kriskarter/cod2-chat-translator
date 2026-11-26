import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
MetalPanel {
 id:root
 property var players:[]
 property string population:"—"
 property string menuRaw:""
 property string menuName:""
 property string menuAddress:""
 property bool menuFavorite:false
 function tr(s){let lang=prototype.uiLanguage;return prototype.trText(s)}
 function openPlayerMenu(row,anchor,point){
  menuRaw=row.rawName;menuName=row.name;menuAddress=row.address;menuFavorite=prototype.isFriend(menuRaw);
  let pos=anchor.mapToItem(root,point.x,point.y);playerMenu.popup(root,pos.x,pos.y)
 }
 Menu {
  id:playerMenu;objectName:"player_context_menu";width:245;padding:4
  background:Rectangle {radius:6;color:"#242824";border.color:"#947a50"}
  MetalMenuItem {objectName:"context_add_friend";text:root.tr("Добавить в друзья");enabled:!root.menuFavorite;onTriggered:prototype.addFriend(root.menuRaw)}
  MetalMenuItem {objectName:"context_remove_friend";text:root.tr("Удалить из друзей");enabled:root.menuFavorite;onTriggered:prototype.removeFriend(root.menuRaw)}
  MetalMenuItem {objectName:"context_copy_nick";text:root.tr("Копировать никнейм");onTriggered:prototype.copyText(root.menuName)}
  MetalMenuItem {objectName:"context_copy_address";text:root.tr("Копировать адрес сервера");enabled:root.menuAddress.length>0;onTriggered:prototype.copyText(root.menuAddress)}
  MetalMenuItem {objectName:"context_connect";text:root.tr("Подключиться к серверу");enabled:prototype.canConnect&&root.menuAddress.length>0;onTriggered:prototype.connectServer(root.menuAddress)}
 }
 ColumnLayout {
  anchors.fill:parent;anchors.margins:7;spacing:2
  RowLayout {
   Image {source:"icons/friends.svg";Layout.preferredWidth:17;Layout.preferredHeight:17}
   Text {text:root.tr("Игроки на сервере")+" · "+root.population;color:"#e2c493";font.pixelSize:13;font.bold:true;Layout.fillWidth:true}
  }
  component Cells: RowLayout {
   property var dataRow
   property bool heading:false
   spacing:6
   Item {
    Layout.preferredWidth:22;Layout.preferredHeight:21
    Image {anchors.centerIn:parent;source:"icons/star_gray.svg";width:14;height:14;visible:heading;opacity:.8}
    Button {
     id:starButton
     objectName:!heading?"friend_star_"+dataRow.name:""
     visible:!heading;enabled:prototype.serverManagementAvailable
     anchors.fill:parent;hoverEnabled:true;padding:0
     Accessible.name:!heading?root.tr(dataRow.favorite?"Удалить из друзей":"Добавить в друзья"):""
     background:Rectangle {radius:3;color:parent.hovered?"#57462c":"transparent";border.color:parent.activeFocus?"#d6ad66":"transparent"}
     contentItem:Item {Image {anchors.centerIn:parent;width:16;height:16;source:!heading&&dataRow.favorite?"icons/star.svg":"icons/star_gray.svg";fillMode:Image.PreserveAspectFit;sourceSize.width:20;sourceSize.height:20}}
     onClicked:prototype.toggleFriend(dataRow.rawName)
     ToolTip {id:starTip;parent:starButton;visible:starButton.hovered;delay:550;text:starButton.Accessible.name
      background:Rectangle {radius:4;color:"#272d27";border.color:"#8a7551"}
      contentItem:Text {text:starTip.text;color:"#f1dfbd";font.pixelSize:12}
     }
    }
   }
   Text {id:nickLabel;objectName:!heading?"player_nick_"+dataRow.name:"";clip:true;Layout.minimumWidth:0;text:heading?root.tr("Никнейм"):dataRow.richName;textFormat:heading?Text.PlainText:Text.RichText;elide:Text.ElideRight;color:"#ddceae";Layout.fillWidth:true;font.pixelSize:12
    TapHandler {enabled:!heading&&prototype.serverManagementAvailable;acceptedButtons:Qt.RightButton;onTapped:(eventPoint,button)=>root.openPlayerMenu(dataRow,nickLabel,eventPoint.position)}
   }
   Text {text:heading?root.tr("Счёт"):dataRow.score;color:"#ddceae";Layout.preferredWidth:56;font.pixelSize:12;horizontalAlignment:Text.AlignRight}
   Text {text:heading?root.tr("Пинг"):dataRow.ping;color:heading?"#ddceae":dataRow.pingQuality==="good"?"#b8dc89":dataRow.pingQuality==="fair"?"#e0c37a":dataRow.pingQuality==="poor"?"#e68b74":"#b1ada2";Layout.preferredWidth:52;font.pixelSize:12;horizontalAlignment:Text.AlignRight}
  }
  Item {Layout.fillWidth:true;Layout.preferredHeight:21;Cells {anchors.fill:parent;anchors.leftMargin:5;anchors.rightMargin:13;heading:true;dataRow:({})}}
  ListView {
   id:roster;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:root.players
   ScrollBar.vertical:MetalScrollBar {}
   delegate:Rectangle {
    id:row;required property int index;required property var modelData
    width:Math.max(0,roster.width-9);height:22;color:index%2?"#1a1e1c":"#242824";radius:2
    Cells {anchors.fill:parent;anchors.leftMargin:5;anchors.rightMargin:4;dataRow:row.modelData}
   }
   Text {anchors.centerIn:parent;visible:roster.count===0;text:root.tr("Нет данных об игроках");color:"#a8a69b";font.pixelSize:12}
  }
 }
}