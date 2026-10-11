import SwiftUI
import WidgetKit
import LiquidGoldShared

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
        .preferredColorScheme(.dark)
        .tint(LiquidGoldTheme.ink)
        .background(LiquidGoldTheme.background.ignoresSafeArea())
        .task { await loadData() }
    }

    private var dashboard: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    header
                    if let snapshot {
                        SnapshotHero(snapshot: snapshot)
                        PriceSignal(snapshot: snapshot)
                        RecommendationPanel(snapshot: snapshot)
                        MetricGrid(snapshot: snapshot)
                    } else if isLoading {
                        ProgressView("READING DATA")
                            .font(LiquidGoldTheme.mono(12, weight: .bold))
                            .padding(.top, 40)
                    } else {
                        MissingDataPanel(message: errorMessage ?? "Unable to load fuel data.")
                    }
                    Text("LIQUID GOLD   /   FUEL INTELLIGENCE")
                        .font(LiquidGoldTheme.mono(10, weight: .medium))
                        .tracking(1)
                        .foregroundStyle(LiquidGoldTheme.muted)
                        .padding(.vertical, 20)
                }
                .padding(.horizontal, 18)
                .padding(.top, 12)
            }
            .background(LiquidGoldTheme.background)
            .toolbar(.hidden, for: .navigationBar)
            .sheet(isPresented: $showingSettings) {
                if let current = settingsStore.selection {
                    SettingsView(initialSelection: current) { selection in
                        settingsStore.update(selection: selection)
                        showingSettings = false
                    }
                    .presentationDetents([.large])
                }
            }
            .refreshable { await loadData() }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(alignment: .top) {
                Text("LG / 001")
                    .font(LiquidGoldTheme.mono(13, weight: .bold))
                    .tracking(1)
                Spacer()
                Button {
                    Task { await loadData() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .frame(width: 44, height: 44)
                }
                .accessibilityLabel("Reload fuel data")
                Button {
                    showingSettings = true
                } label: {
                    Image(systemName: "slider.horizontal.3")
                        .frame(width: 44, height: 44)
                }
                .accessibilityLabel("Settings")
            }
            .foregroundStyle(LiquidGoldTheme.ink)
            .font(LiquidGoldTheme.mono(19))
            Text("FUEL\nTIMING")
                .font(LiquidGoldTheme.mono(48, weight: .black))
                .tracking(-3)
                .lineSpacing(-8)
                .fixedSize(horizontal: false, vertical: true)
                .foregroundStyle(LiquidGoldTheme.ink)
            HStack(spacing: 9) {
                Circle().fill(LiquidGoldTheme.ink).frame(width: 6, height: 6)
                Text(snapshot?.statusText.uppercased() ?? (isLoading ? "READING LIVE DATA" : "AWAITING DATA"))
                    .font(LiquidGoldTheme.mono(11, weight: .medium))
                    .tracking(0.6)
                    .foregroundStyle(LiquidGoldTheme.muted)
            }
            Rectangle().fill(LiquidGoldTheme.rule).frame(height: 1)
        }
        .padding(.bottom, 10)
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

private struct SetupView: View {
    @State private var region: RegionType = .coastal
    @State private var fuelType: FuelType = .petrol95
    @State private var tankSizeLitres: Int = AppConfig.defaultTankSizeLitres
    let onContinue: (RegionType, FuelType, Int) -> Void

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("LG / INITIAL CONFIGURATION")
                    .font(LiquidGoldTheme.mono(11, weight: .bold))
                    .tracking(1)
                    .foregroundStyle(LiquidGoldTheme.muted)
                    .padding(.top, 36)
                Text("FUEL\nTIMING")
                    .font(LiquidGoldTheme.mono(48, weight: .black))
                    .tracking(-3)
                    .foregroundStyle(LiquidGoldTheme.ink)
                Text("Set your region, fuel and tank size to see when to fill.")
                    .font(LiquidGoldTheme.mono(14))
                    .foregroundStyle(LiquidGoldTheme.muted)
                    .padding(.bottom, 12)
                PickerPanel(title: "01 / REGION", options: RegionType.allCases, selection: $region) { $0.title }
                PickerPanel(title: "02 / FUEL", options: FuelType.allCases, selection: $fuelType) { $0.title }
                TankSizePanel(tankSizeLitres: $tankSizeLitres)
                ActionButton(title: "SHOW MY SIGNAL", action: {
                    onContinue(region, fuelType, tankSizeLitres)
                })
            }
            .padding(18)
        }
        .background(LiquidGoldTheme.background.ignoresSafeArea())
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
            ScrollView {
                VStack(spacing: 14) {
                    PickerPanel(title: "01 / REGION", options: RegionType.allCases, selection: $selection.region) { $0.title }
                    PickerPanel(title: "02 / FUEL", options: FuelType.allCases, selection: $selection.fuelType) { $0.title }
                    TankSizePanel(tankSizeLitres: $selection.tankSizeLitres)
                    ActionButton(title: "SAVE CONFIGURATION", action: {
                        onSave(selection)
                        dismiss()
                    })
                }
                .padding(18)
            }
            .background(LiquidGoldTheme.background.ignoresSafeArea())
            .navigationTitle("")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(LiquidGoldTheme.background, for: .navigationBar)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    Text("CONFIGURATION")
                        .font(LiquidGoldTheme.mono(13, weight: .bold))
                        .tracking(1)
                        .foregroundStyle(LiquidGoldTheme.ink)
                }
            }
        }
    }
}

private struct ActionButton: View {
    let title: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                Text(title)
                Spacer()
                Image(systemName: "arrow.up.right")
            }
            .font(LiquidGoldTheme.mono(14, weight: .bold))
            .padding(18)
            .frame(maxWidth: .infinity)
            .foregroundStyle(LiquidGoldTheme.background)
            .background(LiquidGoldTheme.ink)
        }
        .buttonStyle(.plain)
    }
}

private struct TankSizePanel: View {
    @Binding var tankSizeLitres: Int

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            PanelLabel(text: "03 / TANK SIZE")
            HStack {
                Text("\(tankSizeLitres) L")
                    .font(LiquidGoldTheme.mono(30, weight: .bold))
                Spacer()
                Stepper("Tank size in litres", value: $tankSizeLitres, in: 20...120, step: 5)
                    .labelsHidden()
                    .tint(LiquidGoldTheme.ink)
            }
            Text("Used to estimate the cost of your next fill.")
                .font(LiquidGoldTheme.mono(11))
                .foregroundStyle(LiquidGoldTheme.muted)
        }
        .foregroundStyle(LiquidGoldTheme.ink)
        .instrumentPanel()
    }
}

private struct PickerPanel<Option: Hashable>: View {
    let title: String
    let options: [Option]
    @Binding var selection: Option
    let label: (Option) -> String

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelLabel(text: title)
            HStack(spacing: 8) {
                ForEach(options, id: \.self) { option in
                    Button {
                        selection = option
                    } label: {
                        Text(label(option).uppercased())
                            .font(LiquidGoldTheme.mono(12, weight: .bold))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 15)
                            .foregroundStyle(selection == option ? LiquidGoldTheme.background : LiquidGoldTheme.ink)
                            .background(selection == option ? LiquidGoldTheme.ink : LiquidGoldTheme.panel)
                            .overlay(Rectangle().stroke(LiquidGoldTheme.rule, lineWidth: 1))
                    }
                    .buttonStyle(.plain)
                    .accessibilityAddTraits(selection == option ? .isSelected : [])
                }
            }
        }
        .instrumentPanel()
    }
}

private struct PanelLabel: View {
    let text: String

    var body: some View {
        Text(text)
            .font(LiquidGoldTheme.mono(11, weight: .bold))
            .tracking(1.2)
            .foregroundStyle(LiquidGoldTheme.muted)
    }
}

private struct SnapshotHero: View {
    let snapshot: FuelSnapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                PanelLabel(text: "01 / PUMP PRICE")
                Spacer()
                Image(systemName: "asterisk")
                    .font(LiquidGoldTheme.mono(16, weight: .bold))
            }
            Text(PriceFormatter.currencyPerLitre(cents: snapshot.currentPrice))
                .font(LiquidGoldTheme.mono(45, weight: .bold))
                .minimumScaleFactor(0.65)
                .lineLimit(1)
                .tracking(-2)
            HStack {
                Text(snapshot.selection.fuelType.title.uppercased())
                Spacer()
                Text(snapshot.selection.region.title.uppercased())
            }
            .font(LiquidGoldTheme.mono(11, weight: .bold))
            .tracking(0.6)
            Rectangle().fill(LiquidGoldTheme.rule).frame(height: 1)
            HStack {
                Text("NEXT / \(PriceFormatter.currencyPerLitre(cents: snapshot.nextPrice))")
                Spacer()
                Text(PriceFormatter.delta(cents: snapshot.change))
                    .fontWeight(.bold)
            }
            .font(LiquidGoldTheme.mono(12))
        }
        .foregroundStyle(LiquidGoldTheme.ink)
        .instrumentPanel()
    }
}

private struct PriceSignal: View {
    let snapshot: FuelSnapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                PanelLabel(text: "02 / PRICE VECTOR")
                Spacer()
                Text("C/L")
                    .font(LiquidGoldTheme.mono(11, weight: .bold))
                    .foregroundStyle(LiquidGoldTheme.muted)
            }
            if let change = snapshot.change {
                PriceVectorGraphic(change: change)
                    .frame(height: 142)
                    .accessibilityHidden(true)
            } else {
                Text("PROJECTION UNAVAILABLE")
                    .font(LiquidGoldTheme.mono(12, weight: .bold))
                    .foregroundStyle(LiquidGoldTheme.muted)
                    .frame(height: 142)
            }
            HStack {
                Text("NOW")
                Spacer()
                Text("NEXT ADJUSTMENT")
            }
            .font(LiquidGoldTheme.mono(10, weight: .bold))
            .tracking(0.6)
            .foregroundStyle(LiquidGoldTheme.muted)
            Text("\(PriceFormatter.delta(cents: snapshot.change)) PER LITRE")
                .font(LiquidGoldTheme.mono(24, weight: .bold))
                .foregroundStyle(LiquidGoldTheme.ink)
                .accessibilityLabel("Projected price change: \(PriceFormatter.delta(cents: snapshot.change)) per litre")
            if snapshot.change != nil {
                Text("VECTOR SHOWS DIRECTION; UP TO 100C SCALE")
                    .font(LiquidGoldTheme.mono(9))
                    .foregroundStyle(LiquidGoldTheme.muted)
            }
        }
        .instrumentPanel()
    }
}

private struct RecommendationPanel: View {
    let snapshot: FuelSnapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelLabel(text: "03 / DECISION")
            Text(snapshot.recommendationText.uppercased())
                .font(LiquidGoldTheme.mono(30, weight: .black))
                .minimumScaleFactor(0.7)
                .fixedSize(horizontal: false, vertical: true)
            Text(snapshot.recommendationBody)
                .font(LiquidGoldTheme.mono(13))
                .foregroundStyle(LiquidGoldTheme.muted)
            Rectangle().fill(LiquidGoldTheme.rule).frame(height: 1)
            Text(impactLine)
                .font(LiquidGoldTheme.mono(12, weight: .bold))
            Text(snapshot.confidenceText.uppercased())
                .font(LiquidGoldTheme.mono(10))
                .foregroundStyle(LiquidGoldTheme.muted)
        }
        .foregroundStyle(LiquidGoldTheme.ink)
        .instrumentPanel()
    }

    private var impactLine: String {
        guard let impact = snapshot.estimatedTankImpact else { return "Tank impact unavailable." }
        if impact > 0 { return "WAITING COSTS ~\(PriceFormatter.randAmount(impact)) / \(snapshot.selection.tankSizeLitres)L" }
        if impact < 0 { return "WAITING SAVES ~\(PriceFormatter.randAmount(impact)) / \(snapshot.selection.tankSizeLitres)L" }
        return "NO MATERIAL COST CHANGE / \(snapshot.selection.tankSizeLitres)L"
    }
}

private struct MetricGrid: View {
    let snapshot: FuelSnapshot

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            MetricCard(title: "04 / ADJUSTMENT", value: PriceFormatter.shortDate(snapshot.nextAdjustmentDate))
            MetricCard(title: "05 / BEST FILL", value: PriceFormatter.shortDate(snapshot.bestFillUpDate))
        }
    }
}

private struct MetricCard: View {
    let title: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelLabel(text: title)
            Text(value.uppercased())
                .font(LiquidGoldTheme.mono(17, weight: .bold))
                .minimumScaleFactor(0.75)
                .lineLimit(1)
                .foregroundStyle(LiquidGoldTheme.ink)
        }
        .instrumentPanel()
    }
}

private struct MissingDataPanel: View {
    let message: String

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            PanelLabel(text: "00 / SIGNAL UNAVAILABLE")
            Text(message)
                .font(LiquidGoldTheme.mono(14))
                .foregroundStyle(LiquidGoldTheme.ink)
        }
        .instrumentPanel()
    }
}

#Preview {
    RootView()
        .environment(FuelSettingsStore())
}
