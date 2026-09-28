import QtQuick
import Quickshell
import qs.Commons

Item {
    id: slot
    required property var entry
    required property var registry
    required property var host
    readonly property string moduleName: typeof entry === "string" ? entry : (entry ? entry.id : "")
    property var item: null
    readonly property var registered: registry && registry.widgets ? registry.widgets[moduleName] : null
    implicitWidth: item && item.visible ? Math.max(host.tablet ? 48 : 0, item.implicitWidth) : 0
    implicitHeight: host.barSize
    width: implicitWidth
    height: implicitHeight
    property bool ready: false
    Component.onCompleted: { ready = true; host.registerSlot(slot); rebuild() }
    Component.onDestruction: { host.unregisterSlot(slot); if (item) item.destroy() }
    function rebuild() {
        if (!ready) return
        if (item) { item.destroy(); item = null }
        if (!registered || !registered.component) return
        item = registered.component.createObject(slot, {bar: host, moduleName: moduleName,
            settings: typeof entry === "string" ? {} : entry})
        if (item) {
            item.width = Qt.binding(() => slot.width)
            item.height = Qt.binding(() => slot.height)
        }
    }
    onRegisteredChanged: rebuild()
    function inject() {
        if (!item) return
        if ("bar" in item) item.bar = host
        if ("moduleName" in item) item.moduleName = moduleName
        if ("settings" in item) item.settings = typeof entry === "string" ? {} : entry
    }
    onEntryChanged: inject()
}
