import SwiftUI
import WidgetKit

/// Home screen: one question, fill now or wait.
///
/// Setup runs once. After that this view reloads JSON, flattens it with the
/// stored selection, and tells WidgetKit to refresh from the same cache.
struct RootView: View {
    @Environment(FuelSettingsStore.self) private var settingsStore
    @State private var loadedPayload: LoadedFuelPayload?
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showingSettings = false

    private let service = FuelDataService()

    private var snapshot: FuelSnapshot? {
        guard let loadedPayload, let selection = settingsStore.selection else { return nil }
        return FuelSnapshotBuilder.build(loadedPayload: loadedPayload, selection: selection)
    }

    var body: some View {
        Group {
            if settingsStore.hasCompletedOnboarding {
                dashboard
            } else {
                SetupView { region, fuelType, tankSizeLitres in
                    settingsStore.save(region: region, fuelType: fuelType, tankSizeLitres: tankSizeLitres)
                    Task { await loadData() }
                }
            }
        }
        .background(LiquidGoldTheme.backgroundSecondary.ignoresSafeArea())
        .task {
            await loadData()
        }
    }

    private var dashboard: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header
                    if let snapshot {
                        SnapshotHero(snapshot: snapshot)
                        MetricGrid(snapshot: snapshot)
                        RecommendationPanel(snapshot: snapshot)
                    } else if isLoading {
                        ProgressView()
                            .tint(LiquidGoldTheme.hardwareBlack)
                    } else {
                        MissingDataPanel(message: errorMessage ?? "Unable to load fuel data.")
                    }
                }
                .padding(16)
            }
            .navigationTitle("Liquid Gold")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Reload") {
                        Task { await loadData() }
                    }
                    .font(.system(.subheadline, design: .monospaced).weight(.semibold))
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Settings") {
                        showingSettings = true
                    }
                    .font(.system(.subheadline, design: .rounded).weight(.bold))
                }
            }
            .sheet(isPresented: $showingSettings) {
                if let current = settingsStore.selection {
                    SettingsView(initialSelection: current) { selection in
                        settingsStore.update(selection: selection)
                        showingSettings = false
                    }
                    .presentationDetents([.medium])
                }
            }
            .refreshable {
                await loadData()
            }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("FUEL TIMING")
                .font(.system(size: 12, weight: .bold, design: .rounded))
                .tracking(1.2)
            Text("Should you fill now or wait?")
                .font(.system(.title3, design: .rounded).weight(.bold))
            Text(snapshot?.statusText ?? (isLoading ? "Loading live pricing..." : "Waiting for your selection"))
                .font(.system(.footnote, design: .monospaced))
                .foregroundStyle(LiquidGoldTheme.textSecondary)
        }
        .foregroundStyle(LiquidGoldTheme.hardwareBlack)
    }

    @MainActor
    private func loadData() async {
        isLoading = true
        defer { isLoading = false }
        do {
            loadedPayload = try await service.loadPayload()
            errorMessage = nil
            WidgetCenter.shared.reloadAllTimelines()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

/// First-launch form. Tank size is only used for the rand-impact estimate.
private struct SetupView: View {
    @State private var region: RegionType = .coastal
    @State private var fuelType: FuelType = .petrol95
    @State private var tankSizeLitres: Int = AppConfig.defaultTankSizeLitres
    let onContinue: (RegionType, FuelType, Int) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            Spacer()
            Text("LIQUID GOLD")
                .font(.system(size: 40, weight: .heavy, design: .rounded))
            Text("Choose your region, fuel, and tank size once. Liquid Gold only answers one question: fill now or wait.")
                .font(.system(.body, design: .default))
                .foregroundStyle(LiquidGoldTheme.textSecondary)
            PickerPanel(title: "Region", options: RegionType.allCases, selection: $region) { $0.title }
            PickerPanel(title: "Fuel", options: FuelType.allCases, selection: $fuelType) { $0.title }
            TankSizePanel(tankSizeLitres: $tankSizeLitres)
            Button {
                onContinue(region, fuelType, tankSizeLitres)
            } label: {
                Text("Continue")
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(LiquidGoldTheme.signal)
                    .foregroundStyle(LiquidGoldTheme.hardwareBlack)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(LiquidGoldTheme.hardwareBlack, lineWidth: 2)
                    )
            }
            .buttonStyle(.plain)
            Spacer()
        }
        .padding(20)
        .background(LiquidGoldTheme.backgroundSecondary.ignoresSafeArea())
    }
}

private struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var selection: FuelSelection
    let onSave: (FuelSelection) -> Void

    init(initialSelection: FuelSelection, onSave: @escaping (FuelSelection) -> Void) {
        _selection = State(initialValue: initialSelection)
        self.onSave = onSave
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                PickerPanel(title: "Region", options: RegionType.allCases, selection: $selection.region) { $0.title }
                PickerPanel(title: "Fuel", options: FuelType.allCases, selection: $selection.fuelType) { $0.title }
                TankSizePanel(tankSizeLitres: $selection.tankSizeLitres)
                Button("Save") {
                    onSave(selection)
                    dismiss()
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(LiquidGoldTheme.signal)
                .foregroundStyle(LiquidGoldTheme.hardwareBlack)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(LiquidGoldTheme.hardwareBlack, lineWidth: 2)
                )
                .buttonStyle(.plain)
                Spacer()
            }
            .padding(20)
            .background(LiquidGoldTheme.backgroundSecondary.ignoresSafeArea())
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

private struct TankSizePanel: View {
    @Binding var tankSizeLitres: Int

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Tank Size".uppercased())
                .font(.system(size: 12, weight: .bold, design: .rounded))
                .tracking(1.0)
            HStack {
                Text("\(tankSizeLitres)L")
                    .font(.system(.title3, design: .monospaced).weight(.bold))
                Spacer()
                Stepper("", value: $tankSizeLitres, in: 20...120, step: 5)
                    .labelsHidden()
            }
            Text("Used to estimate the cost impact on your next fill.")
                .font(.system(.footnote, design: .default))
                .foregroundStyle(LiquidGoldTheme.textSecondary)
        }
        .utilityPanel(background: LiquidGoldTheme.backgroundPrimary, shadow: 4)
    }
}

private struct PickerPanel<Option: Hashable>: View {
    let title: String
    let options: [Option]
    @Binding var selection: Option
    let label: (Option) -> String

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title.uppercased())
                .font(.system(size: 12, weight: .bold, design: .rounded))
                .tracking(1.0)
            HStack(spacing: 10) {
                ForEach(options, id: \.self) { option in
                    Button {
                        selection = option
                    } label: {
                        Text(label(option))
                            .font(.system(.subheadline, design: .monospaced).weight(.semibold))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(selection == option ? LiquidGoldTheme.signal : LiquidGoldTheme.backgroundPrimary)
                            .foregroundStyle(LiquidGoldTheme.hardwareBlack)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(LiquidGoldTheme.hardwareBlack, lineWidth: 2)
                            )
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .utilityPanel(background: LiquidGoldTheme.backgroundPrimary, shadow: 4)
    }
}

/// LCD-style price panel. Orange is reserved for the selected control, not this readout.
private struct SnapshotHero: View {
    let snapshot: FuelSnapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("\(snapshot.selection.region.title) • \(snapshot.selection.fuelType.title)")
                .font(.system(size: 12, weight: .bold, design: .rounded))
                .tracking(1)
            Text(PriceFormatter.currencyPerLitre(cents: snapshot.currentPrice))
                .font(.system(size: 38, weight: .bold, design: .monospaced))
            HStack(spacing: 12) {
                ChangeBadge(change: snapshot.change)
                Text(snapshot.recommendationText)
                    .font(.system(.headline, design: .rounded).weight(.bold))
            }
        }
        .foregroundStyle(LiquidGoldTheme.lcdDark)
        .utilityPanel(background: LiquidGoldTheme.lcd, shadow: 6)
    }
}

private struct MetricGrid: View {
    let snapshot: FuelSnapshot

    var body: some View {
        VStack(spacing: 14) {
            HStack(spacing: 14) {
                MetricCard(title: "Next Price", value: PriceFormatter.currencyPerLitre(cents: snapshot.nextPrice))
                MetricCard(title: "Tank Impact", value: PriceFormatter.rand(snapshot.estimatedTankImpact))
            }
            HStack(spacing: 14) {
                MetricCard(title: "Next Adjustment", value: PriceFormatter.shortDate(snapshot.nextAdjustmentDate))
                MetricCard(title: "Best Fill Date", value: PriceFormatter.shortDate(snapshot.bestFillUpDate))
            }
        }
    }
}

private struct MetricCard: View {
    let title: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title.uppercased())
                .font(.system(size: 11, weight: .bold, design: .rounded))
                .tracking(0.8)
            Text(value)
                .font(.system(.title3, design: .monospaced).weight(.bold))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .foregroundStyle(LiquidGoldTheme.hardwareBlack)
        .utilityPanel(background: LiquidGoldTheme.backgroundPrimary, shadow: 4)
    }
}

private struct RecommendationPanel: View {
    let snapshot: FuelSnapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Recommendation".uppercased())
                .font(.system(size: 11, weight: .bold, design: .rounded))
                .tracking(0.8)
            Text(snapshot.recommendationText)
                .font(.system(.title3, design: .rounded).weight(.bold))
            Text(snapshot.recommendationBody)
                .font(.system(.headline, design: .rounded))
            Text(impactLine)
                .font(.system(.subheadline, design: .monospaced).weight(.semibold))
            Text(snapshot.confidenceText)
                .font(.system(.footnote, design: .monospaced))
                .foregroundStyle(LiquidGoldTheme.textSecondary)
            Text(reasonLine)
                .font(.system(.subheadline, design: .default))
                .foregroundStyle(LiquidGoldTheme.textSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .foregroundStyle(LiquidGoldTheme.hardwareBlack)
        .utilityPanel(background: LiquidGoldTheme.signalMuted, shadow: 4)
    }

    private var impactLine: String {
        guard let impact = snapshot.estimatedTankImpact else { return "Tank impact unavailable." }
        if impact > 0 {
            return "Waiting likely costs about \(PriceFormatter.randAmount(impact)) on a \(snapshot.selection.tankSizeLitres)L fill."
        }
        if impact < 0 {
            return "Waiting likely saves about \(PriceFormatter.randAmount(impact)) on a \(snapshot.selection.tankSizeLitres)L fill."
        }
        return "No material cost change on a \(snapshot.selection.tankSizeLitres)L fill."
    }

    private var reasonLine: String {
        guard let change = snapshot.change else { return snapshot.statusText }
        if change > 0 { return "Projected up \(PriceFormatter.delta(cents: change)) by the next adjustment." }
        if change < 0 { return "Projected down \(PriceFormatter.delta(cents: change)) by the next adjustment." }
        return "Projected flat by the next adjustment."
    }
}

private struct MissingDataPanel: View {
    let message: String

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("No Data")
                .font(.system(.headline, design: .rounded).weight(.bold))
            Text(message)
                .font(.system(.body, design: .default))
        }
        .foregroundStyle(LiquidGoldTheme.hardwareBlack)
        .utilityPanel(background: LiquidGoldTheme.backgroundPrimary, shadow: 4)
    }
}

private struct ChangeBadge: View {
    let change: Int?

    private var background: Color {
        guard let change else { return LiquidGoldTheme.backgroundPrimary }
        return change > 0 ? LiquidGoldTheme.signalMuted : Color(red: 0.882, green: 0.945, blue: 0.910)
    }

    var body: some View {
        Text(PriceFormatter.delta(cents: change))
            .font(.system(.subheadline, design: .monospaced).weight(.bold))
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(background)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(LiquidGoldTheme.hardwareBlack, lineWidth: 2)
            )
    }
}

#Preview {
    RootView()
        .environment(FuelSettingsStore())
}
