import QtQuick
Item {
    property var shell: null
    property var service: null
    readonly property bool opened: service ? service.homeOpen : false
    function open(payload) {
        service = shell ? shell.serviceFor("surface.tablet") : null
        if (!service) return
        let options = ({})
        try { options = JSON.parse(payload || "{}") } catch (e) {}
        service.home(options.all === true)
    }
    function close() { if (service) service.close() }
}
