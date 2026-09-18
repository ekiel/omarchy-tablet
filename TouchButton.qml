import QtQuick
import QtQuick.Controls
import qs.Commons

Button {
    id: control
    property bool selected: false
    property bool compact: false
    implicitHeight: compact ? Style.bar.sizeHorizontal : Math.max(48, Style.space(40))
    implicitWidth: Math.max(compact ? 28 : 48, label.implicitWidth + Style.spacing.controlPaddingX * 2)
    focusPolicy: Qt.TabFocus
    Accessible.name: text
    contentItem: Text {
        id: label
        text: control.text
        color: control.selected ? Color.accent : Color.foreground
        font.family: Style.font.family
        font.pixelSize: Style.font.body
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        radius: Style.cornerRadius
        color: control.down ? Style.pressedFill : control.selected ? Style.selectedFill : control.hovered ? Style.hoverFill : Style.normalFill
        border.width: Style.controlBorderWidth(control.activeFocus, control.hovered)
        border.color: Style.controlBorder(control.activeFocus, control.hovered)
    }
}
