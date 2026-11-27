import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
ColumnLayout {
 id:root
 property var rows:[]
 property string selected:""
 signal chosen(string address)
 spacing:2
 component Cells:RowLayout {
  property var values
  property bool header:false
  property bool online:false
  property bool favorite:false
  spacing:5
  Item { Layout.preferredWidth:root.width<520?18:38;Layout.preferredHeight:22
   Image {anchors.centerIn:parent;width:21;height:21;fillMode:Image.PreserveAspectFit;source:favorite?"reference_art/star.png":"icons/star_gray.svg";visible:!header}
  }
  Text {text:values[0];Layout.fillWidth:true;Layout.minimumWidth:35;color:header?"#bcb09a":"#f5e7c9";elide:Text.ElideRight;font.pixelSize:root.width<520?12:header?15:17;font.bold:!header}
  Text {text:values[1];Layout.preferredWidth:Math.min(142,root.width*.16);color:"#d4ccba";elide:Text.ElideRight;font.pixelSize:root.width<520?11:15}
  Text {text:values[2];Layout.preferredWidth:Math.max(42,root.width*.115);color:"#d4ccba";font.pixelSize:root.width<520?11:15;horizontalAlignment:Text.AlignHCenter}
  Text {text:values[3];Layout.preferredWidth:Math.max(42,root.width*.105);color:header?"#bcb09a":parseInt(values[3])>0&&parseInt(values[3])<70?"#add880":parseInt(values[3])>=160?"#de8b73":"#d5c5a9";font.pixelSize:root.width<520?11:15;horizontalAlignment:Text.AlignHCenter}
  Rectangle {opacity:header?0:1;width:7;height:7;radius:4;color:online?"#a9d978":"#888b83"}
  Text {text:values[4];Layout.preferredWidth:Math.min(155,root.width*.17);color:header?"#bcb09a":online?"#a9d978":"#bcb8ad";font.pixelSize:root.width<520?11:15;elide:Text.ElideRight}
 }
 Item {Layout.fillWidth:true;Layout.preferredHeight:22;Cells {anchors.fill:parent;anchors.leftMargin:7;anchors.rightMargin:16;header:true;values:[(prototype.uiLanguage,prototype.trText("Сервер")),(prototype.uiLanguage,prototype.trText("Карта")),(prototype.uiLanguage,prototype.trText("Игроки")),(prototype.uiLanguage,prototype.trText("Пинг")),(prototype.uiLanguage,prototype.trText("Статус"))]}}
 ListView {
  id:table;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:2;model:root.rows
  ScrollBar.vertical:MetalScrollBar {}
  delegate:Rectangle {
   id:line;required property var modelData;required property int index
   width:Math.max(0,table.width-9);height:root.width<520?26:32;radius:4
   color:root.selected===modelData.address?"#56452a":index%2?"#161615":"#1c1b19"
   border.color:root.selected===modelData.address?"#c49a58":"transparent"
   BorderImage {anchors.fill:parent;source:"reference_art/selected_row.png";border {left:8;right:8;top:5;bottom:5} visible:root.selected===line.modelData.address}
   Cells {anchors.fill:parent;anchors.leftMargin:7;anchors.rightMargin:7;values:[line.modelData.name,line.modelData.map,line.modelData.population,line.modelData.ping,(prototype.uiLanguage,prototype.trText(line.modelData.state))];favorite:!!line.modelData.favorite;online:line.modelData.state==="online"}
   TapHandler {onTapped:root.chosen(line.modelData.address)}
   HoverHandler {id:hover}
   ToolTip.visible:hover.hovered;ToolTip.text:line.modelData.name+" · "+line.modelData.address
  }
  Text {anchors.centerIn:parent;visible:table.count===0;text:(prototype.uiLanguage,prototype.trText("Добавьте сервер"));color:"#bcb09a"}
 }
}