import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
MetalPanel {
 id:root
 property var players:[]
 property string population:"—"
 ColumnLayout {
  anchors.fill:parent;anchors.margins:7;spacing:2
  RowLayout {
   Image {source:"icons/friends.svg";Layout.preferredWidth:17;Layout.preferredHeight:17}
   Text {text:(prototype.uiLanguage,prototype.trText("Игроки на сервере"))+" · "+root.population;color:"#e2c493";font.pixelSize:13;font.bold:true;Layout.fillWidth:true}
  }
  component Cells: RowLayout {
   property var dataRow
   property bool heading:false
   spacing:6
   Image {source:"icons/star.svg";opacity:!heading&&dataRow.favorite?1:0;Layout.preferredWidth:13;Layout.preferredHeight:13}
   Text {text:heading?(prototype.uiLanguage,prototype.trText("Никнейм")):dataRow.richName;textFormat:heading?Text.PlainText:Text.RichText;elide:Text.ElideRight;color:"#ddceae";Layout.fillWidth:true;font.pixelSize:12}
   Text {text:heading?(prototype.uiLanguage,prototype.trText("Счёт")):dataRow.score;color:"#ddceae";Layout.preferredWidth:56;font.pixelSize:12;horizontalAlignment:Text.AlignRight}
   Text {text:heading?(prototype.uiLanguage,prototype.trText("Пинг")):dataRow.ping;color:heading?"#ddceae":dataRow.pingQuality==="good"?"#b8dc89":dataRow.pingQuality==="fair"?"#e0c37a":dataRow.pingQuality==="poor"?"#e68b74":"#b1ada2";Layout.preferredWidth:52;font.pixelSize:12;horizontalAlignment:Text.AlignRight}
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
   Text {anchors.centerIn:parent;visible:roster.count===0;text:(prototype.uiLanguage,prototype.trText("Нет данных об игроках"));color:"#a8a69b";font.pixelSize:12}
  }
 }
}