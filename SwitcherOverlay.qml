pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import qs.Commons
import qs.Ui

// Lightweight window cards, intentionally without live GPU thumbnails.
// Bar.qml owns the actual layer surface and destroys this view on dismissal.
Item {
    id: root
    property var service: null
    focus: true
    Keys.onEscapePressed: if (service) service.close()
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Style.spacing.panelPadding
        spacing: Style.spacing.panelGap
        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: "Windows"
                color: Color.menu.text
                font { family: Style.font.family; pixelSize: Style.font.display }
            }
            TouchButton { text: "Home"; iconText: "\uf00a"; onClicked: root.service.home(false) }
            TouchButton { iconText: "\uf00d"; Accessible.name: "Dismiss windows"; onClicked: root.service.close() }
        }
        Text {
            text: "Tap a window to return to it"
            color: Color.menu.text
            opacity: 0.65
            font { family: Style.font.family; pixelSize: Style.font.body }
        }
        ListView {
            id: cards
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Style.spacing.panelGap
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: ToplevelManager.toplevels
            ScrollBar.vertical: ScrollBar {}
            delegate: Rectangle {
                id: card
                required property var modelData
                width: cards.width
                height: Math.max(88, Style.space(88))
                radius: Style.cornerRadius
                color: cardTap.pressed ? Style.pressedFillFor(Color.menu.text, Color.accent) : Color.popups.background
                border.width: modelData.active ? Math.max(2, Style.normalBorderWidth) : Style.normalBorderWidth
                border.color: modelData.active ? Color.accent : Util.alpha(Color.menu.text, 0.15)
                Accessible.role: Accessible.Button
                Accessible.name: modelData.title || modelData.appId || "Window"
                Accessible.onPressAction: { card.modelData.activate(); root.service.close() }
                MouseArea {
                    id: cardTap
                    anchors.fill: parent
                    onClicked: { card.modelData.activate(); root.service.close() }
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: Style.spacing.md
                    spacing: Style.spacing.panelGap
                    Image {
                        Layout.preferredWidth: Style.space(40)
                        Layout.preferredHeight: Style.space(40)
                        source: Quickshell.iconPath(card.modelData.appId || "", true) || Quickshell.iconPath("application-x-executable", true)
                        sourceSize.width: Style.space(40) * Screen.devicePixelRatio
                        sourceSize.height: Style.space(40) * Screen.devicePixelRatio
                        asynchronous: true
                        fillMode: Image.PreserveAspectFit
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        Text {
                            Layout.fillWidth: true
                            text: card.modelData.title || card.modelData.appId || "Window"
                            textFormat: Text.PlainText
                            color: Color.menu.text
                            font { family: Style.font.family; pixelSize: Style.font.subtitle }
                            elide: Text.ElideRight
                        }
                        Text {
                            Layout.fillWidth: true
                            text: card.modelData.appId || ""
                            textFormat: Text.PlainText
                            color: Color.menu.text
                            opacity: 0.6
                            font { family: Style.font.family; pixelSize: Style.font.caption }
                            elide: Text.ElideRight
                        }
                    }
                    TouchButton {
                        iconText: "\uf00d"
                        activeColor: Color.urgent
                        Accessible.name: "Close " + (card.modelData.title || card.modelData.appId)
                        onClicked: card.modelData.close()
                    }
                }
            }
            Text {
                anchors.centerIn: parent
                visible: cards.count === 0
                text: "No open windows. Open an application from Home."
                width: parent.width
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                color: Color.menu.text
                font { family: Style.font.family; pixelSize: Style.font.body }
            }
        }
    }
}
