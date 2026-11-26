import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
Popup {
 id:root
 objectName:"friends_panel"
 parent:Overlay.overlay
 anchors.centerIn:parent
 width:Math.min(parent.width-24,prototype.friendRows.length > 0 ? 660 : 540)
 height:Math.min(parent.height-24, Math.max(238, 166 + Math.max(1,prototype.friendRows.length)*70 + (prototype.friendSaveError.length>0?34:0)))
 modal:true;focus:true;padding:16
 closePolicy:Popup.CloseOnEscape|Popup.CloseOnPressOutside
 function tr(s){let lang=prototype.uiLanguage;return prototype.trText(s)}
 background:MetalPanel {}
 contentItem:ColumnLayout {
  spacing:10
  RowLayout {
   Layout.fillWidth:true;spacing:8
   Image {source:"icons/friends.svg";Layout.preferredWidth:28;Layout.preferredHeight:28}
   Text {text:root.tr("Друзья в игре: ")+prototype.friendCount;color:"#ebd6ad";font.bold:true;font.pixelSize:19;Layout.fillWidth:true}
   MetalButton {text:root.tr("Закрыть");onClicked:root.close()}
  }
  Text {text:root.tr("Поиск по никнейму, а не по уникальному ID. Одинаковые имена могут принадлежать разным игрокам.");font.pixelSize:12;color:"#bcb09a";wrapMode:Text.WordWrap;Layout.fillWidth:true}
  RowLayout {
   Layout.fillWidth:true
   MetalTextField {id:manual;Layout.fillWidth:true;placeholderText:root.tr("Ник игрока");onAccepted:if(prototype.addFriend(text))clear()}
   AmberButton {text:root.tr("Добавить в друзья");enabled:manual.text.trim().length>0;onClicked:if(prototype.addFriend(manual.text))manual.clear()}
  }
  Text {visible:prototype.friendSaveError.length>0;text:prototype.friendSaveError;color:"#e99b83";font.pixelSize:12;wrapMode:Text.WordWrap;Layout.fillWidth:true}
  ListView {
   id:list;objectName:"friends_presence_list";Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:5
   model:prototype.friendRows
   ScrollBar.vertical:MetalScrollBar {}
   delegate:Rectangle {
    id:line;required property var modelData
    width:Math.max(0,list.width-10);height:65;radius:5;color:"#202722";border.color:modelData.state==="online"?"#596c48":"#504c41"
    RowLayout {
     anchors.fill:parent;anchors.margins:9;spacing:8
     Image {source:"icons/star.svg";Layout.preferredWidth:18;Layout.preferredHeight:18}
     ColumnLayout {
      Layout.fillWidth:true;spacing:3
      RowLayout {
       Layout.fillWidth:true
       Text {clip:true;Layout.minimumWidth:0;text:line.modelData.richName;textFormat:Text.RichText;color:"#eadaba";font.bold:true;font.pixelSize:14;Layout.fillWidth:true;elide:Text.ElideRight}
       Rectangle {width:8;height:8;radius:4;color:line.modelData.state==="online"?"#9ac76b":line.modelData.state==="unknown"?"#d0ae72":"#797d78"}
       Text {text:root.tr(line.modelData.state);color:line.modelData.state==="online"?"#b7db91":"#c4bba9";font.pixelSize:12}
      }
      Text {text:line.modelData.state==="online"?line.modelData.server+" · "+line.modelData.map+" · "+line.modelData.population:root.tr(line.modelData.state==="unknown"?"Нет полной информации о серверах":"Не найден на отслеживаемых серверах");textFormat:Text.PlainText;Layout.fillWidth:true;elide:Text.ElideRight;color:"#bcb09a";font.pixelSize:12}
      Text {visible:line.modelData.ambiguous;text:root.tr("Несколько совпадений никнейма");color:"#ddb879";font.pixelSize:11}
     }
     MetalButton {text:root.tr("Убрать");onClicked:prototype.removeFriend(line.modelData.rawName)}
     AmberButton {objectName:"friend_connect";text:root.tr("Подключиться");glyph:"icons/connect.svg";enabled:prototype.canConnect&&line.modelData.state==="online";visible:line.modelData.state==="online";onClicked:if(prototype.connectServer(line.modelData.address))root.close()}
    }
   }
   Text {anchors.centerIn:parent;visible:list.count===0;width:parent.width*.85;wrapMode:Text.WordWrap;horizontalAlignment:Text.AlignHCenter;color:"#bcb09a";text:root.tr("Добавьте друзей звёздочкой в списке игроков или по никнейму.")}
  }
 }
}