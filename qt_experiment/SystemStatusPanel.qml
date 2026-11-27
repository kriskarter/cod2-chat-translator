import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
RowLayout {
 id:root
 property string statusText:""
 property bool ready:false
 signal configure()
 spacing:8
 Image { visible:root.ready; source:"reference_art/ready.png"; Layout.preferredWidth:40; Layout.preferredHeight:40 }
 Rectangle { visible:!root.ready; width:30;height:30;radius:15;color:"#18241b";border.color:root.ready?"#9ac276":"#bf9659"
  Text { anchors.centerIn:parent;text:root.ready?"✓":"!";font.pixelSize:20;font.bold:true;color:root.ready?"#b0db84":"#d4a75e" }
 }
 ColumnLayout { Layout.fillWidth:true;spacing:3
  Text { text:prototype.translationAvailable?(prototype.uiLanguage,prototype.trText(root.ready?"Движок готов":"Требуется настройка")):root.statusText;color:root.ready?"#b0db84":"#e9c88d";font.bold:true;font.pixelSize:13;elide:Text.ElideRight;Layout.fillWidth:true }
  Text { visible:prototype.translationAvailable;text:visible?(prototype.uiLanguage,prototype.trText(prototype.logReady?"Журнал подключён":"Журнал не выбран"))+" · "+(prototype.uiLanguage,prototype.trText(prototype.canConnect?"Игра обнаружена":"Игра не обнаружена")):"";color:"#bcb4a5";font.pixelSize:11;elide:Text.ElideRight;Layout.fillWidth:true }
 }
 TapHandler { onTapped:if(prototype.translationAvailable)root.configure() }
 HoverHandler { id:hover }
 ToolTip.visible:hover.hovered
 ToolTip.text:root.statusText
}