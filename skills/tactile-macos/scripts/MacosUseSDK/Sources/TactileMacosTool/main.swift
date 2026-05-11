import AppKit
import CoreGraphics
import Foundation
import MacosUseSDK

enum ToolFailure: Error, LocalizedError {
    case usage(String)

    var errorDescription: String? {
        switch self {
        case .usage(let message):
            return message
        }
    }
}

func printUsage() {
    fputs(
        """
        usage: TactileMacosTool <command> [args...]

        commands:
          open <application-name|bundle-id|path>
          traverse [--visible-only] [--no-activate] <pid>
          highlight <pid> [--duration <seconds>]
          input <action> [args...]
          visual <action> [args...] [--duration <seconds>]

        """,
        stderr
    )
}

func jsonPrint<T: Encodable>(_ value: T) throws {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    let data = try encoder.encode(value)
    guard let text = String(data: data, encoding: .utf8) else {
        throw ToolFailure.usage("failed to encode JSON as UTF-8")
    }
    print(text)
}

func parsePid(_ value: String, name: String = "pid") throws -> Int32 {
    guard let pid = Int32(value) else {
        throw ToolFailure.usage("invalid \(name): \(value)")
    }
    return pid
}

func parsePoint(_ args: [String], usage: String) throws -> CGPoint {
    guard args.count == 2, let x = Double(args[0]), let y = Double(args[1]) else {
        throw ToolFailure.usage(usage)
    }
    return CGPoint(x: x, y: y)
}

func keyCodeAndFlags(_ keyCombo: String) throws -> (CGKeyCode, CGEventFlags) {
    let parts = keyCombo
        .split(separator: "+")
        .map { String($0).trimmingCharacters(in: .whitespacesAndNewlines).lowercased() }
    guard let keyPart = parts.last, let keyCode = MacosUseSDK.mapKeyNameToKeyCode(keyPart) else {
        throw ToolFailure.usage("unknown key name or key code: \(keyCombo)")
    }

    var flags: CGEventFlags = []
    for modifier in parts.dropLast() {
        switch modifier {
        case "cmd", "command":
            flags.insert(.maskCommand)
        case "shift":
            flags.insert(.maskShift)
        case "opt", "option", "alt":
            flags.insert(.maskAlternate)
        case "ctrl", "control":
            flags.insert(.maskControl)
        case "fn", "function":
            flags.insert(.maskSecondaryFn)
        default:
            throw ToolFailure.usage("unknown key modifier: \(modifier)")
        }
    }
    return (keyCode, flags)
}

func runOpen(_ args: [String]) async throws {
    guard args.count == 1 else {
        throw ToolFailure.usage("usage: TactileMacosTool open <application-name|bundle-id|path>")
    }
    let result = try await MacosUseSDK.openApplication(identifier: args[0])
    print(result.pid)
}

func runTraverse(_ rawArgs: [String]) throws {
    var args = rawArgs
    var onlyVisible = false
    var activateApp = true

    if let index = args.firstIndex(of: "--visible-only") {
        onlyVisible = true
        args.remove(at: index)
        fputs("info: '--visible-only' flag detected.\n", stderr)
    }

    if let index = args.firstIndex(of: "--no-activate") {
        activateApp = false
        args.remove(at: index)
        fputs("info: '--no-activate' flag detected.\n", stderr)
    }

    guard args.count == 1 else {
        throw ToolFailure.usage("usage: TactileMacosTool traverse [--visible-only] [--no-activate] <pid>")
    }

    let pid = try parsePid(args[0])
    fputs("info: calling traverseAccessibilityTree for pid \(pid) (Visible Only: \(onlyVisible), Activate App: \(activateApp))...\n", stderr)
    let response = try MacosUseSDK.traverseAccessibilityTree(
        pid: pid,
        onlyVisibleElements: onlyVisible,
        activateApp: activateApp
    )
    fputs("info: successfully received response from traverseAccessibilityTree.\n", stderr)
    try jsonPrint(response)
}

func runHighlight(_ rawArgs: [String]) async throws {
    var args = rawArgs
    var duration = 3.0

    if let index = args.firstIndex(of: "--duration") {
        guard index + 1 < args.count, let parsed = Double(args[index + 1]), parsed > 0 else {
            throw ToolFailure.usage("invalid --duration value")
        }
        duration = parsed
        args.remove(at: index + 1)
        args.remove(at: index)
    }

    guard args.count == 1 else {
        throw ToolFailure.usage("usage: TactileMacosTool highlight <pid> [--duration <seconds>]")
    }

    let pid = try parsePid(args[0])
    fputs("info: Target PID: \(pid), Highlight Duration: \(duration) seconds.\n", stderr)
    let response = try MacosUseSDK.traverseAccessibilityTree(pid: pid, onlyVisibleElements: true)
    let highlightDuration = duration
    await MainActor.run {
        MacosUseSDK.drawHighlightBoxes(for: response.elements, duration: highlightDuration)
    }
    try jsonPrint(response)
    try await Task.sleep(nanoseconds: UInt64((duration + 0.2) * 1_000_000_000))
}

func runInput(_ args: [String], visual: Bool) async throws {
    guard let action = args.first?.lowercased() else {
        throw ToolFailure.usage("usage: TactileMacosTool \(visual ? "visual" : "input") <action> [args...]")
    }

    var rest = Array(args.dropFirst())
    var duration = visual ? 0.5 : 0.0
    if visual, let index = rest.firstIndex(of: "--duration") {
        guard index + 1 < rest.count, let parsed = Double(rest[index + 1]), parsed > 0 else {
            throw ToolFailure.usage("invalid --duration value")
        }
        duration = parsed
        rest.remove(at: index + 1)
        rest.remove(at: index)
    }

    switch action {
    case "keypress":
        guard rest.count == 1 else {
            throw ToolFailure.usage("'keypress' requires exactly one argument")
        }
        let (keyCode, flags) = try keyCodeAndFlags(rest[0])
        if visual {
            try MacosUseSDK.pressKeyAndVisualize(keyCode: keyCode, flags: flags, duration: duration > 0 ? duration : 0.8)
        } else {
            try MacosUseSDK.pressKey(keyCode: keyCode, flags: flags)
        }

    case "click", "doubleclick", "rightclick", "mousemove":
        let point = try parsePoint(rest, usage: "'\(action)' requires <x> <y>")
        switch (action, visual) {
        case ("click", true):
            try MacosUseSDK.clickMouseAndVisualize(at: point, duration: duration)
        case ("click", false):
            try MacosUseSDK.clickMouse(at: point)
        case ("doubleclick", true):
            try MacosUseSDK.doubleClickMouseAndVisualize(at: point, duration: duration)
        case ("doubleclick", false):
            try MacosUseSDK.doubleClickMouse(at: point)
        case ("rightclick", true):
            try MacosUseSDK.rightClickMouseAndVisualize(at: point, duration: duration)
        case ("rightclick", false):
            try MacosUseSDK.rightClickMouse(at: point)
        case ("mousemove", true):
            try MacosUseSDK.moveMouseAndVisualize(to: point, duration: duration)
        case ("mousemove", false):
            try MacosUseSDK.moveMouse(to: point)
        default:
            break
        }

    case "scroll":
        guard rest.count == 3 || rest.count == 4,
              let x = Double(rest[0]),
              let y = Double(rest[1]),
              let deltaY = Int32(rest[2]) else {
            throw ToolFailure.usage("'scroll' requires <x> <y> <deltaY> [deltaX]")
        }
        let deltaX = rest.count == 4 ? Int32(rest[3]) : 0
        guard let finalDeltaX = deltaX else {
            throw ToolFailure.usage("invalid deltaX for 'scroll'")
        }
        let point = CGPoint(x: x, y: y)
        if visual {
            try MacosUseSDK.scrollWheelAndVisualize(at: point, deltaY: deltaY, deltaX: finalDeltaX, duration: duration)
        } else {
            try MacosUseSDK.scrollWheel(at: point, deltaY: deltaY, deltaX: finalDeltaX)
        }

    case "writetext":
        guard rest.count == 1 else {
            throw ToolFailure.usage("'writetext' requires exactly one argument")
        }
        if visual {
            try MacosUseSDK.writeTextAndVisualize(rest[0], duration: duration)
        } else {
            try MacosUseSDK.writeText(rest[0])
        }

    case "axactivate", "axpress", "axfocus":
        guard !visual, rest.count == 2 else {
            throw ToolFailure.usage("'\(action)' requires <pid> <ax_path>")
        }
        let pid = try parsePid(rest[0])
        switch action {
        case "axactivate":
            try MacosUseSDK.activateAccessibilityElement(pid: pid, atPath: rest[1])
        case "axpress":
            try MacosUseSDK.pressAccessibilityElement(pid: pid, atPath: rest[1])
        case "axfocus":
            try MacosUseSDK.focusAccessibilityElement(pid: pid, atPath: rest[1])
        default:
            break
        }

    case "axselect":
        guard !visual, rest.count == 2 || rest.count == 3 else {
            throw ToolFailure.usage("'axselect' requires <pid> <ax_path> [true|false]")
        }
        let pid = try parsePid(rest[0])
        let selected = rest.count == 3 ? ["true", "1", "yes", "y"].contains(rest[2].lowercased()) : true
        try MacosUseSDK.setAccessibilitySelected(pid: pid, atPath: rest[1], selected: selected)

    case "axsetvalue":
        guard !visual, rest.count == 3 else {
            throw ToolFailure.usage("'axsetvalue' requires <pid> <ax_path> <text>")
        }
        let pid = try parsePid(rest[0])
        try MacosUseSDK.setAccessibilityValue(pid: pid, atPath: rest[1], value: rest[2])

    default:
        throw ToolFailure.usage("unsupported action: \(action)")
    }

    if visual {
        try await Task.sleep(nanoseconds: UInt64((duration + 0.2) * 1_000_000_000))
    }
}

@main
struct TactileMacosTool {
    static func main() async {
        var args = CommandLine.arguments
        args.removeFirst()
        guard let command = args.first?.lowercased() else {
            printUsage()
            exit(1)
        }
        let rest = Array(args.dropFirst())

        do {
            switch command {
            case "open":
                try await runOpen(rest)
            case "traverse":
                try runTraverse(rest)
            case "highlight":
                try await runHighlight(rest)
            case "input":
                try await runInput(rest, visual: false)
            case "visual":
                try await runInput(rest, visual: true)
            default:
                throw ToolFailure.usage("unsupported command: \(command)")
            }
            exit(0)
        } catch let error as MacosUseSDKError {
            fputs("❌ Error from MacosUseSDK: \(error.localizedDescription)\n", stderr)
            exit(1)
        } catch {
            fputs("❌ Error: \(error.localizedDescription)\n", stderr)
            exit(1)
        }
    }
}
