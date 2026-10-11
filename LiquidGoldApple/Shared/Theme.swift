import SwiftUI

public enum LiquidGoldTheme {
    public static let background = Color(red: 0.075, green: 0.079, blue: 0.075)
    public static let panel = Color(red: 0.125, green: 0.133, blue: 0.125)
    public static let ink = Color(red: 0.936, green: 0.918, blue: 0.867)
    public static let muted = Color(red: 0.648, green: 0.646, blue: 0.615)
    public static let rule = Color(red: 0.310, green: 0.322, blue: 0.302)

    public static func mono(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .monospaced)
    }
}

public struct PanelStyle: ViewModifier {
    public func body(content: Content) -> some View {
        content
            .padding(18)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(LiquidGoldTheme.panel)
            .overlay(Rectangle().stroke(LiquidGoldTheme.rule, lineWidth: 1))
    }
}

public extension View {
    func instrumentPanel() -> some View {
        modifier(PanelStyle())
    }
}

public struct PriceVectorGraphic: View {
    public let change: Int
    public let columns: Int
    public let rows: Int

    public init(change: Int, columns: Int = 21, rows: Int = 7) {
        self.change = change
        self.columns = columns
        self.rows = rows
    }

    public var body: some View {
        Canvas { context, size in
            let left = size.width * 0.10
            let right = size.width * 0.90
            let middle = size.height * 0.5
            let travel = min(CGFloat(change.magnitude) / 100, 1) * size.height * 0.34
            let nextY = middle - (change > 0 ? travel : -travel)

            for column in 0..<columns {
                for row in 0..<rows {
                    let point = CGPoint(x: left + CGFloat(column) * (right - left) / CGFloat(columns - 1),
                                        y: size.height * 0.12 + CGFloat(row) * size.height * 0.75 / CGFloat(rows - 1))
                    context.fill(Path(ellipseIn: CGRect(x: point.x - 1.5, y: point.y - 1.5, width: 3, height: 3)),
                                 with: .color(LiquidGoldTheme.rule))
                }
            }
            var path = Path()
            path.move(to: CGPoint(x: left, y: middle))
            path.addLine(to: CGPoint(x: right, y: nextY))
            context.stroke(path, with: .color(LiquidGoldTheme.ink), style: StrokeStyle(lineWidth: 2))
            for point in [CGPoint(x: left, y: middle), CGPoint(x: right, y: nextY)] {
                context.fill(Path(ellipseIn: CGRect(x: point.x - 6, y: point.y - 6, width: 12, height: 12)),
                             with: .color(LiquidGoldTheme.ink))
                context.fill(Path(ellipseIn: CGRect(x: point.x - 2, y: point.y - 2, width: 4, height: 4)),
                             with: .color(LiquidGoldTheme.panel))
            }
        }
    }
}
