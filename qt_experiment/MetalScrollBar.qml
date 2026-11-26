import QtQuick
import QtQuick.Controls
ScrollBar {
    id: root
    policy: ScrollBar.AsNeeded
    implicitWidth: 12
    padding: 1
    background: BorderImage {
        source: "../assets/ui_wwii/premium_scroll_track.png"
        border { left: 5; right: 5; top: 9; bottom: 9 }
    }
    contentItem: BorderImage {
        source: "../assets/ui_wwii/premium_scroll_grip.png"
        border { left: 5; right: 5; top: 12; bottom: 12 }
        opacity: root.active ? 1 : .8
    }
}
