import SwiftUI

struct RootView: View {
    @EnvironmentObject var store: AppStore
    @EnvironmentObject var callManager: CallManager
    @AppStorage("nevod.termsAcceptedVersion") private var termsAcceptedVersion = 0
    // Set by AppStore.openMessageStore when the history store couldn't be opened and was
    // moved aside; dismissing the alert clears it, so it's shown once.
    @AppStorage(AppStore.storeRecoveryKey) private var storeRecoveryNotice = false

    var body: some View {
        ZStack {
            if termsAcceptedVersion < NevodLinks.termsVersion {
                // App Store Guideline 1.2: terms (zero tolerance for objectionable content)
                // accepted before any user-generated content is reachable — including the
                // registration-free browse segment below.
                TermsAcceptanceView()
            } else if store.identity == nil {
                // Rare fallback only (e.g. keychain save failed at cold start) — normally
                // AppStore.init() already generated a browsing-only identity, so this branch
                // isn't the everyday "new user" path anymore, NodesView below is.
                SetupView()
            } else if !store.isRegistered || !IdentityStore.hasEverConnected {
                // Open discovery segment: planets, verified nodes, published pages/bots — no
                // display name or home node required yet. NodesView itself offers the path into
                // full registration (toolbar button, or tapping a bot cell).
                //
                // The second half of this condition exists because isRegistered flips true
                // SYNCHRONOUSLY at createIdentity() — long before the server round trip that
                // decides whether this node needs admin approval. Gating on isRegistered alone
                // swapped straight to MainTabView the instant "Get started" was tapped, tearing
                // down NodesView (and SetupView's sheet on top of it) before an invite_required
                // NACK could ever render — confirmed on device 2026-09-13, "Request access" was
                // unreachable via the normal join flow, not just the later revisit. Once this
                // identity has EVER actually connected (IdentityStore.hasEverConnected, set in
                // AppStore's status sink and reset in resetIdentity()), later transient
                // disconnects/reconnects no longer bounce an established user back here — only
                // a still-unresolved FIRST registration attempt does.
                //
                // No exception for an optimistic "connected" either: NevdClient reports it
                // right after SENDING cell_register, and letting it through here swapped to
                // MainTabView for ~150 ms — long enough to tear down SetupView's sheet — before
                // a "name taken" NACK flipped it back to bare NodesView with no error shown
                // (device log 2026-10-13, iPad stuck on the planet list). hasEverConnected is
                // only set once "connected" has held for 1.5 s (AppStore's status sink), which
                // also republishes the store so this view moves on then.
                //
                // A genuinely pending (already-acked) or just-denied join request needs its
                // OWN branch here, ahead of plain NodesView: the waiting/denied screens only
                // exist nested inside SetupView, which is only ever reachable by manually
                // tapping "Join this node" again — nothing re-presents that sheet on its own.
                // A cold app launch (relaunch, not just foreground) while a request is
                // outstanding landed silently on plain browsing with zero indication anything
                // was pending, even though joinRequestPending itself was correctly persisted
                // and tracked the whole time. Confirmed on device 2026-09-19: a tester's app was
                // relaunched ~48s after their join request was acked (already approved by the
                // time they reopened it, per node1's own logs) and they never saw any waiting
                // screen at all — just landed back on the planet list.
                if store.joinRequestPending || store.joinRequestDenied {
                    SetupView()
                } else {
                    NodesView()
                }
            } else {
                MainTabView()
                    .overlay(alignment: .top) {
                        if let card = store.pendingCard, shouldShowBanner(card) {
                            AddContactBanner(card: card, suggestedName: store.pendingCardName ?? "")
                        }
                    }
            }

            if !callManager.state.isIdle {
                CallOverlay()
            }
        }
        // Which screen RootView chose, and why — device test 2026-10-16 showed MainTabView's
        // sidebar for an identity a closed node had only NACKed, and the log couldn't say how.
        .task(id: screenTrace) { nlog("RootView screen \(screenTrace)") }
        .alert(Text("Invitation to another node"), isPresented: Binding(
            get: { store.inviteLinkForOtherNode != nil },
            set: { if !$0 { store.inviteLinkForOtherNode = nil } })) {
            Button("OK", role: .cancel) {}
        } message: {
            Text("This invitation is for signing up on \(store.inviteLinkForOtherNode ?? "") as a new user. You are already registered on a node. To switch, reset your identity in Profile (this deletes your chats on this device), then open the link again.")
        }
        .alert(Text("Message history"), isPresented: $storeRecoveryNotice) {
            Button("OK", role: .cancel) {}
        } message: {
            Text("Your message history couldn't be opened after the update. It hasn't been deleted: it's kept on this device, and a later update will bring it back. New messages are saved as usual.")
        }
    }

    private var screenTrace: String {
        let screen: String
        if termsAcceptedVersion < NevodLinks.termsVersion { screen = "terms" }
        else if store.identity == nil { screen = "setup(no identity)" }
        else if !store.isRegistered || !IdentityStore.hasEverConnected {
            screen = (store.joinRequestPending || store.joinRequestDenied) ? "setup(join request)" : "nodes"
        } else { screen = "main" }
        return "\(screen) registered=\(store.isRegistered) everConnected=\(IdentityStore.hasEverConnected)"
    }

    private func shouldShowBanner(_ card: String) -> Bool {
        guard let contact = parseCard(card) else { return false }
        if store.contacts.contains(where: { $0.cellId == contact.cellId }) { return false }
        if store.nodeMembers.contains(where: { $0.cellId == contact.cellId }) { return false }
        return true
    }
}
