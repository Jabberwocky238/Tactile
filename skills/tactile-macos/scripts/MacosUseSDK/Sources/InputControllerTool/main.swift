import Foundation
import CoreGraphics // For CGPoint, CGEventFlags
import MacosUseSDK // Import the library

// --- Start Time ---
let startTime = Date() // Record start time for the tool's execution

// --- Helper Function for Logging ---
// Tool-specific logging prefix
func log(_ message: String) {
    fputs("InputControllerTool: \(message)\n", stderr)
}

// --- Helper Function for Exiting ---
// Logs final time and exits
func finish(success: Bool, message: String? = nil) -> Never {
    if let msg = message {
        log(success ? "✅ Success: \(msg)" : "❌ Error: \(msg)")
    }

    // --- Calculate and Log Time ---
    let endTime = Date()
    let processingTime = endTime.timeIntervalSince(startTime)
    let formattedTime = String(format: "%.3f", processingTime)
    fputs("InputControllerTool: total execution time: \(formattedTime) seconds\n", stderr)
    // --- End Time Logging ---

    exit(success ? 0 : 1)
}


// --- Argument Parsing and Main Logic ---
let arguments = CommandLine.arguments
let scriptName = arguments.first ?? "InputControllerTool"

// Define usage instructions
let usage = """
usage: \(scriptName) <action> [options...]

actions:
  keypress <key_name_or_code>[+modifier...]   Simulate pressing a key (e.g., 'return', 'a', 'f1', 'cmd+c', 'shift+tab').
                                             Supported modifiers: cmd, shift, opt, ctrl, fn.
  click <x> <y>                 Simulate a left mouse click at screen coordinates.
  doubleclick <x> <y>           Simulate a left mouse double-click at screen coordinates.
  rightclick <x> <y>            Simulate a right mouse click at screen coordinates.
  mousemove <x> <y>             Move the mouse cursor to screen coordinates.
  scroll <x> <y> <deltaY> [deltaX]  Simulate a scroll wheel event at screen coordinates.
  writetext <text_to_type>      Simulate typing a string of text.
  axactivate <pid> <ax_path>    Activate a traversed AX element directly (focus/select/press; no mouse event).
  axpress <pid> <ax_path>       Perform AXPress on a traversed AX element directly.
  axfocus <pid> <ax_path>       Set AXFocused on a traversed AX element directly.
  axselect <pid> <ax_path> [true|false]  Set AXSelected on a traversed AX element directly.
  axsetvalue <pid> <ax_path> <text>      Set AXValue on a traversed AX element directly.

Examples:
  \(scriptName) keypress enter
  \(scriptName) keypress cmd+shift+4
  \(scriptName) click 100 250
  \(scriptName) scroll 500 500 5
  \(scriptName) writetext "Hello World!"
  \(scriptName) axactivate 12345 'app.windows[0].children[3]'
"""

// Check for minimum argument count
guard arguments.count > 1 else {
    fputs(usage, stderr)
    finish(success: false, message: "No action specified.")
}

let action = arguments[1].lowercased()
log("Action: \(action)")

// --- Action Handling ---
do {
    switch action {
    case "keypress":
        guard arguments.count == 3 else {
            throw MacosUseSDKError.inputInvalidArgument("'keypress' requires exactly one argument: <key_name_or_code_with_modifiers>\n\(usage)")
        }
        let keyCombo = arguments[2]
        log("Key Combo Argument: '\(keyCombo)'")
        var keyCode: CGKeyCode?
        var flags: CGEventFlags = []

        // Parse modifiers (cmd, shift, opt, ctrl, fn)
        let parts = keyCombo.split(separator: "+").map { String($0).trimmingCharacters(in: .whitespacesAndNewlines).lowercased() }

        // The last part is the key
        guard let keyPart = parts.last else {
            throw MacosUseSDKError.inputInvalidArgument("Invalid key combination format: '\(keyCombo)'")
        }
        log("Parsing key part: '\(keyPart)'")
        keyCode = MacosUseSDK.mapKeyNameToKeyCode(keyPart) // Use library function

        // Process modifier parts
        if parts.count > 1 {
             log("Parsing modifiers: \(parts.dropLast().joined(separator: ", "))")
            for i in 0..<(parts.count - 1) {
                switch parts[i] {
                    case "cmd", "command": flags.insert(.maskCommand)
                    case "shift": flags.insert(.maskShift)
                    case "opt", "option", "alt": flags.insert(.maskAlternate)
                    case "ctrl", "control": flags.insert(.maskControl)
                    case "fn", "function": flags.insert(.maskSecondaryFn) // Note: 'fn' might need special handling or accessibility settings
                    default: throw MacosUseSDKError.inputInvalidArgument("Unknown modifier: '\(parts[i])' in '\(keyCombo)'")
                }
            }
        }


        guard let finalKeyCode = keyCode else {
            throw MacosUseSDKError.inputInvalidArgument("Unknown key name or invalid key code: '\(keyPart)' in '\(keyCombo)'")
        }

        log("Calling pressKey library function...")
        try MacosUseSDK.pressKey(keyCode: finalKeyCode, flags: flags)
        finish(success: true, message: "Key press '\(keyCombo)' simulated.")

    case "click", "doubleclick", "rightclick", "mousemove":
        guard arguments.count == 4 else {
             throw MacosUseSDKError.inputInvalidArgument("'\(action)' requires exactly two arguments: <x> <y>\n\(usage)")
        }
        guard let x = Double(arguments[2]), let y = Double(arguments[3]) else {
            throw MacosUseSDKError.inputInvalidArgument("Invalid coordinates for '\(action)'. x and y must be numbers.")
        }
        let point = CGPoint(x: x, y: y)
        log("Coordinates: (\(x), \(y))")

        log("Calling \(action) library function...")
        switch action {
            case "click":       try MacosUseSDK.clickMouse(at: point)
            case "doubleclick": try MacosUseSDK.doubleClickMouse(at: point)
            case "rightclick":  try MacosUseSDK.rightClickMouse(at: point)
            case "mousemove":   try MacosUseSDK.moveMouse(to: point)
            default: break // Should not happen
        }
        finish(success: true, message: "\(action) simulated at (\(x), \(y)).")

    case "scroll":
        guard arguments.count == 5 || arguments.count == 6 else {
            throw MacosUseSDKError.inputInvalidArgument("'scroll' requires arguments: <x> <y> <deltaY> [deltaX]\n\(usage)")
        }
        guard let x = Double(arguments[2]), let y = Double(arguments[3]), let deltaY = Int32(arguments[4]) else {
            throw MacosUseSDKError.inputInvalidArgument("Invalid arguments for 'scroll'. x/y must be numbers and deltaY must be an integer.")
        }
        let deltaX: Int32
        if arguments.count == 6 {
            guard let parsedDeltaX = Int32(arguments[5]) else {
                throw MacosUseSDKError.inputInvalidArgument("Invalid deltaX for 'scroll'. deltaX must be an integer.")
            }
            deltaX = parsedDeltaX
        } else {
            deltaX = 0
        }
        let point = CGPoint(x: x, y: y)
        log("Scroll coordinates: (\(x), \(y)), deltaY: \(deltaY), deltaX: \(deltaX)")
        log("Calling scrollWheel library function...")
        try MacosUseSDK.scrollWheel(at: point, deltaY: deltaY, deltaX: deltaX)
        finish(success: true, message: "scroll simulated at (\(x), \(y)) with deltaY \(deltaY), deltaX \(deltaX).")

    case "writetext":
         guard arguments.count == 3 else {
            throw MacosUseSDKError.inputInvalidArgument("'writetext' requires exactly one argument: <text_to_type>\n\(usage)")
        }
        let text = arguments[2]
        log("Text Argument: \"\(text)\"")
        log("Calling writeText library function...")
        try MacosUseSDK.writeText(text)
        finish(success: true, message: "Text writing simulated.")

    case "axactivate", "axpress", "axfocus":
        guard arguments.count == 4 else {
            throw MacosUseSDKError.inputInvalidArgument("'\(action)' requires arguments: <pid> <ax_path>\n\(usage)")
        }
        guard let pid = Int32(arguments[2]) else {
            throw MacosUseSDKError.inputInvalidArgument("Invalid pid for '\(action)': \(arguments[2])")
        }
        let path = arguments[3]
        log("AX PID: \(pid), path: '\(path)'")
        switch action {
        case "axactivate":
            try MacosUseSDK.activateAccessibilityElement(pid: pid, atPath: path)
        case "axpress":
            try MacosUseSDK.pressAccessibilityElement(pid: pid, atPath: path)
        case "axfocus":
            try MacosUseSDK.focusAccessibilityElement(pid: pid, atPath: path)
        default:
            break
        }
        finish(success: true, message: "\(action) performed for AX path '\(path)'.")

    case "axselect":
        guard arguments.count == 4 || arguments.count == 5 else {
            throw MacosUseSDKError.inputInvalidArgument("'axselect' requires arguments: <pid> <ax_path> [true|false]\n\(usage)")
        }
        guard let pid = Int32(arguments[2]) else {
            throw MacosUseSDKError.inputInvalidArgument("Invalid pid for 'axselect': \(arguments[2])")
        }
        let path = arguments[3]
        let selected: Bool
        if arguments.count == 5 {
            switch arguments[4].lowercased() {
            case "true", "1", "yes", "y":
                selected = true
            case "false", "0", "no", "n":
                selected = false
            default:
                throw MacosUseSDKError.inputInvalidArgument("Invalid selected value for 'axselect': \(arguments[4])")
            }
        } else {
            selected = true
        }
        log("AX select PID: \(pid), path: '\(path)', selected: \(selected)")
        try MacosUseSDK.setAccessibilitySelected(pid: pid, atPath: path, selected: selected)
        finish(success: true, message: "axselect performed for AX path '\(path)'.")

    case "axsetvalue":
        guard arguments.count == 5 else {
            throw MacosUseSDKError.inputInvalidArgument("'axsetvalue' requires arguments: <pid> <ax_path> <text>\n\(usage)")
        }
        guard let pid = Int32(arguments[2]) else {
            throw MacosUseSDKError.inputInvalidArgument("Invalid pid for 'axsetvalue': \(arguments[2])")
        }
        let path = arguments[3]
        let value = arguments[4]
        log("AX set value PID: \(pid), path: '\(path)', value length: \(value.count)")
        try MacosUseSDK.setAccessibilityValue(pid: pid, atPath: path, value: value)
        finish(success: true, message: "axsetvalue performed for AX path '\(path)'.")

    default:
        fputs(usage, stderr)
        throw MacosUseSDKError.inputInvalidArgument("Unknown action '\(action)'")
    }

} catch let error as MacosUseSDKError {
    // Handle specific SDK errors
    finish(success: false, message: "MacosUseSDK Error: \(error.localizedDescription)")
} catch {
    // Handle other unexpected errors
     finish(success: false, message: "An unexpected error occurred: \(error.localizedDescription)")
}

// Should not be reached due to finish() calls, but satisfies the compiler
exit(0)

/*
# Example: Open Calculator and type 2*3=
swift run AppOpenerTool Calculator
# (Wait a moment or use the PID from above if needed)
swift run InputControllerTool writetext "2*3="
*/
