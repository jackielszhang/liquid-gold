import SwiftUI
import WidgetKit
import LiquidGoldShared

/// Home-screen widget backed by the same JSON and settings as the app.
///
/// Refresh is six-hourly because the official price only moves once a month;
/// more frequent polls would not change the answer.

struct LiquidGoldEntry: TimelineEntry {
    let date: Date
    let snapshot: FuelSnapshot?
}

struct LiquidGoldProvider: TimelineProvider {
    private let service = FuelDataService()

    func placeholder(in context: Context) -> LiquidGoldEntry {
        LiquidGoldEntry(date: .now, snapshot: bundledSnapshot())
    }

    func getSnapshot(in context: Context, completion: @escaping (LiquidGoldEntry) -> Void) {
        Task {
            completion(await loadEntry())
        }
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<LiquidGoldEntry>) -> Void) {
        Task {
            let entry = await loadEntry()
            let nextUpdate = Calendar.current.date(byAdding: .hour, value: 6, to: .now) ?? .now.addingTimeInterval(21600)
            completion(Timeline(entries: [entry], policy: .after(nextUpdate)))
        }
    }

    private func bundledSnapshot() -> FuelSnapshot? {
        guard
            let payload = try? service.loadBundledPayload(),
            let selection = FuelSettingsStore.loadSelection() ?? FuelSelection(region: .coastal, fuelType: .petrol95) as FuelSelection?
        else {
            return nil
        }
        return FuelSnapshotBuilder.build(
            loadedPayload: LoadedFuelPayload(payload: payload, source: .bundled),
            selection: selection
        )
    }

    private func loadEntry() async -> LiquidGoldEntry {
        let selection = FuelSettingsStore.loadSelection() ?? FuelSelection(region: .coastal, fuelType: .petrol95)
        let loadedPayload = (try? await service.loadPayload()) ?? (try? service.loadBundledPayload()).map { LoadedFuelPayload(payload: $0, source: .bundled) }
        let snapshot = loadedPayload.flatMap { FuelSnapshotBuilder.build(loadedPayload: $0, selection: selection) }
        return LiquidGoldEntry(date: .now, snapshot: snapshot)
    }
}

struct LiquidGoldWidgetEntryView: View {
    @Environment(\.widgetFamily) private var family
    let entry: LiquidGoldEntry

    var body: some View {
        Group {
            if let snapshot = entry.snapshot {
                switch family {
                case .systemMedium: mediumWidget(snapshot: snapshot)
                default: smallWidget(snapshot: snapshot)
                }
            } else {
                Text("SIGNAL UNAVAILABLE")
                    .font(LiquidGoldTheme.mono(13, weight: .bold))
                    .foregroundStyle(LiquidGoldTheme.ink)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .containerBackground(LiquidGoldTheme.background, for: .widget)
    }

    private func smallWidget(snapshot: FuelSnapshot) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                Text("LG / \(snapshot.selection.fuelType == .petrol95 ? "P95" : "D50")")
                Spacer()
                Text(snapshot.isStale ? "STALE" : "LIVE")
            }
            .font(LiquidGoldTheme.mono(9, weight: .bold))
            .tracking(0.5)
            .foregroundStyle(LiquidGoldTheme.muted)
            Text(PriceFormatter.currencyPerLitre(cents: snapshot.currentPrice))
                .font(LiquidGoldTheme.mono(22, weight: .bold))
                .minimumScaleFactor(0.7)
                .lineLimit(1)
            if let change = snapshot.change {
                PriceVectorGraphic(change: change, columns: 9, rows: 3)
                    .frame(height: 28)
                    .accessibilityHidden(true)
            }
            Rectangle().fill(LiquidGoldTheme.rule).frame(height: 1)
            HStack {
                Text(PriceFormatter.delta(cents: snapshot.change))
                    .font(LiquidGoldTheme.mono(17, weight: .bold))
                Spacer()
                Text("C/L")
                    .font(LiquidGoldTheme.mono(9, weight: .bold))
                    .foregroundStyle(LiquidGoldTheme.muted)
            }
            Text(shortAction(snapshot.recommendationAction))
                .font(LiquidGoldTheme.mono(11, weight: .bold))
                .lineLimit(1)
        }
        .foregroundStyle(LiquidGoldTheme.ink)
        .padding(11)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
        .background(LiquidGoldTheme.panel)
        .overlay(Rectangle().stroke(LiquidGoldTheme.rule, lineWidth: 1))
    }

    private func mediumWidget(snapshot: FuelSnapshot) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("LG / PRICE SIGNAL")
                Spacer()
                Text(snapshot.isStale ? "STALE" : "LIVE")
            }
            .font(LiquidGoldTheme.mono(9, weight: .bold))
            .tracking(0.5)
            .foregroundStyle(LiquidGoldTheme.muted)
            HStack(alignment: .bottom, spacing: 12) {
                VStack(alignment: .leading, spacing: 5) {
                    Text(PriceFormatter.currencyPerLitre(cents: snapshot.currentPrice))
                        .font(LiquidGoldTheme.mono(27, weight: .bold))
                        .minimumScaleFactor(0.7)
                        .lineLimit(1)
                    Text("\(snapshot.selection.fuelType.title.uppercased()) / \(snapshot.selection.region.title.uppercased())")
                        .font(LiquidGoldTheme.mono(9, weight: .bold))
                        .lineLimit(1)
                        .minimumScaleFactor(0.8)
                }
                Spacer(minLength: 0)
                VStack(alignment: .trailing, spacing: 5) {
                    Text(PriceFormatter.delta(cents: snapshot.change))
                        .font(LiquidGoldTheme.mono(24, weight: .bold))
                    Text("NEXT / \(PriceFormatter.shortDate(snapshot.nextAdjustmentDate).uppercased())")
                        .font(LiquidGoldTheme.mono(9, weight: .bold))
                        .foregroundStyle(LiquidGoldTheme.muted)
                }
            }
            if let change = snapshot.change {
                PriceVectorGraphic(change: change, columns: 17, rows: 3)
                    .frame(height: 38)
                    .accessibilityHidden(true)
            }
            Rectangle().fill(LiquidGoldTheme.rule).frame(height: 1)
            Text(snapshot.recommendationText.uppercased())
                .font(LiquidGoldTheme.mono(10, weight: .bold))
                .lineLimit(1)
                .minimumScaleFactor(0.8)
        }
        .foregroundStyle(LiquidGoldTheme.ink)
        .padding(12)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
        .background(LiquidGoldTheme.panel)
        .overlay(Rectangle().stroke(LiquidGoldTheme.rule, lineWidth: 1))
    }

    private func shortAction(_ action: String) -> String {
        switch action {
        case "fill_now": "FILL NOW"
        case "wait": "WAIT"
        case "fill_normally": "FILL NORMALLY"
        default: "CHECK FORECAST"
        }
    }

}

@main
struct LiquidGoldWidgetBundle: WidgetBundle {
    var body: some Widget {
        LiquidGoldWidget()
    }
}

struct LiquidGoldWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "LiquidGoldWidget", provider: LiquidGoldProvider()) { entry in
            LiquidGoldWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("Liquid Gold")
        .description("Fuel timing for your selected region and fuel type.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

#Preview(as: .systemSmall) {
    LiquidGoldWidget()
} timeline: {
    LiquidGoldEntry(
        date: .now,
        snapshot: FuelSnapshotBuilder.build(
            loadedPayload: LoadedFuelPayload(payload: try! FuelDataService(bundle: .main).loadBundledPayload(), source: .bundled),
            selection: FuelSelection(region: .coastal, fuelType: .petrol95)
        )
    )
}
