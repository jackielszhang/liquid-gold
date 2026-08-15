import SwiftUI
import WidgetKit

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
                case .systemMedium:
                    mediumWidget(snapshot: snapshot)
                default:
                    smallWidget(snapshot: snapshot)
                }
            } else {
                Text("No fuel data")
                    .font(.system(.headline, design: .rounded))
                    .foregroundStyle(LiquidGoldTheme.hardwareBlack)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(LiquidGoldTheme.backgroundPrimary)
            }
        }
        .containerBackground(LiquidGoldTheme.backgroundPrimary, for: .widget)
    }

    private func smallWidget(snapshot: FuelSnapshot) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(snapshot.selection.fuelType.title.uppercased())
                .font(.system(size: 10, weight: .bold, design: .rounded))
                .tracking(0.8)
            Text(PriceFormatter.currencyPerLitre(cents: snapshot.currentPrice))
                .font(.system(size: 24, weight: .bold, design: .monospaced))
            Text(PriceFormatter.delta(cents: snapshot.change))
                .font(.system(.headline, design: .monospaced).weight(.bold))
                .foregroundStyle((snapshot.change ?? 0) > 0 ? LiquidGoldTheme.signal : LiquidGoldTheme.positive)
            Spacer()
            Text("Best: \(PriceFormatter.shortDate(snapshot.bestFillUpDate))")
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
        }
        .foregroundStyle(LiquidGoldTheme.hardwareBlack)
        .padding(14)
        .background(LiquidGoldTheme.lcd)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(LiquidGoldTheme.hardwareBlack, lineWidth: 2)
        )
    }

    private func mediumWidget(snapshot: FuelSnapshot) -> some View {
        HStack(spacing: 14) {
            VStack(alignment: .leading, spacing: 8) {
                Text(snapshot.selection.region.title.uppercased())
                    .font(.system(size: 10, weight: .bold, design: .rounded))
                    .tracking(0.8)
                Text(snapshot.selection.fuelType.title)
                    .font(.system(.headline, design: .rounded).weight(.bold))
                Text(PriceFormatter.currencyPerLitre(cents: snapshot.currentPrice))
                    .font(.system(size: 26, weight: .bold, design: .monospaced))
                Text("Next \(PriceFormatter.currencyPerLitre(cents: snapshot.nextPrice))")
                    .font(.system(.subheadline, design: .monospaced))
            }
            Spacer()
            VStack(alignment: .leading, spacing: 8) {
                Text(PriceFormatter.delta(cents: snapshot.change))
                    .font(.system(.title3, design: .monospaced).weight(.bold))
                    .foregroundStyle((snapshot.change ?? 0) > 0 ? LiquidGoldTheme.signal : LiquidGoldTheme.positive)
                Text("Best \(PriceFormatter.shortDate(snapshot.bestFillUpDate))")
                    .font(.system(.subheadline, design: .monospaced))
                Text("Adj \(PriceFormatter.shortDate(snapshot.nextAdjustmentDate))")
                    .font(.system(.subheadline, design: .monospaced))
                Text(snapshot.recommendationText)
                    .font(.system(size: 11, weight: .semibold, design: .rounded))
                    .lineLimit(2)
            }
        }
        .foregroundStyle(LiquidGoldTheme.hardwareBlack)
        .padding(14)
        .background(LiquidGoldTheme.backgroundPrimary)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(LiquidGoldTheme.hardwareBlack, lineWidth: 2)
        )
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
