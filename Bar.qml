pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import Quickshell.Hyprland
import qs.Commons

Item {
    id: root
    property var shell: null
    property var manifest: null
    property var barConfig: ({})
    property var pluginRegistry: null
    property var barWidgetRegistry: null
    property var service: null
    readonly property bool tablet: service ? service.tablet : false
    readonly property var internalScreen: Quickshell.screens.find(s => /^(eDP|DSI|LVDS)/.test(s.name)) || Quickshell.screens[0]
    readonly property var entries: {
        const layout = barConfig.layout || {}
        return [].concat(layout.left || [], layout.center || [], layout.right || [])
    }
    property var hosts: []
    readonly property string position: "top"
    readonly property string fontFamily: Style.font.family
    readonly property bool barHidden: false
    readonly property int barSize: hosts.length ? hosts[0].panelHeight : Style.bar.sizeHorizontal
    function findPanelWidget(id) {
        const name = Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : ""
        const ordered = hosts.slice().sort((a, b) => (b.screenName === name ? 1 : 0) - (a.screenName === name ? 1 : 0))
        for (const host of ordered) {
            const items = host.moduleWidgets(id)
            for (const item of items) if (item.open && item.close) return item
        }
        return null
    }
    function isBarWidgetOpen(id) { const w = findPanelWidget(id); return w ? w.opened === true : false }
    function summonBarWidget(id) { const w = findPanelWidget(id); if (!w) return false; w.open(); return true }
    function hideBarWidget(id) { const w = findPanelWidget(id); if (!w) return false; w.close(); return true }
    function toggleBarWidget(id) { const w = findPanelWidget(id); if (!w) return false; if (w.opened) w.close(); else w.open(); return true }
    function panelWidgetIdAt(region, index) {
        const layout = barConfig.layout || {}
        const candidates = (layout[region] || []).filter(e => findPanelWidget(typeof e === "string" ? e : e.id))
        const entry = candidates[Number(index) - 1]
        return entry ? (typeof entry === "string" ? entry : entry.id) : ""
    }
    IpcHandler {
        target: "tablet-bar"
        function more(): void { for (const host of root.hosts) host.showMore() }
        function geometry(): string {
            return JSON.stringify(root.hosts.map(h => ({screen: h.screenName, touch: h.tablet, size: h.barSize,
                slots: h.slots.map(s => ({id: s.moduleName, width: s.width, height: s.height, loaded: !!s.item}))})))
        }
    }
    Timer {
        interval: 500; running: true; repeat: true; triggeredOnStart: true
        onTriggered: root.service = root.shell ? root.shell.serviceFor("surface.tablet") : null
    }
    Variants {
        model: Quickshell.screens
        PanelWindow {
            id: bar
            required property var modelData
            screen: modelData
            readonly property bool touch: root.tablet && screen === root.internalScreen
            readonly property int rowHeight: native.barSize
            readonly property bool narrow: width < screen.height || width < Math.max(900, Style.space(650))
            property bool moreOpen: false
            readonly property var primary: root.entries.filter(e => /\.(clock|power|audio|network|bluetooth)$/.test(typeof e === "string" ? e : e.id))
            readonly property var secondary: root.entries.filter(e => primary.indexOf(e) < 0)
            readonly property int navHeight: rowHeight + Style.spacing.sm * 2
            anchors { top: true; left: true; right: true }
            implicitHeight: navHeight + (touch && !narrow ? rowHeight + Style.spacing.sm : 0)
            exclusiveZone: implicitHeight
            color: root.barConfig.transparent ? "transparent" : Color.bar.background
            WlrLayershell.layer: WlrLayer.Top
            WlrLayershell.namespace: "omarchy-tablet-bar"
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            NativeHost {
                id: native
                property string screenName: bar.screen.name
                property int panelHeight: bar.implicitHeight
                function showMore() { bar.moreOpen = !bar.moreOpen }
                shell: root.shell
                tablet: bar.touch
                animations: root.service ? root.service.status.animations !== false : true
                layoutConfig: root.barConfig.layout || ({})
                transparent: root.barConfig.transparent === true
                Component.onCompleted: root.hosts = root.hosts.concat([native])
                Component.onDestruction: root.hosts = root.hosts.filter(h => h !== native)
            }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Style.spacing.sm
                spacing: Style.spacing.sm
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Style.spacing.sm
                    Repeater {
                        model: [{label: "Home", glyph: "⌂", page: "home"}, {label: "Apps", glyph: "▦", page: "apps"}, {label: "Windows", glyph: "▣", page: "windows"}]
                        TouchButton {
                            required property var modelData
                            compact: !bar.touch
                            text: bar.narrow ? modelData.glyph : modelData.label
                            Accessible.name: modelData.label
                            onClicked: if (root.service) root.service.openPage(modelData.page)
                        }
                    }
                    // A Flickable keeps every primary widget reachable at large font sizes.
                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentWidth: primaryRow.implicitWidth
                        contentHeight: height
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        Row {
                            id: primaryRow
                            spacing: Style.spacing.sm
                            Repeater {
                                model: bar.touch && !bar.narrow ? [] : (bar.narrow ? bar.primary : root.entries)
                                NativeWidget { required property var modelData; entry: modelData; registry: root.barWidgetRegistry; host: native }
                            }
                        }
                    }
                    TouchButton {
                        compact: !bar.touch
                        text: "⌨"
                        Accessible.name: "Toggle on-screen keyboard"
                        focusPolicy: Qt.NoFocus
                        onClicked: if (root.service) root.service.command("keyboard")
                    }
                    TouchButton {
                        visible: bar.touch
                        text: ""
                        Accessible.name: "Toggle dictation"
                        focusPolicy: Qt.NoFocus
                        onClicked: if (root.service) root.service.command("dictation")
                    }
                    TouchButton {
                        compact: !bar.touch
                        text: "More"
                        selected: bar.moreOpen
                        onClicked: bar.moreOpen = !bar.moreOpen
                    }
                }
                Flickable {
                    visible: bar.touch && !bar.narrow
                    Layout.fillWidth: true
                    Layout.preferredHeight: bar.rowHeight
                    clip: true
                    contentWidth: allRow.implicitWidth
                    contentHeight: height
                    boundsBehavior: Flickable.StopAtBounds
                    Row {
                        id: allRow
                        spacing: Style.spacing.sm
                        Repeater {
                            model: bar.touch && !bar.narrow ? root.entries : []
                            NativeWidget { required property var modelData; entry: modelData; registry: root.barWidgetRegistry; host: native }
                        }
                    }
                }
            }
            PanelWindow {
                id: more
                screen: bar.screen
                visible: bar.moreOpen
                anchors { top: true; left: true; right: true }
                margins.top: bar.implicitHeight
                exclusionMode: ExclusionMode.Ignore
                implicitHeight: Math.min(bar.screen.height * 0.65, moreColumn.implicitHeight + Style.spacing.panelPadding * 2)
                exclusiveZone: 0
                color: Color.popups.background
                WlrLayershell.layer: WlrLayer.Top
                WlrLayershell.namespace: "omarchy-tablet-more"
                WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
                Flickable {
                    anchors.fill: parent
                    anchors.margins: Style.spacing.panelPadding
                    contentHeight: moreColumn.implicitHeight
                    clip: true
                    Column {
                        id: moreColumn
                        width: parent.width
                        spacing: Style.spacing.panelGap
                        Flow {
                            width: parent.width
                            spacing: Style.spacing.controlGap
                            Repeater {
                                model: bar.narrow ? bar.secondary : []
                                NativeWidget { required property var modelData; entry: modelData; registry: root.barWidgetRegistry; host: native }
                            }
                        }
                        Flow {
                            width: parent.width
                            spacing: Style.spacing.controlGap
                            TouchButton { text: root.tablet ? "Tablet" : "Desktop"; selected: root.tablet; onClicked: root.service.command("mode", "toggle") }
                            TouchButton { text: "Auto"; selected: root.service && root.service.status.mode === "auto"; onClicked: root.service.command("mode", "auto") }
                            TouchButton { text: "Single app"; selected: root.service && root.service.status.layout === "single"; onClicked: root.service.command("layout", "single") }
                            TouchButton { text: "Omarchy tiling"; selected: root.service && root.service.status.layout === "tiling"; onClicked: root.service.command("layout", "tiling") }
                            TouchButton { text: "Settings"; onClicked: { bar.moreOpen = false; root.service.openPage("settings") } }
                            TouchButton { text: "Close"; onClicked: bar.moreOpen = false }
                        }
                    }
                }
            }
        }
    }
    PanelWindow {
        id: desktop
        screen: root.internalScreen
        visible: root.tablet && root.service !== null
        anchors { top: true; bottom: true; left: true; right: true }
        exclusiveZone: 0
        color: "transparent"
        WlrLayershell.layer: WlrLayer.Bottom
        WlrLayershell.namespace: "omarchy-tablet-desktop"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        HomeContent { anchors.fill: parent; service: root.service; backgroundMode: true }
    }
    PanelWindow {
        screen: root.internalScreen
        visible: root.service ? root.service.homeOpen : false
        anchors { top: true; bottom: true; left: true; right: true }
        exclusiveZone: 0
        color: "transparent"
        WlrLayershell.layer: WlrLayer.Top
        WlrLayershell.namespace: "omarchy-tablet-home"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
        HomeContent { anchors.fill: parent; service: root.service }
    }
}
