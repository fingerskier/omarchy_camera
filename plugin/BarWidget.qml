import QtQuick
import Quickshell
import Quickshell.Io
import qs.Ui as Ui
import qs.Commons

Ui.Panel {
    id: root
    moduleName: "fingerskier.camera"
    ipcTarget: "fingerskier.camera"
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight

    // plugin/BarWidget.qml → repo root, where scripts/camera.py lives.
    readonly property string pluginRoot: Qt.resolvedUrl("../").toString().replace(/^file:\/\//, "").replace(/\/$/, "")
    property bool probing: false
    property bool acquired: false
    property string device: ""
    property string cameraName: ""
    property string lastError: ""

    readonly property string statusText: lastError !== "" ? lastError : (acquired ? ("Camera: " + cameraName) : "No camera found")
    readonly property color foreground: Color.popups.text

    function refresh() {
        if (probe.running)
            return;
        probing = true;
        lastError = "";
        probe.running = true;
    }

    function applyStatus(raw) {
        probing = false;
        var data;
        try {
            data = JSON.parse(raw);
        } catch (e) {
            acquired = false;
            device = "";
            cameraName = "";
            lastError = "No camera found";
            return;
        }
        acquired = !!data.ok;
        device = data.device || "";
        cameraName = data.name || "";
        lastError = data.ok ? "" : (data.error || "No camera found");
    }

    Component.onCompleted: refresh()

    Ui.BarIconButton {
        id: button
        anchors.fill: parent
        bar: root.bar
        slotSize: Style.bar.statusSlot
        dimmed: !root.acquired && !root.lastError
        tooltipText: root.statusText
        iconComponent: Canvas {
            property color foreground: root.lastError && !root.acquired ? Color.urgent : root.barForeground
            onForegroundChanged: requestPaint()
            onPaint: {
                const p = getContext("2d");
                p.clearRect(0, 0, width, height);
                p.save();
                p.scale(width / 24, height / 24);
                p.strokeStyle = foreground;
                p.fillStyle = foreground;
                p.lineWidth = 1.7;
                p.lineCap = "round";
                p.lineJoin = "round";
                p.beginPath();
                p.rect(3, 8, 18, 12);
                p.stroke();
                p.beginPath();
                p.arc(12, 14, 3.5, 0, Math.PI * 2);
                p.stroke();
                p.beginPath();
                p.moveTo(8, 8);
                p.lineTo(9.5, 5);
                p.lineTo(14.5, 5);
                p.lineTo(16, 8);
                p.stroke();
                p.restore();
            }
        }
        onPressed: function (mouseButton) {
            if (mouseButton === Qt.LeftButton || mouseButton === Qt.RightButton)
                root.toggle();
        }
    }

    Process {
        id: probe
        command: ["python3", root.pluginRoot + "/scripts/camera.py"]
        stdout: StdioCollector {
            waitForEnd: true
            onStreamFinished: root.applyStatus(text.trim())
        }
        onExited: function (code) {
            root.probing = false;
            if (code !== 0 && !root.acquired && root.lastError === "")
                root.lastError = "No camera found";
        }
    }

    Ui.KeyboardPanel {
        id: panel
        anchorItem: button
        owner: root
        bar: root.bar
        open: root.opened
        focusTarget: statusLabel
        contentWidth: panel.fittedContentWidth(Style.space(320))
        contentHeight: panel.fittedContentHeight(column.implicitHeight)

        Item {
            anchors.fill: parent
            Keys.onEscapePressed: root.close()
            Column {
                id: column
                width: parent.width
                spacing: Style.space(10)
                Text {
                    id: statusLabel
                    width: parent.width
                    text: root.probing ? "Looking for camera…" : root.statusText
                    textFormat: Text.PlainText
                    wrapMode: Text.WordWrap
                    color: root.lastError && !root.acquired ? Color.urgent : root.foreground
                    font.family: Style.font.family
                    font.pixelSize: Style.font.body
                    focus: true
                    Keys.onEscapePressed: root.close()
                }
                Text {
                    width: parent.width
                    visible: root.acquired && root.device !== ""
                    text: root.device
                    textFormat: Text.PlainText
                    color: Qt.alpha(root.foreground, 0.65)
                    font.family: Style.font.family
                    font.pixelSize: Style.font.caption
                }
                Ui.Button {
                    width: parent.width
                    text: "Retry"
                    bordered: true
                    focusable: true
                    onClicked: root.refresh()
                }
            }
        }
    }
}
