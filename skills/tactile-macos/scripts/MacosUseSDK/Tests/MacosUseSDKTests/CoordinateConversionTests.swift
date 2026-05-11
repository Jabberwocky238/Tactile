import XCTest
@testable import MacosUseSDK
import AppKit

final class CoordinateConversionTests: XCTestCase {
    func testTopLeftScreenRectConvertsToAppKitFrameUsingPrimaryTopEdge() {
        let frame = appKitFrameFromTopLeftScreenRect(
            CGRect(x: 61, y: 94, width: 1581, height: 895),
            primaryTopY: 1117
        )

        XCTAssertEqual(frame.origin.x, 61)
        XCTAssertEqual(frame.origin.y, 128)
        XCTAssertEqual(frame.width, 1581)
        XCTAssertEqual(frame.height, 895)
    }

    func testTopLeftScreenRectSupportsDisplaysAbovePrimaryScreen() {
        let frame = appKitFrameFromTopLeftScreenRect(
            CGRect(x: -457, y: -1440, width: 2560, height: 1440),
            primaryTopY: 1117
        )

        XCTAssertEqual(frame.origin.x, -457)
        XCTAssertEqual(frame.origin.y, 1117)
        XCTAssertEqual(frame.width, 2560)
        XCTAssertEqual(frame.height, 1440)
    }

    func testCenteredPointConversionUsesSameCoordinateBridge() {
        let frame = appKitFrameCenteredOnTopLeftScreenPoint(
            CGPoint(x: 100, y: 200),
            size: CGSize(width: 40, height: 20),
            primaryTopY: 1117
        )

        XCTAssertEqual(frame.origin.x, 80)
        XCTAssertEqual(frame.origin.y, 907)
        XCTAssertEqual(frame.width, 40)
        XCTAssertEqual(frame.height, 20)
    }

    @MainActor
    func testOverlayWindowsDoNotInterceptMouseEvents() {
        let window = createOverlayWindow(
            frame: NSRect(x: 0, y: 0, width: 20, height: 20),
            type: .box(text: "AXButton")
        )

        XCTAssertTrue(window.ignoresMouseEvents)
    }
}
