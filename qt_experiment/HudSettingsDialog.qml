import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

MetalDialog {
    id: editor
    objectName: incoming ? "incoming_hud_dialog" : "outgoing_hud_dialog"
    property bool incoming: false
    property bool fullSize: false
    property var draft: ({})
    property var area: ({x:0, y:0, width:1366, height:768})
    property string sample: ""
    readonly property real minHeight: incoming ? 46 : draft.mode === "expanded" ? 145 : Math.max(60, 3*(Number(draft.font_size || 14)+3)+8)
    function tr(s) { let locale = prototype.uiLanguage; return prototype.trText(s) }
    function edit(isIncoming) {
        incoming = isIncoming
        fullSize = false
        area = incoming ? prototype.incomingDesktop() : Object.assign({x:0,y:0}, prototype.outgoingScreenSize())
        draft = incoming ? prototype.incomingHudSettings(false) : prototype.outgoingHudSettings
        refresh()
        open()
    }
    function refresh() { sample = incoming ? prototype.incomingHudPreview(draft) : prototype.outgoingHudPreview(draft) }
    function update(values) {
        let next = Object.assign({}, draft, values)
        let minimum = incoming ? 46 : next.mode === "expanded" ? 145 : Math.max(60,3*(next.font_size+3)+8)
        next.width = Math.max(200, Math.min(incoming?1200:1600, Math.round(next.width)))
        next.height = Math.max(minimum, Math.min(incoming?600:1200, Math.round(next.height)))
        next.x = Math.round(Math.max(area.x, Math.min(area.x+Math.max(0,area.width-next.width), next.x)))
        next.y = Math.round(Math.max(area.y, Math.min(area.y+Math.max(0,area.height-next.height), next.y)))
        draft = next
        refreshTimer.restart()
    }
    onClosed: { refreshTimer.stop(); sample = "" }
    Timer { id:refreshTimer; interval:40; onTriggered:editor.refresh() }
    anchors.centerIn: parent
    width: Math.min(900,parent.width-24)
    height: Math.min(450,parent.height-20)
    title: tr("Настройки окна")+" "+(incoming ? "F8" : "F9")
    standardButtons: Dialog.NoButton
    ColumnLayout {
        anchors.fill:parent
        RowLayout {
            Layout.fillWidth:true; Layout.fillHeight:true; spacing:15
            ColumnLayout {
                Layout.fillWidth:true; Layout.preferredWidth:410; Layout.fillHeight:true
                Rectangle {
                    id: stage
                    Layout.fillWidth:true; Layout.fillHeight:true
                    color:"#171c20"; border.color:"#85765c"; clip:true
                    property real scaleFactor: Math.min(width/editor.area.width,height/editor.area.height)
                    Item {
                        id: map
                        visible:!editor.fullSize; anchors.centerIn:parent
                        width:editor.area.width*stage.scaleFactor; height:editor.area.height*stage.scaleFactor
                        Rectangle { anchors.fill:parent; color:"#293230"; border.color:"#a38c64" }
                        Rectangle {
                            id: frame
                            x:(Number(editor.draft.x || 0)-editor.area.x)*stage.scaleFactor
                            y:(Number(editor.draft.y || 0)-editor.area.y)*stage.scaleFactor
                            width:Number(editor.draft.width || 400)*stage.scaleFactor
                            height:Number(editor.draft.height || 80)*stage.scaleFactor
                            color:"transparent";border.color:"#e0b46e"
                            Image { objectName:"outgoingHudPreview"; source:editor.sample; width:implicitWidth*stage.scaleFactor; height:implicitHeight*stage.scaleFactor }
                            MouseArea {
                                anchors.fill:parent;cursorShape:Qt.SizeAllCursor
                                property point offset
                                onPressed:m => { offset=Qt.point(m.x,m.y) }
                                onPositionChanged:m => {
                                    if (!pressed) return
                                    let point=mapToItem(map,m.x-offset.x,m.y-offset.y)
                                    editor.update({x:editor.area.x+point.x/stage.scaleFactor,y:editor.area.y+point.y/stage.scaleFactor})
                                }
                            }
                            Rectangle {
                                anchors.right:parent.right;anchors.bottom:parent.bottom;width:10;height:10;color:"#e2bd7f"
                                MouseArea {
                                    anchors.fill:parent;anchors.margins:-3;cursorShape:Qt.SizeFDiagCursor
                                    onPositionChanged:m => {
                                        if (!pressed) return
                                        let p=mapToItem(frame,m.x,m.y)
                                        editor.update({width:p.x/stage.scaleFactor,height:p.y/stage.scaleFactor})
                                    }
                                }
                            }
                        }
                    }
                    Flickable {
                        anchors.fill:parent;visible:editor.fullSize;clip:true
                        contentWidth:nativePreview.width;contentHeight:nativePreview.height
                        Image { id:nativePreview; source:editor.sample; width:implicitWidth/Screen.devicePixelRatio;height:implicitHeight/Screen.devicePixelRatio }
                    }
                }
                MetalButton { text:editor.fullSize ? editor.tr("Положение") : "1:1"; sizeClass:"compact";onClicked:editor.fullSize=!editor.fullSize }
            }
            ColumnLayout {
                Layout.preferredWidth:Math.min(editor.width*.44,380); Layout.maximumWidth:Math.min(editor.width*.44,380); Layout.minimumWidth:Math.min(editor.width*.40,340); Layout.fillHeight:true
                RowLayout {
                    visible:!editor.incoming
                    MetalButton { text:editor.tr("Компактный");selected:editor.draft.mode==="compact";onClicked:editor.update({mode:"compact",height:80}) }
                    MetalButton { text:editor.tr("Расширенный");selected:editor.draft.mode==="expanded";onClicked:editor.update({mode:"expanded",height:Math.max(160,editor.draft.height)}) }
                }
                GridLayout {
                    columns:4; Layout.fillWidth:true
                    Text { text:"X";color:"#e9dbbf" }
                    MetalTextField { text:String(editor.draft.x || 0);Layout.fillWidth:true;validator:IntValidator{} onEditingFinished:editor.update({x:Number(text)}) }
                    Text { text:"Y";color:"#e9dbbf" }
                    MetalTextField { text:String(editor.draft.y || 0);Layout.fillWidth:true;validator:IntValidator{} onEditingFinished:editor.update({y:Number(text)}) }
                }
                Repeater {
                    model:[{key:"width",label:"Ширина",lo:200,hi:editor.incoming?1200:1600,step:1},
                           {key:"height",label:"Высота",lo:editor.minHeight,hi:editor.incoming?600:1200,step:1},
                           {key:"font_size",label:"Размер текста",lo:editor.incoming?8:9,hi:editor.incoming?20:28,step:1},
                           {key:"background_opacity",label:"Непрозрачность фона",lo:editor.incoming?0:.35,hi:editor.incoming?.9:.95,step:.01}]
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth:true;spacing:0
                        Text { text:editor.tr(modelData.label)+"   "+(modelData.key==="background_opacity"?Math.round((editor.draft[modelData.key] || 0)*100)+"%":Math.round(editor.draft[modelData.key] || 0));color:"#e8d9bf" }
                        MetalSlider { Layout.fillWidth:true;from:modelData.lo;to:modelData.hi;stepSize:modelData.step;value:Number(editor.draft[modelData.key] || modelData.lo);onMoved:{let change={};change[modelData.key]=value;editor.update(change)} }
                    }
                }
                RowLayout {
                    Text { text:editor.tr("Автоматическая высота");color:"#e8d9bf";Layout.fillWidth:true }
                    TacticalSwitch { checked:editor.draft.auto_height!==false; onClicked:editor.update({auto_height:checked}) }
                }
            }
        }
        RowLayout {
            MetalButton { text:editor.tr("Сбросить");onClicked:editor.update(editor.incoming?prototype.incomingHudSettings(true):prototype.defaultOutgoingHud()) }
            Item { Layout.fillWidth:true }
            MetalButton { text:editor.tr("Отмена");onClicked:editor.reject() }
            AmberButton { text:editor.tr("Применить");onClicked:if(editor.incoming?prototype.applyIncomingHud(editor.draft):prototype.applyOutgoingHud(editor.draft)) editor.accept() }
        }
    }
}
