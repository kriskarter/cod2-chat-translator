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
 Image { anchors.fill:parent;anchors.margins:4;source:root.artwork;sourceSize.width:1024;fillMode:Image.PreserveAspectCrop;opacity:1 }
 Rectangle { anchors.fill:parent;anchors.margins:4;gradient:Gradient {orientation:Gradient.Horizontal;GradientStop{position:0;color:"#cc171916"} GradientStop{position:.55;color:"#9a171916"} GradientStop{position:1;color:"#34171919"} } }
 ArtFrame {anchors.fill:parent;z:1}
 KeycapButton {
  id:key
  objectName:root.keyName.toLowerCase()+"Key"
  anchors.left:parent.left;anchors.leftMargin:root.compact?8:16;anchors.verticalCenter:parent.verticalCenter
  width:root.compact?Math.min(62,Math.max(42,root.height-24)):Math.min(94,root.height-24)
  height:width;text:root.keyName;active:root.active;enabled:root.controlsEnabled
  onClicked:root.toggled()
 }
 ColumnLayout {
  id:body
  anchors.left:key.right;anchors.leftMargin:root.compact?6:16;anchors.right:parent.right;anchors.rightMargin:root.compact?9:18
  anchors.verticalCenter:parent.verticalCenter
  spacing:root.compact?3:6
  RowLayout {
   Layout.fillWidth:true;spacing:5
   Text {
    text:root.heading;color:"#fff0d1";font.pixelSize:root.compact?14:22;font.bold:true;wrapMode:Text.WordWrap;maximumLineCount:2;elide:Text.ElideRight
    Layout.fillWidth:true;Layout.minimumWidth:0
   }
   TacticalSwitch { objectName:root.keyName.toLowerCase()+"Switch"; Layout.preferredWidth:66;Layout.minimumWidth:66;Layout.maximumWidth:66;checked:root.active;enabled:root.controlsEnabled;Accessible.name:root.heading;onClicked:root.toggled() }
  }
  Text {visible:!root.live;text:root.description;color:"#e8d4b3";font.pixelSize:root.compact?11:13;elide:Text.ElideRight;Layout.fillWidth:true}
  Loader {
   active:root.live;visible:active;Layout.fillWidth:true;Layout.minimumWidth:0;Layout.maximumWidth:root.keyName==="F8"?235:340
   sourceComponent:RowLayout {
    spacing:3
    Text {visible:root.keyName==="F8";text:(prototype.uiLanguage,prototype.trText("Авто"))+" →";color:"#e1c18a";font.pixelSize:11}
    LanguageSelector {
     objectName:root.keyName.toLowerCase()+"Language"
     model:root.keyName==="F8"?prototype.languages:prototype.outgoingLanguages
     textRole:"label";valueRole:"code";Layout.fillWidth:true;Layout.minimumWidth:0
     currentIndex:model?model.findIndex(item=>item.code===(root.keyName==="F8"?prototype.targetLanguage:prototype.outgoingSource)):-1
     onActivated:if(root.keyName==="F8")prototype.setTargetLanguage(currentValue);else prototype.setOutgoingRoute(currentValue,prototype.outgoingTarget)
    }
    Text {visible:root.keyName==="F9";text:"→";color:"#d9b477"}
    LanguageSelector {
     objectName:root.keyName.toLowerCase()+"Target";visible:root.keyName==="F9";model:prototype.outgoingLanguages;textRole:"label";valueRole:"code";Layout.fillWidth:true;Layout.minimumWidth:0
     currentIndex:model?model.findIndex(item=>item.code===prototype.outgoingTarget):-1
     onActivated:prototype.setOutgoingRoute(prototype.outgoingSource,currentValue)
    }
   }
  }
  RowLayout {
   Layout.fillWidth:true;spacing:5
   Rectangle {width:7;height:7;radius:4;color:root.active?"#b0db84":"#847c6d"}
   Text {text:root.liveStatus.length>0?root.liveStatus:!root.controlsEnabled?(prototype.uiLanguage,prototype.trText("Не перенесён")):root.active?(prototype.uiLanguage,prototype.trText("Активен")):(prototype.uiLanguage,prototype.trText("Выключен"));color:root.active?"#b0db84":"#bcb09a";font.pixelSize:11;elide:Text.ElideRight;Layout.minimumWidth:0;Layout.fillWidth:true}
   MetalButton {objectName:root.keyName==="F9"?"manual_outgoing":"unused_manual";visible:root.live&&root.keyName==="F9";text:(prototype.uiLanguage,prototype.trText("Ручной перевод"));font.pixelSize:11;sizeClass:"compact";Layout.minimumWidth:0;Layout.preferredWidth:Math.min(implicitWidth,body.width*.65);onClicked:root.manual()}
  }
 }
}