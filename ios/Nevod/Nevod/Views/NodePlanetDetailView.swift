import SwiftUI

/// Detail screen for a single planet — its admin-published cell list (bots to chat with,
/// static "landing page" cells) fetched via NODE_CELLS_REQUEST. See node.py's
/// _handle_node_cells_request and NodeManifest.swift for the trust model.
///
/// Group chats ("moons" in the original approved mockup, design_mockups/Main.dc.html) are
/// NOT rendered here yet — the iOS app has no group/child-node membership model at all today
/// (see MD_Discuss/DISCUSS_GROUPS.md; the backend feature exists and is tested, node/,
/// tests/test_groups.py, but nothing on the client tracks "which child nodes am I in"). This
/// is a real, known gap, not an oversight — revisit once that membership model exists.
struct NodePlanetDetailView: View {
    let node: ExploreNode
    @EnvironmentObject var store: AppStore

    @State private var cells: [PublishedCell] = []
    @State private var isLoading = true
    @State private var loadFailed = false
    @State private var showSetup = false

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
        ScrollView {
            VStack(spacing: 16) {
                PlanetView(purpose: purpose, verified: isVerified, isHome: node.isHome)
                    .frame(height: 96)
                    .padding(.top, 8)

                VStack(spacing: 4) {
                    Text(displayName)
                        .font(.title2.bold())
                        .foregroundStyle(.white)
                    Text(badgeLabel)
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(purpose.badgeColor)
                        .padding(.horizontal, 10).padding(.vertical, 4)
                        .background(purpose.badgeColor.opacity(0.18), in: Capsule())
                    Text(node.address)
                        .font(.footnote)
                        .foregroundStyle(.white.opacity(0.4))

                    // Entry point into real (named) registration on THIS specific planet —
                    // distinct from PublishedCellRow.handleTap()'s silent anonymous join,
                    // which stays scoped to messaging one particular bot. Only one node can
                    // be "home" at a time (no multi-node membership model yet), so hidden once
                    // actually admitted somewhere — but gating on isRegistered alone (as before)
                    // hid this for anyone who'd merely picked a display name and gotten stuck at
                    // "invite required" (pendingInviteMode != nil), leaving them with NO path to
                    // ever request access. Confirmed on device 2026-09-13: a fresh identity sat
                    // in "invite required" with this button gone and nowhere else offering
                    // "Request access" either.
                    //
                    // Also needs !IdentityStore.hasEverConnected: isRegistered only reflects
                    // "a display name was chosen at some point" (see its own doc comment) — it
                    // stays permanently true even for an identity that picked a name once, never
                    // got admitted anywhere (no live NACK right now either, so pendingInviteMode
                    // is nil too), and is just idly browsing NodesView. RootView itself already
                    // treats "never actually connected" as the real signal for staying in the
                    // browsing/join flow — this button needs the same signal, or it silently
                    // vanishes with no way back in. Confirmed on device 2026-09-18: exactly this
                    // state (isRegistered=true from an earlier attempt, pendingInviteMode=nil,
                    // hasEverConnected=false) showed a bare loading planet page with no join
                    // button and no name prompt at all.
                    if !store.isRegistered || store.pendingInviteMode != nil || !IdentityStore.hasEverConnected {
                        Button("Join this node") {
                            IdentityStore.nodeAddr = node.address
                            showSetup = true
                        }
                        .buttonStyle(.borderedProminent)
                        .padding(.top, 8)
                    }
                }

                Rectangle().fill(Color.white.opacity(0.08)).frame(height: 1).padding(.horizontal, 24)

                Group {
                    if isLoading {
                        ProgressView().tint(.white).padding(.top, 24)
                    } else if cells.isEmpty {
                        ContentUnavailableView(
                            loadFailed ? "Couldn't reach this node" : "Nothing published here yet",
                            systemImage: "circle.dashed"
                        )
                        .padding(.top, 8)
                    } else {
                        LazyVStack(spacing: 10) {
                            ForEach(cells) { cell in
                                PublishedCellRow(cell: cell, node: node)
                            }
                        }
                        .padding(.horizontal, 16)
                    }
                }
            }
            .padding(.bottom, 32)
        }
        .scrollContentBackground(.hidden)
        .background(NodeSkyBackground())
        .navigationTitle(displayName)
        .skyNavigationTitle(Text(verbatim: displayName))
        .task { await load() }
        // The home-node connection observably flaps every 10-30s in practice (confirmed via
        // device logs 2026-08-27: reconnect churn on this exact websocket) — landing on this
        // screen during one of those brief disconnected windows previously showed "Nothing
        // published here yet" indistinguishable from a genuinely empty list (see load()'s own
        // comment). Retrying once the socket comes back covers that window without the user
        // needing to back out and re-enter the screen.
        .onChange(of: store.connectionStatus) { _, status in
            if status == "connected" { Task { await load() } }
        }
        .sheet(isPresented: $showSetup) { SetupView() }
    }

    private func load() async {
        isLoading = true
        defer { isLoading = false }
        // Also true while mid-join-request on a non-home planet (Dev Planet, say) — not just
        // the literal "home" node. Reusing the already-live connection here isn't just an
        // optimization: opening a SEPARATE NodeCellsBrowser connection with the SAME identity
        // while a persistent one is already registered under that same cell_id causes a real
        // server-side bug (ConnectionRegistry.add() in transport.py silently overwrites the
        // registry slot for that peer_node_id, and the probe's own disconnect moments later
        // wipes the slot entirely) — messages/acks addressed to this identity then find "no
        // connection" and sit buffered, or get silently dropped, until the persistent client
        // happens to reconnect for some other reason. Confirmed on device 2026-09-19: exactly
        // this made delivered/read receipts stop arriving while chatting with the admin during
        // a pending join request, right after this same planet-detail screen had been open.
        let usesLiveConnection = node.isHome
            || (store.client?.isConnected == true && store.client?.activeAddr == node.address)
        if usesLiveConnection {
            // Deliberately NOT `try?` — that swallowed "socket isn't connected right now"
            // (NevdError.notConnected) into the same empty [] as "asked, node said nothing is
            // published", both rendering as "Nothing published here yet" with no way to tell
            // them apart. loadFailed distinguishes them, same as the non-home NodeCellsBrowser
            // path below already did — this branch just never set it.
            do {
                cells = try await store.client?.getNodeCells() ?? []
                loadFailed = false
            } catch {
                loadFailed = true
            }
            return
        }
        guard let identity = store.identity else { return }
        let fingerprint = manifestInfo?.tlsFingerprint
        do {
            cells = try await NodeCellsBrowser.fetch(
                nodeAddr: node.address,
                expectedFingerprint: (fingerprint?.isEmpty == false) ? fingerprint : nil,
                identity: identity
            )
        } catch {
            loadFailed = true
        }
    }
}

// MARK: - Cell row

private struct PublishedCellRow: View {
    let cell: PublishedCell
    let node: ExploreNode
    @EnvironmentObject var store: AppStore
    @State private var chatContact: Contact?
    @State private var showPage = false

    private var isBot: Bool { cell.kind == "bot" }

    var body: some View {
        Button(action: handleTap) {
            HStack(spacing: 12) {
                Image(systemName: isBot ? "bubble.left.and.bubble.right.fill" : "doc.text.fill")
                    .font(.system(size: 15))
                    .foregroundStyle(isBot ? Color(red: 0.39, green: 0.71, blue: 1.0)
                                            : Color(red: 1.00, green: 0.69, blue: 0.40))
                    .frame(width: 34, height: 34)
                    .background(Color.white.opacity(0.08), in: Circle())

                VStack(alignment: .leading, spacing: 2) {
                    Text(cell.name)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundStyle(.white)
                    if !cell.description.isEmpty {
                        Text(cell.description)
                            .font(.system(size: 12))
                            .foregroundStyle(.white.opacity(0.5))
                            .lineLimit(1)
                    }
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(.white.opacity(0.3))
            }
            .padding(12)
            .background(Color.white.opacity(0.045), in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.white.opacity(0.07), lineWidth: 1))
        }
        .buttonStyle(.plain)
        .navigationDestination(item: $chatContact) { contact in ChatGateView(contact: contact) }
        .navigationDestination(isPresented: $showPage) {
            MarkdownPageView(title: cell.name, markdown: cell.landingMd ?? "")
        }
    }

    private func handleTap() {
        guard isBot else { showPage = true; return }
        // No form, no interruption — silently register under a generated name if this is a
        // browsing-only identity (see AppStore.registerAnonymously). The chat opens right away;
        // ChatView already shows "Подключение…" and disables sending until the connection this
        // kicks off actually completes (build 148), so there's nothing else to wait for here.
        if !store.isRegistered {
            store.registerAnonymously(nodeAddr: node.address)
        }
        guard let encPub = cell.encPubkey else { return }
        store.registerAIBot(cellId: cell.cellId, providers: cell.aiProviders)
        let contact = Contact(cellId: cell.cellId, nodeAddr: node.address, encPub: encPub,
                              alias: cell.name, nodeId: node.nodeId)
        store.addContact(contact)
        chatContact = contact
    }
}
