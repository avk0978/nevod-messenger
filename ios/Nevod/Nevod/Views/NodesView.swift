import SwiftUI

/// Read-only directory of publicly joinable ("open" access) nodes this node knows about via
/// gossip — see node.py's _handle_node_list_request. A node also present (with a valid
/// signature) in the bundled curator manifest (NodeManifest.swift) renders with its purpose and
/// a "verified" ring; any other open node still shows, muted, as a plain unbadged planet — per
/// design_mockups/nevod-nodes-as-planets.html and MD_Discuss/DISCUSS_NODE_ADMISSION.md's "3. UI
/// — бейдж 'проверено'". Browse-only for now: no "switch to this node" action here, that's
/// handled separately (SetupView's "Change server…").
struct NodesView: View {
    @EnvironmentObject var store: AppStore
    @State private var isLoading = false
    @State private var searchText = ""
    @State private var showSetup = false
    @State private var showGuide = false
    @State private var setupAfterGuide = false
    // The first-registration guide (RegistrationGuideView) opens by itself once, on the first
    // visit to this screen before signing up; the "?" button reopens it.
    @AppStorage("nevod.registrationGuideSeen") private var guideSeen = false

    /// Own home node always comes first, regardless of what node_list_request returns — a
    /// closed home node can never appear there itself (that query is access=="open"-only, see
    /// node.py), yet it's the one node every member trivially already has access to browse.
    /// See MD_Discuss note: "домашняя нода объединяет все ваши устройства" — this is that
    /// node's entry point on this screen, not just another discovered node.
    ///
    /// Only once this node has actually admitted the cell: an open connection alone isn't
    /// membership — a closed node completes the handshake and only then NACKs
    /// "invite required", and that node used to show up here as "Home" anyway (device test
    /// 2026-10-16, Kitaevo before the invite code was entered).
    private var homeEntry: ExploreNode? {
        guard let client = store.client, !client.nodeId.isEmpty, !client.activeAddr.isEmpty,
              store.isRegistered, IdentityStore.hasEverConnected,
              client.status != "invite required", client.status != "invite invalid" else {
            return nil
        }
        return ExploreNode(nodeId: client.nodeId, name: homeNodeName(client), address: client.activeAddr, isHome: true)
    }

    /// The home planet's own name (a project node's comes from the manifest in the card
    /// itself): the node list if the node is open, else the node-signed administrator record
    /// (a closed node isn't in that list), else the domain. Was a hardcoded "Home" (VPS test
    /// 2026-10-30: the iPad showed "Home" where the iPhone showed "Test VPS").
    private func homeNodeName(_ client: NevdClient) -> String {
        let listed = store.publicNodes.first { $0.nodeId == client.nodeId }?.name ?? ""
        if !listed.isEmpty { return listed }
        let admin = store.nodeAdministrators.values.first { $0.nodeId == client.nodeId }?.nodeName ?? ""
        if !admin.isEmpty { return admin }
        return String(client.activeAddr.split(whereSeparator: { $0 == "/" || $0 == ":" }).first ?? "")
    }

    private var allNodes: [ExploreNode] {
        let home = homeEntry
        let discovered = store.publicNodes
            .filter { $0.nodeId != home?.nodeId }
            .map { node -> ExploreNode in
                // A manifest-listed node's address is hand-curated to be the real externally-
                // reachable one — a node's own self-reported address can be an internal one
                // nothing outside can dial (e.g. behind a reverse proxy), see NodeManifest.swift.
                let address = store.verifiedNodes[node.nodeId]?.address ?? node.address
                return ExploreNode(nodeId: node.nodeId, name: node.name, address: address, isHome: false,
                                   tlsFingerprint: node.tlsFingerprint)
            }
        let discoveredIds = Set(discovered.map { $0.nodeId })
        // Curated manifest nodes not already surfaced via gossip. This is what makes the open
        // segment browsable with zero live connection: fetchVerifiedNodes() is a plain HTTPS
        // fetch (no identity/client needed), while publicNodes needs an authenticated client —
        // which a browsing-only user (no home node yet) doesn't have. Without this, the manifest
        // loads fine but never renders, and NodesView shows "No public nodes found" even though
        // there are verified nodes to explore.
        let verifiedOnly = store.verifiedNodes
            .filter { $0.key != home?.nodeId && !discoveredIds.contains($0.key) }
            .map { nodeId, info in
                ExploreNode(nodeId: nodeId, name: info.name, address: info.address, isHome: false)
            }
        return (home.map { [$0] } ?? []) + discovered + verifiedOnly
    }

    private var filteredNodes: [ExploreNode] {
        guard !searchText.isEmpty else { return allNodes }
        return allNodes.filter {
            $0.name.localizedCaseInsensitiveContains(searchText) ||
            $0.address.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                if allNodes.isEmpty && !isLoading {
                    ContentUnavailableView("No public nodes found", systemImage: "network",
                        description: Text("Known open nodes on the network will appear here"))
                        .padding(.top, 60)
                } else {
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 14) {
                        ForEach(filteredNodes) { node in
                            NavigationLink(value: node) {
                                NodePlanetCard(node: node)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(16)
                }
            }
            .scrollContentBackground(.hidden)
            .background(NodeSkyBackground())
            .searchable(text: $searchText, prompt: "Search nodes")
            .navigationTitle("Explore Network")
            .skyNavigationTitle(Text("Explore Network"))
            .toolbar {
                // See NodePlanetDetailView's matching "Join this node" comment (2026-09-18
                // update) — isRegistered/pendingInviteMode alone left anyone with a
                // never-actually-admitted identity (hasEverConnected == false) stuck with no
                // way back into SetupView's Request-access UI at all.
                if !store.isRegistered || store.pendingInviteMode != nil || !IdentityStore.hasEverConnected {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button { showSetup = true } label: {
                            Label("Start messaging", systemImage: "person.badge.plus")
                        }
                    }
                    ToolbarItem(placement: .topBarLeading) {
                        Button { showGuide = true } label: {
                            Label("Как зарегистрироваться", systemImage: "questionmark.circle")
                        }
                    }
                }
            }
            .navigationDestination(for: ExploreNode.self) { node in
                NodePlanetDetailView(node: node)
            }
            .refreshable { await refresh() }
            .task { await refresh() }
            .sheet(isPresented: $showSetup) { SetupView() }
            .sheet(isPresented: $showGuide, onDismiss: {
                guideSeen = true
                if setupAfterGuide { setupAfterGuide = false; showSetup = true }
            }) {
                RegistrationGuideView(onStart: { setupAfterGuide = true; showGuide = false },
                                      onBrowse: { showGuide = false })
            }
            // Invite link (AppStore.handleOpenURL): open the form, SetupView fills it in.
            .onAppear {
                if store.pendingInviteLink != nil { showSetup = true }
                else if !guideSeen && !store.isRegistered { showGuide = true }
            }
            .onChange(of: store.pendingInviteLink) { _, token in if token != nil { showSetup = true } }
        }
    }

    private func refresh() async {
        isLoading = true
        async let nodes: Void = store.fetchPublicNodes()
        async let manifest: Void = store.fetchVerifiedNodes()
        _ = await (nodes, manifest)
        isLoading = false
    }
}

// MARK: - Explore node model

/// Unifies "own home node" (always shown, never comes from node_list_request) and any
/// discovered NevdClient.PublicNode into one type the planets grid + detail screen share.
struct ExploreNode: Identifiable, Hashable {
    let nodeId: String
    let name: String
    let address: String
    let isHome: Bool
    var tlsFingerprint: String = ""
    var id: String { nodeId }
}

// MARK: - Planet card

private struct NodePlanetCard: View {
    let node: ExploreNode
    @EnvironmentObject var store: AppStore

    private var manifestInfo: VerifiedNodeInfo? { store.verifiedNodes[node.nodeId] }
    private var purpose: NodePurpose { NodePurpose(rawValue: manifestInfo?.purpose ?? "") ?? .generic }
    private var isVerified: Bool { manifestInfo != nil }
    private var displayName: String {
        let manifestName = manifestInfo?.name ?? ""
        if !manifestName.isEmpty { return manifestName }
        return node.name.isEmpty ? String(node.nodeId.prefix(12)) + "…" : node.name
    }
    private var badgeLabel: String { node.isHome ? String(localized: "Домашняя") : purpose.label }

    var body: some View {
        VStack(spacing: 8) {
            PlanetView(purpose: purpose, verified: isVerified, isHome: node.isHome)
                .frame(height: 84)
            VStack(spacing: 3) {
                HStack(spacing: 4) {
                    // Closed: by invitation or with the administrator's approval. Not on the
                    // home planet — its member is already in.
                    if !node.isHome && store.isClosedNode(node.nodeId) {
                        Image(systemName: "lock.fill")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundStyle(.white.opacity(0.75))
                            .accessibilityLabel(Text("Закрытый узел"))
                    }
                    Text(displayName)
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(.white)
                        .lineLimit(1)
                }
                Text(badgeLabel)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(purpose.badgeColor)
                    .padding(.horizontal, 8).padding(.vertical, 3)
                    .background(purpose.badgeColor.opacity(0.18), in: Capsule())
                Text(node.address)
                    .font(.system(size: 12))
                    .foregroundStyle(.white.opacity(0.4))
                    .lineLimit(1)
            }
        }
        .padding(.vertical, 18).padding(.horizontal, 10)
        .frame(maxWidth: .infinity)
        .background(Color.white.opacity(0.045), in: RoundedRectangle(cornerRadius: 18))
        .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color.white.opacity(0.07), lineWidth: 1))
        .opacity(isVerified || node.isHome ? 1.0 : 0.72)
    }
}

// MARK: - Planet kinds

enum NodePurpose: String {
    case informational, aiAgent = "ai_agent", community, generic

    var label: String {
        switch self {
        case .informational: String(localized: "Informational")
        case .aiAgent:        String(localized: "AI Agent")
        case .community:      String(localized: "Community")
        case .generic:        String(localized: "Open Node")
        }
    }

    var badgeColor: Color {
        switch self {
        case .informational: Color(red: 0.31, green: 0.84, blue: 0.60)
        case .aiAgent:        Color(red: 0.39, green: 0.71, blue: 1.00)
        case .community:      Color(red: 1.00, green: 0.69, blue: 0.40)
        case .generic:        Color.white.opacity(0.55)
        }
    }
}

/// Procedural planet — gradients keyed off `purpose`, matching
/// design_mockups/nevod-nodes-as-planets.html's "Main" (procedural) variant. The AI-agent ring
/// is purpose-specific styling; the gold verified ring is a separate, independent visual axis
/// (a community/informational/AI planet can each be verified or not) — see the design doc.
struct PlanetView: View {
    let purpose: NodePurpose
    let verified: Bool
    var isHome: Bool = false

    var body: some View {
        ZStack {
            if purpose == .aiAgent {
                Ellipse()
                    .stroke(Color(red: 0.35, green: 0.75, blue: 1.0).opacity(0.55), lineWidth: 1.5)
                    .frame(width: 104, height: 30)
                    .rotationEffect(.degrees(-14))
            }

            planetBody
                .frame(width: 72, height: 72)
                .clipShape(Circle())
                .overlay(
                    Circle().fill(
                        RadialGradient(colors: [.clear, .black.opacity(0.5)],
                                       center: UnitPoint(x: 0.72, y: 0.74), startRadius: 8, endRadius: 46)
                    )
                )
                .shadow(color: purpose == .generic ? .clear : purpose.badgeColor.opacity(0.3), radius: 10)

            if verified {
                Ellipse()
                    .stroke(
                        LinearGradient(colors: [.yellow.opacity(0.85), .white.opacity(0.6), .yellow.opacity(0.85)],
                                       startPoint: .leading, endPoint: .trailing),
                        lineWidth: 2
                    )
                    .frame(width: 98, height: 24)
                    .rotationEffect(.degrees(12))
            }

            // Independent visual axis from `verified` — a home node's own trust comes from
            // being yours, not from curator sign-off, so this can appear with or without the
            // gold ring (see MD_Discuss note: "домашняя нода объединяет все ваши устройства").
            if isHome {
                Image(systemName: "house.fill")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundStyle(.white)
                    .padding(5)
                    .background(Circle().fill(Color(red: 0.25, green: 0.5, blue: 0.95)))
                    .overlay(Circle().stroke(Color.black.opacity(0.4), lineWidth: 1))
                    .offset(x: 28, y: 26)
            }
        }
        .frame(height: 84)
    }

    @ViewBuilder
    private var planetBody: some View {
        switch purpose {
        case .informational:
            RadialGradient(
                colors: [Color(red: 0.20, green: 0.60, blue: 0.85), Color(red: 0.12, green: 0.48, blue: 0.30),
                         Color(red: 0.08, green: 0.31, blue: 0.56)],
                center: UnitPoint(x: 0.4, y: 0.32), startRadius: 2, endRadius: 46)
        case .aiAgent:
            RadialGradient(
                colors: [Color(red: 0.23, green: 0.27, blue: 0.34), Color(red: 0.08, green: 0.09, blue: 0.12)],
                center: UnitPoint(x: 0.35, y: 0.3), startRadius: 2, endRadius: 50)
        case .community:
            RadialGradient(
                colors: [Color(red: 1.00, green: 0.85, blue: 0.54), Color(red: 0.91, green: 0.53, blue: 0.17),
                         Color(red: 0.64, green: 0.29, blue: 0.10)],
                center: UnitPoint(x: 0.34, y: 0.3), startRadius: 2, endRadius: 46)
        case .generic:
            RadialGradient(
                colors: [Color(red: 0.36, green: 0.37, blue: 0.42), Color(red: 0.14, green: 0.15, blue: 0.17)],
                center: UnitPoint(x: 0.38, y: 0.34), startRadius: 2, endRadius: 46)
        }
    }
}

// MARK: - Background

extension View {
    /// The sky is always black, but the system title takes the system scheme: in light mode
    /// "Explore Network" was black on black (device screenshots 2026-10-19). Neither a dark scheme
    /// for the whole stack (it also darkened the SetupView sheet) nor toolbarColorScheme (iOS 26
    /// left the large title black) fixed it, so the title is drawn here in white. navigationTitle
    /// stays set by the caller — it is still the back button's label on the next screen.
    func skyNavigationTitle(_ title: Text) -> some View {
        self.navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    title.font(.headline).foregroundStyle(.white).lineLimit(1)
                }
            }
    }
}

struct NodeSkyBackground: View {
    var body: some View {
        ZStack {
            Color.black
            RadialGradient(colors: [Color(red: 0.27, green: 0.35, blue: 0.59).opacity(0.20), .clear],
                           center: UnitPoint(x: 0.15, y: 0.05), startRadius: 0, endRadius: 320)
            RadialGradient(colors: [Color(red: 0.35, green: 0.24, blue: 0.55).opacity(0.14), .clear],
                           center: UnitPoint(x: 0.9, y: 0.35), startRadius: 0, endRadius: 300)
        }
        .ignoresSafeArea()
    }
}

/// Short first-registration guide: what a node is, the two ways in (no invitation → Nevod
/// Open; an invitation → its link or code), and how to add people. Requested 2026-11-01 after
/// a visitor tried a bot on a closed node without knowing how registration works.
struct RegistrationGuideView: View {
    let onStart: () -> Void
    let onBrowse: () -> Void
    @State private var page = 0
    private let lastPage = 2

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                TabView(selection: $page) {
                    guidePage(icon: "globe", title: "Nevod — сеть узлов") {
                        Text("Узел — сервер, через который идут ваши сообщения. Вы регистрируетесь на одном узле — это ваш дом в сети. Писать можно людям с любых узлов — для этого нужна карточка собеседника: его контактные данные в Nevod.")
                    }.tag(0)
                    guidePage(icon: "person.badge.plus", title: "Как зарегистрироваться") {
                        VStack(alignment: .leading, spacing: 18) {
                            guideStep(icon: "person.fill", title: "Нет приглашения",
                                      text: "Нажмите «Начать переписку» и введите имя или псевдоним — вы попадёте на узел Nevod Open, он открыт для всех.")
                            guideStep(icon: "envelope.open.fill", title: "Есть приглашение",
                                      text: "Откройте ссылку из приглашения или введите код: «Начать переписку» → «Есть код приглашения?».")
                            HStack(alignment: .top, spacing: 14) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .font(.title3).foregroundStyle(.orange).frame(width: 28)
                                Text("Частные узлы принимают новых участников по приглашению или с одобрения администратора.")
                            }
                        }
                    }.tag(1)
                    guidePage(icon: "person.text.rectangle", title: "Карточка вместо номера телефона") {
                        VStack(alignment: .leading, spacing: 18) {
                            Text("В Nevod нет номеров телефонов и почты. Вместо них у вас карточка контакта — ваш идентификатор в сети: по ней собеседники находят и добавляют вас.")
                            guideStep(icon: "qrcode", title: "Показать",
                                      text: "Профиль → «Поделиться карточкой»: на экране появится QR-код и сама карточка. Собеседник сканирует QR-код своим телефоном.")
                            guideStep(icon: "square.and.arrow.up", title: "Отправить",
                                      text: "Там же «Скопировать» или «Поделиться…»: отправьте карточку текстом — почтой, в SMS, в другом мессенджере.")
                            guideStep(icon: "person.badge.plus", title: "Добавить собеседника",
                                      text: "Контакты → «Добавить контакт» (значок с плюсом): отсканируйте QR-код собеседника или вставьте присланную им карточку.")
                        }
                    }.tag(2)
                }
                .tabViewStyle(.page(indexDisplayMode: .always))
                .indexViewStyle(.page(backgroundDisplayMode: .always))

                VStack(spacing: 10) {
                    if page < lastPage {
                        Button { withAnimation { page += 1 } } label: {
                            Text("Дальше").frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent).controlSize(.large)
                    } else {
                        Button(action: onStart) {
                            Text("Start messaging").frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent).controlSize(.large)
                        Button("Осмотреться", action: onBrowse)
                    }
                }
                .padding(.horizontal, 24).padding(.bottom, 20)
            }
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    if page < lastPage { Button("Пропустить", action: onBrowse) }
                }
            }
        }
    }

    private func guidePage<Content: View>(icon: String, title: LocalizedStringKey,
                                          @ViewBuilder content: () -> Content) -> some View {
        ScrollView {
            VStack(spacing: 20) {
                Image(systemName: icon)
                    .font(.system(size: 56)).foregroundStyle(.tint)
                    .padding(.top, 24)
                Text(title).font(.title2.bold()).multilineTextAlignment(.center)
                content()
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(.horizontal, 28).padding(.bottom, 48)
        }
    }

    private func guideStep(icon: String, title: LocalizedStringKey, text: LocalizedStringKey) -> some View {
        HStack(alignment: .top, spacing: 14) {
            Image(systemName: icon).font(.title3).foregroundStyle(.tint).frame(width: 28)
            VStack(alignment: .leading, spacing: 4) {
                Text(title).font(.headline)
                Text(text).foregroundStyle(.secondary)
            }
        }
    }
}
