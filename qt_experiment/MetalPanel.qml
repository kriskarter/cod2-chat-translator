import QtQuick
Item {
 id:root
 property url texture:"art_steel.jpg"
 property bool artBorder:true
 implicitHeight:64
 Rectangle {anchors.fill:parent;anchors.topMargin:2;radius:7;color:"#0b0d0c"}
 Rectangle {anchors.fill:parent;anchors.bottomMargin:2;radius:6;color:"#1d211e"}
 Image {anchors.fill:parent;anchors.margins:4;source:root.texture;fillMode:Image.Tile;opacity:root.artBorder ? .56 : .32;clip:true}
 Rectangle {anchors.fill:parent;anchors.margins:3;radius:4;gradient:Gradient {GradientStop{position:0;color:"#292a2923"} GradientStop{position:1;color:"#80101311"}}}
 ArtFrame {anchors.fill:parent;visible:root.artBorder}
}
