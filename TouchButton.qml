import QtQuick
import qs.Commons

// Touch-friendly control that mirrors the Omarchy button kit. It renders the
// same state fills/borders from qs.Commons.Style as qs.Ui.Button, so the bar
// and home screen feel native, while keeping a generous (48px+) touch target
// on tablets and compact sizing in desktop mode.
Item {
    id: root

    property string text: ""
    property string iconText: ""
    property color foreground: Color.foreground
    property color activeColor: Color.accent
    property bool selected: false
    property bool compact: false
    property bool animations: true
    property real iconSize: compact ? Style.font.icon : Style.font.iconLarge

    signal clicked()

    // Reserve the largest border any state can paint so idle and hover/focus
    // don't change the control's outer size.
    readonly property int _reserve: Math.max(
        Style.hoverBorderWidth, Style.focusBorderWidth,
        root.selected ? Style.selectedBorderWidth : 0)
    readonly property bool _hot: hoverArea.containsMouse
    readonly property bool _focused: activeFocus
    readonly property color _color: root.selected ? Style.selectedStateColor(root.foreground, root.activeColor)
        : root.foreground

    implicitWidth: Math.max(compact ? 0 : 48, row.implicitWidth + Style.spacing.controlPaddingX * 2 + _reserve * 2)
    implicitHeight: (compact ? Style.bar.sizeHorizontal : Math.max(48, Style.space(40))) + _reserve * 2

    activeFocusOnTab: true
    Keys.onReturnPressed: if (activeFocus) root.clicked()
    Keys.onEnterPressed: if (activeFocus) root.clicked()
    Keys.onSpacePressed: if (activeFocus) root.clicked()

    Accessible.role: Accessible.Button
    Accessible.name: root.text
    Accessible.onPressAction: if (enabled) root.clicked()
    opacity: enabled ? 1 : 0.4

    Rectangle {
        anchors.fill: parent
        radius: Style.cornerRadius
        color: hoverArea.pressed ? Style.pressedFillFor(root.foreground, root.activeColor)
            : root._focused ? Style.focusFillFor(root.foreground, root.activeColor)
            : root._hot ? Style.hoverFillFor(root.foreground, root.activeColor)
            : root.selected ? Style.selectedFillFor(root.foreground, root.activeColor)
            : "transparent"
        border.width: root._focused ? Style.focusBorderWidth
            : root._hot ? Style.hoverBorderWidth
            : root.selected ? Style.selectedBorderWidth : 0
        border.color: root._focused ? Style.focusBorderFor(root.foreground, root.activeColor)
            : root._hot ? Style.hoverBorderFor(root.foreground, root.activeColor)
            : root.selected ? Style.selectedBorderFor(root.foreground, root.activeColor)
            : "transparent"

        Behavior on color { enabled: root.animations; ColorAnimation { duration: 100 } }
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: root.text.length > 0 ? Style.spacing.controlGap : 0

        Text {
            visible: root.iconText.length > 0
            text: root.iconText
            color: root._color
            font.family: Style.font.family
            font.pixelSize: root.iconSize
            verticalAlignment: Text.AlignVCenter
        }

        Text {
            visible: root.text.length > 0
            text: root.text
            color: root._color
            font.family: Style.font.family
            font.pixelSize: compact ? Style.font.body : Style.font.body
            font.bold: root.selected
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton
        cursorShape: Qt.PointingHandCursor
        onClicked: { root.forceActiveFocus(); root.clicked() }
    }
}