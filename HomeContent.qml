pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import qs.Commons

Item {
    id: root
    property var service: null
    property bool backgroundMode: false
    readonly property string page: !backgroundMode && service ? service.page : "home"
    property bool editing: false
    property string query: ""
    readonly property var entries: {
        if (!service || !service.apps) return []
        const revision = service.appsRevision
        const values = service.apps.sortedEntries(query).map(row => row.entry)
        if (page === "apps" || query.length) return values
        return (service.status.favorites || []).map(id => values.find(entry => entry.id === id)).filter(Boolean)
    }
    Image {
        anchors.fill: parent
        visible: !root.backgroundMode
        source: root.service ? root.service.status.wallpaper || "" : ""
        fillMode: Image.PreserveAspectCrop
    }
    Rectangle { anchors.fill: parent; color: Color.menu.scrim }
    Keys.onEscapePressed: if (service) service.close()
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Style.spacing.panelPadding
        spacing: Style.spacing.panelGap
        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: root.page === "settings" ? "Tablet settings" : root.page === "windows" ? "Windows" : root.page === "apps" ? "Applications" : "Home"
                color: Color.menu.text
                font { family: Style.font.family; pixelSize: Style.font.displayLarge }
                elide: Text.ElideRight
            }
            TouchButton { visible: !root.backgroundMode; text: "Close"; onClicked: root.service.close() }
        }
        Flow {
            visible: root.page === "home" || root.page === "apps"
            Layout.fillWidth: true
            spacing: Style.spacing.controlGap
            TouchButton { text: "Favorites"; selected: root.page === "home"; onClicked: { root.query = ""; root.service.openPage("home") } }
            TouchButton { text: "All apps"; selected: root.page === "apps"; onClicked: root.service.openPage("apps") }
            TouchButton {
                text: root.editing ? "Done" : "Customize"
                selected: root.editing
                onClicked: {
                    if (root.backgroundMode) root.service.openPage("apps")
                    else { root.service.page = "apps"; root.editing = !root.editing }
                }
            }
        }
        TextField {
            id: search
            visible: !root.backgroundMode && (root.page === "home" || root.page === "apps")
            Layout.fillWidth: true
            Layout.preferredHeight: Math.max(48, Style.space(40))
            placeholderText: "Search applications"
            Accessible.name: placeholderText
            text: root.query
            onTextEdited: root.query = text
            color: Color.menu.text
            placeholderTextColor: Util.alpha(Color.menu.text, 0.65)
            font { family: Style.font.family; pixelSize: Style.font.body }
            background: Rectangle { radius: Style.cornerRadius; color: Color.menu.background; border.color: Style.controlBorder(search.activeFocus, search.hovered); border.width: Style.normalBorderWidth }
        }
        Text {
            visible: root.service && root.service.message.length > 0
            text: root.service ? root.service.message : ""
            color: Color.urgent
            font { family: Style.font.family; pixelSize: Style.font.body }
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        GridView {
            id: grid
            visible: root.page === "home" || root.page === "apps"
            Layout.fillHeight: true
            Layout.fillWidth: true
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            cellWidth: width / Math.max(1, Math.floor(width / Style.space(150)))
            cellHeight: Style.space(156)
            model: root.entries
            ScrollBar.vertical: ScrollBar {}
            delegate: Item {
                id: tile
                required property var modelData
                width: grid.cellWidth
                height: grid.cellHeight
                readonly property bool favorite: root.service && (root.service.status.favorites || []).indexOf(modelData.id) !== -1
                Button {
                    id: appButton
                    anchors { fill: parent; margins: Style.spacing.md }
                    Accessible.name: root.service.apps.entryName(tile.modelData)
                    onClicked: root.service.launch(tile.modelData)
                    background: Rectangle {
                        radius: Style.cornerRadius
                        color: appButton.down ? Style.pressedFill : appButton.hovered ? Style.hoverFill : Color.menu.background
                        border.color: Style.controlBorder(appButton.activeFocus, appButton.hovered)
                        border.width: Style.controlBorderWidth(appButton.activeFocus, appButton.hovered)
                    }
                    contentItem: Column {
                        spacing: Style.spacing.controlGap
                        topPadding: Style.spacing.controlPaddingY
                        Image {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: Style.space(56); height: width
                            sourceSize { width: 128; height: 128 }
                            source: root.service.apps.iconSource(tile.modelData.icon)
                            fillMode: Image.PreserveAspectFit
                            Text { anchors.centerIn: parent; visible: parent.status !== Image.Ready; text: "▦"; color: Color.accent; font.pixelSize: Style.font.displayLarge }
                        }
                        Text {
                            width: parent.width
                            text: appButton.Accessible.name
                            color: Color.menu.text
                            font { family: Style.font.family; pixelSize: Style.font.body }
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.Wrap
                            maximumLineCount: 2
                            elide: Text.ElideRight
                        }
                    }
                }
                TouchButton {
                    visible: root.editing
                    anchors { right: parent.right; top: parent.top }
                    text: tile.favorite ? "★" : "☆"
                    selected: tile.favorite
                    Accessible.name: tile.favorite ? "Remove favorite" : "Add favorite"
                    onClicked: root.service.favorite(tile.modelData.id)
                }
            }
            Text {
                anchors.centerIn: parent
                visible: grid.count === 0
                text: root.page === "apps" || root.query.length ? "No applications found." : "Choose favorites in All apps → Customize."
                color: Color.menu.text
                font { family: Style.font.family; pixelSize: Style.font.body }
                width: parent.width
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }
        }
        Flickable {
            visible: root.page === "settings"
            Layout.fillHeight: true
            Layout.fillWidth: true
            contentHeight: settingsColumn.implicitHeight
            clip: true
            ColumnLayout {
                id: settingsColumn
                width: parent.width
                spacing: Style.spacing.panelGap
                Text { text: "Mode"; color: Color.menu.text; font.pixelSize: Style.font.heading; font.family: Style.font.family }
                Flow {
                    Layout.fillWidth: true
                    spacing: Style.spacing.controlGap
                    Repeater {
                        model: [{label: "Automatic", mode: "auto"}, {label: "Tablet", mode: "tablet"}, {label: "Desktop", mode: "desktop"}]
                        TouchButton { required property var modelData; text: modelData.label; selected: root.service && root.service.status.mode === modelData.mode; onClicked: root.service.command("mode", modelData.mode) }
                    }
                }
                Text {
                    text: root.service && root.service.status.attached ? "Physical keyboard attached. Auto uses desktop mode." : "Physical keyboard detached. Auto uses tablet mode."
                    color: Color.menu.text; font.pixelSize: Style.font.body; font.family: Style.font.family
                    Layout.fillWidth: true; wrapMode: Text.WordWrap
                }
                Text { text: "Tablet layout"; color: Color.menu.text; font.pixelSize: Style.font.heading; font.family: Style.font.family }
                Flow {
                    Layout.fillWidth: true
                    spacing: Style.spacing.controlGap
                    TouchButton { text: "Single app"; selected: root.service && root.service.status.layout === "single"; onClicked: root.service.command("layout", "single") }
                    TouchButton { text: "Omarchy tiling"; selected: root.service && root.service.status.layout === "tiling"; onClicked: root.service.command("layout", "tiling") }
                    TouchButton { text: "On-screen keyboard"; focusPolicy: Qt.NoFocus; onClicked: root.service.command("keyboard") }
                }
                Text { text: "Dictation command"; color: Color.menu.text; font.pixelSize: Style.font.heading; font.family: Style.font.family }
                TextField {
                    id: dictation
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(48, Style.space(40))
                    text: root.service ? root.service.status.dictationCommandText || "" : ""
                    Accessible.name: "Dictation command"
                    color: Color.menu.text
                    font { family: Style.font.family; pixelSize: Style.font.body }
                    background: Rectangle { color: Color.menu.background; radius: Style.cornerRadius; border.color: Color.menu.border; border.width: Style.normalBorderWidth }
                }
                TouchButton { text: "Save command"; onClicked: root.service.command("dictationCommand", dictation.text) }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: "Tap the microphone in the top bar to toggle dictation into the focused field.\nThe keyboard opens automatically in compatible Wayland fields; use the keyboard button elsewhere.\nF9 and your keyboard language remain independent of these settings."
                    color: Color.menu.text; font.pixelSize: Style.font.body; font.family: Style.font.family
                }
            }
        }
        ListView {
            visible: root.page === "windows"
            Layout.fillHeight: true
            Layout.fillWidth: true
            clip: true
            spacing: Style.spacing.controlGap
            model: ToplevelManager.toplevels
            ScrollBar.vertical: ScrollBar {}
            delegate: TouchButton {
                required property var modelData
                width: ListView.view.width
                text: modelData.title || modelData.appId
                onClicked: { modelData.activate(); root.service.close() }
            }
        }
    }
}
