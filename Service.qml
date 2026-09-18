import QtQuick
import Quickshell
import Quickshell.Io

Item {
    id: root
    property var shell: null
    property var manifest: null
    property var status: ({ mode: "auto", tablet: false, attached: true, keyboardAvailable: false, favorites: [] })
    property bool homeOpen: false
    property string page: "home"
    property string message: ""
    readonly property bool tablet: status.tablet === true
    readonly property var apps: shell ? shell.appLibrary : null
    property int appsRevision: 0

    function command(action, value) {
        if (backend.running) backend.write(JSON.stringify({action: action, value: value}) + "\n")
    }
    function openPage(value) { page = value; homeOpen = true }
    function home(all) { openPage(all ? "apps" : "home") }
    function close() { homeOpen = false }
    function launch(entry) {
        if (!entry || !apps) return
        // Wayland IM modules let Squeekboard receive text-input events.
        // gtk-launch handles desktop-entry quoting, actions and field codes.
        Quickshell.execDetached(["env", "GTK_IM_MODULE=wayland", "QT_IM_MODULE=wayland",
            "uwsm-app", "--", "gtk-launch", entry.id + ".desktop"])
        close()
    }
    function favorite(id) { command("favorite", id) }
    function run(argv) { Quickshell.execDetached(argv) }

    Process {
        id: backend
        command: ["python3", "-B", Qt.resolvedUrl("tablet.py").toString().replace("file://", ""), "daemon"]
        stdinEnabled: true
        running: true
        stdout: SplitParser {
            onRead: function(line) {
                try {
                    const next = JSON.parse(line)
                    root.status = next
                    root.message = next.error || ""
                } catch (e) { console.warn("Omarchy Tablet: invalid backend response") }
            }
        }
        onExited: restart.restart()
    }
    Timer { id: restart; interval: 4000; onTriggered: backend.running = true }
    Connections {
        target: root.apps
        function onAppsChanged() { root.appsRevision++ }
    }
    IpcHandler {
        target: "tablet"
        function home(): void { root.home(false) }
        function apps(): void { root.home(true) }
        function close(): void { root.close() }
        function mode(value: string): void { root.command("mode", value) }
        function layout(value: string): void { root.command("layout", value) }
        function dictation(): void { root.command("dictation") }
        function keyboard(): void { root.command("keyboard") }
        function build(): string { return Qt.resolvedUrl("tablet.py").toString() }
        function status(): string { return JSON.stringify(root.status) }
    }
}
