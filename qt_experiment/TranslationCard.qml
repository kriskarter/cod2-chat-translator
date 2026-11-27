import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
MetalPanel {
 id:root
 objectName:keyName.toLowerCase()+"Card"
 property string keyName
 property string heading
 property string description
 property bool controlsEnabled:true
 property bool active
 property bool compact
 property url artwork
 property bool live:false
 property string liveStatus:""
 signal manual()
 signal toggled()
 clip:true
 artBorder:false
 Image {anchors.fill:parent;anchors.margins:5;source:root.artwork;fillMode:Image.Stretch}
 ArtFrame {anchors.fill:parent;source:"reference_art/card_frame.png";z:1}
 KeycapButton {
  id:key
  objectName:root.keyName.toLowerCase()+"Key"
  anchors.left:parent.left;anchors.leftMargin:root.compact?3:Math.min(14,root.width*.022);anchors.verticalCenter:parent.verticalCenter
  width:root.compact?Math.min(65,Math.max(42,root.height-18)):Math.min(140,root.width*.217,root.height*.84)
  height:width*135/140;text:root.keyName;active:root.active;enabled:root.controlsEnabled
  onClicked:root.toggled()
 }
 ColumnLayout {
  id:body
  anchors.left:key.right;anchors.leftMargin:root.compact?5:Math.min(17,root.width*.026);anchors.right:parent.right;anchors.rightMargin:root.compact?9:18
  anchors.verticalCenter:parent.verticalCenter
  spacing:root.compact?2:6
  RowLayout {
   Layout.fillWidth:true;spacing:5
   Text {
    text:root.heading;color:"#fff0d1";font.pixelSize:root.compact?14:Math.min(28,root.width*.043);font.bold:true;font.letterSpacing:-.35;fontSizeMode:Text.Fit;minimumPixelSize:root.compact?12:18;elide:Text.ElideRight
    Layout.fillWidth:true;Layout.minimumWidth:0
   }
   TacticalSwitch { objectName:root.keyName.toLowerCase()+"Switch"; cardStyle:true;Layout.preferredWidth:root.compact?67:Math.min(124,root.width*.19);Layout.minimumWidth:Layout.preferredWidth;Layout.maximumWidth:Layout.preferredWidth;Layout.preferredHeight:root.compact?25:34;checked:root.active;enabled:root.controlsEnabled;Accessible.name:root.heading;onClicked:root.toggled() }
  }
  Text {visible:!root.compact && root.height>=116;text: {
    let locale = prototype.uiLanguage
    let incoming = root.keyName === "F8"
    let target = root.live ? (incoming ? prototype.targetLanguage : prototype.outgoingTarget) : (incoming ? "ru" : "en")
    let base = prototype.trText(incoming ? "Перевод чата с любого языка" : "Перевод ваших сообщений")
    let suffix = {ru:"на русский", uk:"на украинский", en:"на английский"}[target]
    return suffix ? base + " " + prototype.trText(suffix) : base
   }
   color:"#e8d4b3";font.pixelSize:root.compact?11:16;elide:Text.ElideRight;Layout.fillWidth:true}
  Loader {
   active:root.live;visible:active;Layout.fillWidth:true;Layout.minimumWidth:0;Layout.maximumWidth:root.keyName==="F8"?194:294
   sourceComponent:RowLayout {
    spacing:3
    Image {visible:!root.compact;source:"reference_art/chat.png";Layout.preferredWidth:24;Layout.preferredHeight:24;fillMode:Image.PreserveAspectFit}
    Text {visible:root.keyName==="F8";text:(prototype.uiLanguage,prototype.trText("Авто"))+" →";color:"#e6d7b7";font.pixelSize:root.compact?11:15}
    LanguageSelector {
     inlineRoute:true; objectName:root.keyName.toLowerCase()+"Language"
     model:root.keyName==="F8"?prototype.languages:prototype.outgoingLanguages
     textRole:"label";valueRole:"code";Layout.fillWidth:true;Layout.minimumWidth:0
     currentIndex:model?model.findIndex(item=>item.code===(root.keyName==="F8"?prototype.targetLanguage:prototype.outgoingSource)):-1
     onActivated:if(root.keyName==="F8")prototype.setTargetLanguage(currentValue);else prototype.setOutgoingRoute(currentValue,prototype.outgoingTarget)
    }
    Text {visible:root.keyName==="F9";text:"→";color:"#d9b477"}
    LanguageSelector {
     inlineRoute:true; objectName:root.keyName.toLowerCase()+"Target";visible:root.keyName==="F9";model:prototype.outgoingLanguages;textRole:"label";valueRole:"code";Layout.fillWidth:true;Layout.minimumWidth:0
     currentIndex:model?model.findIndex(item=>item.code===prototype.outgoingTarget):-1
     onActivated:prototype.setOutgoingRoute(prototype.outgoingSource,currentValue)
    }
   }
  }
  Text { visible:!root.live; text:root.description;color:"#e8d7b9"; font.pixelSize:root.compact?12:16 }
  RowLayout {
   visible:root.live
   Layout.fillWidth:true;spacing:5
   Rectangle {width:7;height:7;radius:4;color:root.active?"#b0db84":"#847c6d"}
   Text {text:root.liveStatus.length>0?root.liveStatus:!root.controlsEnabled?(prototype.uiLanguage,prototype.trText("Не перенесён")):root.active?(prototype.uiLanguage,prototype.trText("Активен")):(prototype.uiLanguage,prototype.trText("Выключен"));color:root.active?"#b0db84":"#bcb09a";font.pixelSize:root.compact?11:12;elide:Text.ElideRight;Layout.minimumWidth:0;Layout.fillWidth:true}
   MetalButton {objectName:root.keyName==="F9"?"manual_outgoing":"unused_manual";visible:root.live&&root.keyName==="F9";text:(prototype.uiLanguage,prototype.trText("Ручной перевод"));font.pixelSize:11;sizeClass:"compact";Layout.minimumWidth:0;Layout.preferredWidth:Math.min(implicitWidth,body.width*.65);onClicked:root.manual()}
  }
 }
}