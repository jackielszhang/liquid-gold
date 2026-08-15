import Foundation

public enum PriceFormatter {
    public static func currencyPerLitre(cents: Int?) -> String {
        guard let cents else { return "Unavailable" }
        return String(format: "R%.2f/L", Double(cents) / 100)
    }

    public static func delta(cents: Int?) -> String {
        guard let cents else { return "Unknown" }
        if cents == 0 { return "0c" }
        return String(format: "%@%dc", cents > 0 ? "+" : "", cents)
    }

    public static func shortDate(_ date: Date?) -> String {
        guard let date else { return "Unknown" }
        return date.formatted(.dateTime.day().month(.abbreviated))
    }

    public static func rand(_ amount: Int?) -> String {
        guard let amount else { return "Unknown" }
        let value = Double(abs(amount))
        let prefix = amount > 0 ? "+" : amount < 0 ? "-" : ""
        return String(format: "%@R%.0f", prefix, value)
    }

    public static func randAmount(_ amount: Int?) -> String {
        guard let amount else { return "Unknown" }
        return String(format: "R%.0f", Double(abs(amount)))
    }
}
