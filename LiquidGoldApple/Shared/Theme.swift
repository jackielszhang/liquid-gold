import SwiftUI

public enum LiquidGoldTheme {
    public static let backgroundPrimary = Color(red: 0.961, green: 0.945, blue: 0.957)
    public static let backgroundSecondary = Color(red: 0.910, green: 0.890, blue: 0.898)
    public static let hardwareBlack = Color(red: 0.071, green: 0.071, blue: 0.078)
    public static let signal = Color(red: 1.0, green: 0.290, blue: 0.098)
    public static let signalMuted = Color(red: 1.0, green: 0.878, blue: 0.835)
    public static let lcd = Color(red: 0.835, green: 0.816, blue: 0.718)
    public static let lcdDark = Color(red: 0.141, green: 0.149, blue: 0.122)
    public static let textSecondary = Color(red: 0.337, green: 0.329, blue: 0.353)
    public static let border = hardwareBlack
    public static let positive = Color(red: 0.176, green: 0.416, blue: 0.310)
}

public struct PanelStyle: ViewModifier {
    let background: Color
    let shadow: CGFloat

    public func body(content: Content) -> some View {
        content
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(background)
                    .shadow(color: LiquidGoldTheme.border, radius: 0, x: shadow, y: shadow)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(LiquidGoldTheme.border, lineWidth: 2)
            )
    }
}

public extension View {
    func utilityPanel(background: Color = LiquidGoldTheme.backgroundPrimary, shadow: CGFloat = 5) -> some View {
        modifier(PanelStyle(background: background, shadow: shadow))
    }
}
