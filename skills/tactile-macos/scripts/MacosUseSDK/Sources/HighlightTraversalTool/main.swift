import Foundation
import AppKit // Required for NSApplication and RunLoop
import MacosUseSDK // Your library

// --- Helper Function for Argument Parsing ---
// Simple parser for "--duration <value>", "--input-json <path>", "--no-activate", and PID.
func parseArguments() -> (pid: Int32?, duration: Double?, inputJSONPath: String?, activateApp: Bool) {
    var pid: Int32? = nil
    var duration: Double? = nil
    var inputJSONPath: String? = nil
    var activateApp = true
    var waitingForDurationValue = false
    var waitingForInputJSONValue = false

    // Skip the executable path
    for arg in CommandLine.arguments.dropFirst() {
        if waitingForDurationValue {
            if let durationValue = Double(arg), durationValue > 0 {
                duration = durationValue
            } else {
                fputs("error: Invalid value provided after --duration.\n", stderr)
                return (nil, nil, nil, activateApp) // Indicate parsing error
            }
            waitingForDurationValue = false
        } else if waitingForInputJSONValue {
            inputJSONPath = arg
            waitingForInputJSONValue = false
        } else if arg == "--duration" {
            waitingForDurationValue = true
        } else if arg == "--input-json" {
            waitingForInputJSONValue = true
        } else if arg == "--no-activate" {
            activateApp = false
        } else if pid == nil, let pidValue = Int32(arg) {
            pid = pidValue
        } else {
            fputs("error: Unexpected argument '\(arg)'.\n", stderr)
            return (nil, nil, nil, activateApp) // Indicate parsing error
        }
    }

    // Check if duration flag was seen but value is missing
    if waitingForDurationValue {
        fputs("error: Missing value after --duration flag.\n", stderr)
        return (nil, nil, nil, activateApp)
    }
    if waitingForInputJSONValue {
        fputs("error: Missing value after --input-json flag.\n", stderr)
        return (nil, nil, nil, activateApp)
    }

    // Check if a geometry source was found
    if pid == nil && inputJSONPath == nil {
        fputs("error: Missing required PID argument or --input-json path.\n", stderr)
        return (nil, nil, nil, activateApp)
    }

    return (pid, duration, inputJSONPath, activateApp)
}

// --- Main Execution Logic ---

// 1. Parse Arguments
let (parsedPID, parsedDuration, parsedInputJSONPath, activateApp) = parseArguments()

if parsedPID == nil && parsedInputJSONPath == nil {
    // Error messages printed by parser
    fputs("\nusage: HighlightTraversalTool <PID> [--duration <seconds>] [--no-activate]\n", stderr)
    fputs("       HighlightTraversalTool --input-json <response-json> [--duration <seconds>]\n", stderr)
    fputs("  <PID>: Process ID of the application to highlight.\n", stderr)
    fputs("  --input-json <path>: Draw highlights from an existing traversal JSON payload instead of traversing again.\n", stderr)
    fputs("  --no-activate: Traverse without activating the target app.\n", stderr)
    fputs("  --duration <seconds>: How long the highlights should stay visible (default: 3.0).\n", stderr)
    fputs("\nexample: HighlightTraversalTool 14154 --duration 5\n", stderr)
    exit(1)
}

// Use provided duration or default
let highlightDuration = parsedDuration ?? 3.0

if let targetPID = parsedPID {
    fputs("info: Target PID: \(targetPID), Highlight Duration: \(highlightDuration) seconds, Activate App: \(activateApp).\n", stderr)
} else {
    fputs("info: Input JSON: \(parsedInputJSONPath ?? ""), Highlight Duration: \(highlightDuration) seconds.\n", stderr)
}

// Wrap async calls in a Task
Task {
    do {
        let responseData: ResponseData
        if let inputJSONPath = parsedInputJSONPath {
            fputs("info: Loading highlight elements from existing traversal JSON...\n", stderr)
            let inputURL = URL(fileURLWithPath: inputJSONPath)
            let inputData = try Data(contentsOf: inputURL)
            responseData = try JSONDecoder().decode(ResponseData.self, from: inputData)
            fputs("info: Loaded \(responseData.elements.count) elements from JSON.\n", stderr)
        } else if let targetPID = parsedPID {
            // 2. Perform Traversal FIRST
            fputs("info: Calling traverseAccessibilityTree (visible only)...\n", stderr)
            responseData = try await MacosUseSDK.traverseAccessibilityTree(
                pid: targetPID,
                onlyVisibleElements: true,
                activateApp: activateApp
            )
            fputs("info: Traversal complete. Found \(responseData.elements.count) visible elements.\n", stderr)
        } else {
            throw MacosUseSDKError.internalError("Missing highlight geometry source.")
        }

        // 3. Dispatch Highlighting using the traversal results
        fputs("info: Calling drawHighlightBoxes with \(responseData.elements.count) elements...\n", stderr)
        // Ensure this call happens on the main actor, drawHighlightBoxes requires it.
        // Since we are in a Task, explicitly hop to MainActor.
        await MainActor.run {
            MacosUseSDK.drawHighlightBoxes(for: responseData.elements, duration: highlightDuration)
        }
        fputs("info: drawHighlightBoxes call dispatched successfully.\n", stderr)
        fputs("      Overlays appear/disappear asynchronously on the main thread.\n", stderr)

        // 4. Encode the ResponseData to JSON
        fputs("info: Encoding traversal response to JSON...\n", stderr)
        let encoder = JSONEncoder()
        // Optionally make the output prettier
        // encoder.outputFormatting = [.prettyPrinted, .sortedKeys] // Uncomment for human-readable JSON
        let jsonData = try encoder.encode(responseData)

        // 5. Print JSON to standard output
        guard let jsonString = String(data: jsonData, encoding: .utf8) else {
            throw MacosUseSDKError.internalError("Failed to convert JSON data to UTF-8 string.")
        }
        print(jsonString) // Print JSON to stdout
        fputs("info: Successfully printed JSON response to stdout.\n", stderr)

        // 6. Keep the Main Thread Alive for UI Updates
        // IMPORTANT: Still need this for the visual highlights to appear/disappear
        // We need to schedule this *after* the async work above has potentially returned.
        let waitTime = highlightDuration + 1.0 // Wait a bit longer than the effect
        fputs("info: Keeping the tool alive for \(waitTime) seconds to allow UI updates...\n", stderr)
        // Use DispatchQueue.main.async to schedule the RunLoop wait on the main thread
        DispatchQueue.main.async {
            RunLoop.main.run(until: Date(timeIntervalSinceNow: waitTime))
            fputs("info: Run loop finished. Tool exiting normally.\n", stderr)
            exit(0) // Success
        }
        // Allow the Task itself to stay alive while the main thread waits
         try await Task.sleep(nanoseconds: UInt64((waitTime + 0.1) * 1_000_000_000))
         // Fallback exit if runloop doesn't trigger exit
         exit(0)

    } catch let error as MacosUseSDKError {
        // Specific SDK errors
        fputs("❌ Error from MacosUseSDK: \(error.localizedDescription)\n", stderr)
        exit(1)
    } catch {
        // Other errors (e.g., JSON encoding failure)
        fputs("❌ An unexpected error occurred: \(error.localizedDescription)\n", stderr)
        exit(1)
    }
}

// Keep the process alive so the Task can run
RunLoop.main.run()

/*

swift run HighlightTraversalTool $(swift run AppOpenerTool Messages) --duration 5

*/
