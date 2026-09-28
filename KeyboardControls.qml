import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.Commons

// A focus-free extension of the OSK sheet. Normal exclusion places it just
// above the keyboard's reserved area, and reserves its own height for apps.
PanelWindow {
    id: root
    property var service: null
    visible: service ? service.keyboardVisible : false
    anchors { bottom: true; left: true; right: true }
    implicitHeight: Math.max(48, Style.space(36))
    exclusiveZone: implicitHeight
    color: Color.background
    WlrLayershell.layer: WlrLayer.Top
    WlrLayershell.namespace: "omarchy-tablet-keyboard-controls"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    Rectangle { width: parent.width; height: 1; color: Util.alpha(Color.foreground, 0.12) }
    Text {
        anchors.left: parent.left
        anchors.leftMargin: Style.spacing.panelPadding
        anchors.verticalCenter: parent.verticalCenter
        text: "Keyboard"
        color: Color.foreground
        font { family: Style.font.family; pixelSize: Style.font.body }
    }
    Row {
        anchors.right: parent.right
        anchors.rightMargin: Style.spacing.panelPadding
        anchors.verticalCenter: parent.verticalCenter
        spacing: Style.spacing.sm
        TouchButton {
            width: Math.max(48, Style.space(40)); height: root.implicitHeight
            iconText: "\uf130"; iconSize: Style.font.icon
            enabled: !!(root.service && root.service.status.dictationAvailable)
            Accessible.name: "Toggle dictation"
            onClicked: root.service.command("dictation")
        }
        TouchButton {
            width: Math.max(48, Style.space(40)); height: root.implicitHeight
            iconText: "\uf078"; iconSize: Style.font.icon
            Accessible.name: "Hide keyboard"
            onClicked: root.service.command("hideKeyboard")
        }
    }
}
