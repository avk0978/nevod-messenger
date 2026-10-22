import SwiftUI

struct SetupView: View {
    @EnvironmentObject var store: AppStore
    @Environment(\.dismiss) private var dismiss
    @State private var displayName = ""
    @State private var inviteCode = ""
    @State private var showInviteField = false
    @State private var showScanner = false
    @State private var error: String? = nil
    @State private var loading = false
    // "Name taken" must be acknowledged, not just flashed: the client keeps retrying, and
    // a red caption under the form was easy to miss (device test 2026-10-13). Once per
    // "Get started" tap — the retries would otherwise pop it again every ~20 s.
    @State private var showNameTakenAlert = false
    @State private var nameTakenAlerted = false
    @State private var submitted = false   // "Get started" tapped in this presentation
    @State private var serverAddr = IdentityStore.nodeAddr
    @State private var showServerField = false
    @State private var pinnedFingerprint = ""
    @State private var pinnedAddress = ""  // address the fingerprint above was pinned for

    var body: some View {
        NavigationStack {
            if store.joinRequestDenied {
                deniedView
            } else if store.joinRequestPending {
                waitingForApprovalView
            } else {
                setupFormView
            }
        }
    }

    // invite_mode="admin" registration channel — a JOIN_REQUEST was sent and acked, the
    // node hasn't admitted this cell yet. Two independent ways this screen finds out the
    // request was decided: a real-time JOIN_REQUEST_RESOLVED over this same connection if
    // it's still open (AppStore's onJoinRequestResolved — near-instant, but only reaches a
    // client that's actually connected at the exact moment an admin decides), and this
    // view's own "Check again" plus AppStore.retryPendingJoinRequestIfNeeded() (called on
    // every app-foreground) for everyone else — a request can realistically sit pending for
    // days, so a background nudge alone isn't enough to rely on.
    private var waitingForApprovalView: some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "clock.badge.checkmark").font(.system(size: 56)).foregroundStyle(.tint)
            Text("Waiting for approval").font(.title2.bold())
            Text("Your request was sent to the node administrator. You'll be notified once it's approved.")
                .multilineTextAlignment(.center).foregroundStyle(.secondary)
                .padding(.horizontal, 32)
            Button("Check again") { store.retryPendingJoinRequestIfNeeded() }
                .buttonStyle(.bordered)
            Spacer()
        }
        .padding()
    }

    /// Shown when a JOIN_REQUEST_RESOLVED{approved:false} arrives while this device is
    /// still connected — without this, a denial looked identical to still-pending (the
    /// waiting screen stayed up forever with nothing telling the user it was actually
    /// over). A denial that happens while this device is offline still shows up as
    /// silence, same as before — no push is sent for a denial, only approval — but at
    /// least the common "admin was watching and just said no" case is no longer a dead end.
    private var deniedView: some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "xmark.circle").font(.system(size: 56)).foregroundStyle(.secondary)
            Text("Request denied").font(.title2.bold())
            Text("The node administrator declined your request to join.")
                .multilineTextAlignment(.center).foregroundStyle(.secondary)
                .padding(.horizontal, 32)
            Button("Close") {
                store.joinRequestDenied = false
                dismiss()
            }
            .buttonStyle(.borderedProminent)
            Spacer()
        }
        .padding()
    }

    private var setupFormView: some View {
        VStack(spacing: 24) {
                Spacer()
                Image(systemName: "bubble.left.and.bubble.right")
                    .font(.system(size: 64)).foregroundStyle(.tint)
                Text("Nevod").font(.largeTitle.bold())
                Text("Encrypted messenger").foregroundStyle(.secondary)
                Spacer()
                VStack(spacing: 12) {
                    TextField("Your display name", text: $displayName)
                        .textFieldStyle(.roundedBorder).autocorrectionDisabled()
                    if showServerField {
                        TextField("Server address", text: $serverAddr)
                            .textFieldStyle(.roundedBorder).autocorrectionDisabled()
                            .textInputAutocapitalization(.never)
                            .keyboardType(.URL)
                    } else {
                        Button("Change server…") { showServerField = true }
                            .font(.caption)
                    }
                    if showInviteField {
                        HStack {
                            TextField("XXXX-XXXX", text: $inviteCode)
                                .textFieldStyle(.roundedBorder).autocorrectionDisabled()
                                .textInputAutocapitalization(.characters)
                                .onChange(of: inviteCode) { _, newValue in applyInviteInput(newValue) }
                            Button { showScanner = true } label: {
                                Image(systemName: "qrcode.viewfinder").font(.title2)
                            }
                        }
                    } else {
                        Button("Have an invite code?") { showInviteField = true }
                            .font(.caption)
                    }
                    if store.pendingInviteMode == "admin" {
                        // The join request is sent automatically the moment this node NACKs
                        // CELL_REGISTER with invite_mode="admin" (see AppStore.onInviteRequired)
                        // — no separate button. There's nothing left for the user to decide at
                        // this point (they already chose to join this node); a manual step here
                        // only added a screen state to keep in sync with RootView/SetupView's
                        // presentation logic, which broke three times in a row before this.
                        HStack(spacing: 8) {
                            ProgressView()
                            Text("This node requires administrator approval. Sending your request…")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        .padding(.top, 4)
                    }
                    if let err = error {
                        Text(err).foregroundStyle(.red).font(.caption)
                    }
                    Button(action: setup) {
                        if loading { ProgressView() }
                        else { Text("Get started").frame(maxWidth: .infinity) }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(displayName.trimmingCharacters(in: .whitespaces).isEmpty || loading)
                }
                .padding(.horizontal)
                Spacer()
            }
            .padding()
            .onReceive(store.objectWillChange) { handleStatusChange() }
            .sheet(isPresented: $showScanner) {
                QRScannerSheet { code in inviteCode = code }
            }
            // When shown as a sheet from NodesView (browsing-only user registering), close
            // automatically once registration succeeds. No-op when SetupView is the RootView
            // fallback itself (nothing presenting it) — RootView's own gate swaps away from it.
            //
            // Deliberately keyed on connectionStatus=="connected", not isRegistered:
            // isRegistered flips true the instant createIdentity() is called (see AppStore's
            // own doc comment on that property) — long before the server has actually admitted
            // the cell. Dismissing on isRegistered closed this sheet immediately after tapping
            // "Get started," before a CELL_REGISTER NACK{invite_required, invite_mode:"admin"}
            // could ever arrive — the "Request access" button and waitingForApprovalView were
            // unreachable as a result. Found 2026-08-30 via a real device test: the join
            // request never left the client at all.
            //
            // And not on the first "connected" either: NevdClient reports it right after
            // SENDING cell_register, and a "name taken" NACK ~100 ms later then landed on an
            // already-closed sheet (device log 2026-10-13). hasEverConnected is set once
            // "connected" has held for 1.5 s, and AppStore republishes when it does.
            .onReceive(store.objectWillChange) {
                if submitted && IdentityStore.hasEverConnected && store.connectionStatus == "connected" { dismiss() }
            }
            .alert(Text("Name already taken, choose another"), isPresented: $showNameTakenAlert) {
                Button("OK", role: .cancel) {}
            }
            // Invite link opened from nevod.network/join/ (AppStore.handleOpenURL) — fill in
            // the node and code; the user still types a name and taps "Get started".
            .onAppear { applyPendingInviteLink() }
            .onChange(of: store.pendingInviteLink) { _, _ in applyPendingInviteLink() }
    }

    private func applyPendingInviteLink() {
        guard let token = store.pendingInviteLink else { return }
        store.pendingInviteLink = nil
        nlog("SetupView applying invite link addr=\(token.address)")
        serverAddr = token.address; showServerField = true
        pinnedFingerprint = token.fingerprint; pinnedAddress = token.address
        inviteCode = formatInviteCode(token.code); showInviteField = true
        error = nil
    }

    /// Combined cell-invite tokens ("ADDRESS|FINGERPRINT|CODE") carry the server
    /// address + TLS fingerprint alongside the code — detect and split them out so
    /// scanning (or pasting) one is a one-tap "just connect" action. A bare
    /// "XXXX-XXXX" code falls through to the normal character-stripping format.
    /// pinnedAddress records which address the fingerprint belongs to, so that if
    /// the user later hand-edits the server field, setup() can tell the pin is
    /// stale instead of applying a fingerprint that no longer matches the target.
    private func applyInviteInput(_ raw: String) {
        if let token = parseCellInviteToken(raw) {
            serverAddr = token.address; showServerField = true
            pinnedFingerprint = token.fingerprint; pinnedAddress = token.address
            inviteCode = formatInviteCode(token.code)
            return
        }
        let formatted = formatInviteCode(raw)
        if formatted != raw { inviteCode = formatted }
    }

    private func setup() {
        let name = displayName.trimmingCharacters(in: .whitespaces)
        nlog("SetupView.setup() tapped name=«\(name)» serverAddr=«\(serverAddr)» hasInviteCode=\(!inviteCode.isEmpty)")
        loading = true; error = nil; nameTakenAlerted = false; submitted = true
        let addr = serverAddr.trimmingCharacters(in: .whitespaces)
        if !addr.isEmpty { IdentityStore.nodeAddr = addr }
        IdentityStore.nodeFingerprint = (addr == pinnedAddress) ? pinnedFingerprint : ""
        do {
            try store.createIdentity(displayName: name,
                                     inviteCode: inviteCode.isEmpty ? nil : inviteCode)
            nlog("SetupView.setup() createIdentity call returned without throwing")
        } catch {
            nlog("SetupView.setup() createIdentity THREW err=\(error)")
            self.error = error.localizedDescription; loading = false
        }
    }

    private func handleStatusChange() {
        guard let status = store.client?.status else {
            nlog("SetupView.handleStatusChange no client yet (loading=\(loading))")
            return
        }
        if loading {
            nlog("SetupView.handleStatusChange status=«\(status)» loading=\(loading)")
        }
        if status == "invite required" {
            loading = false; showInviteField = true; error = String(localized: "Invite code required")
        } else if status == "name taken" {
            loading = false; error = String(localized: "Name already taken, choose another")
            if !nameTakenAlerted { nameTakenAlerted = true; showNameTakenAlert = true }
        } else if status == "connected" {
            loading = false
        }
    }
}
