import SwiftUI
import UserNotifications
#if os(iOS)
import PushKit
#endif

#if os(iOS)
// @MainActor + callManager created here (not in NevdApp via @StateObject/onAppear) so it
// exists before iOS can possibly deliver a VoIP push — a background launch triggered by a
// killed app receiving a call doesn't reliably run SwiftUI's onAppear in time, which left
// callManager nil exactly when didReceiveIncomingPushWith needed it (confirmed via device
// logs: VoIP push was sent and accepted by APNs, but reportNewIncomingCall never fired).
//
// store is created and wired to callManager here too, for the exact same reason — confirmed
// live 2026-07-30: on a cold VoIP-push launch, callManager.store was still nil (only ever set
// in NevdApp's .onAppear, which SwiftUI doesn't reliably run in time either), so
// resolvedCallerName's local contact lookup silently found nothing and fell back to the
// caller's self-declared name — worked fine once the app was already in memory (.onAppear had
// already run by then), which is exactly the "AVK when foregrounded, Andrey when killed"
// split observed on device.
@MainActor
class AppDelegate: NSObject, UIApplicationDelegate {
    let callManager = CallManager()
    let store = AppStore()
    private let voipRegistry = PKPushRegistry(queue: .main)

    override init() {
        super.init()
        callManager.store = store
        store.callSignalHandler = { [weak self] cellId, signal in
            self?.callManager.handleSignal(from: cellId, signal: signal)
        }
        store.onTurnCredentials = { [weak self] info in
            self?.callManager.turnInfo = info
        }
    }

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        voipRegistry.delegate = self
        voipRegistry.desiredPushTypes = [.voIP]
        UNUserNotificationCenter.current().delegate = self
        return true
    }

    func application(_ application: UIApplication,
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02x", $0) }.joined()
        NotificationCenter.default.post(name: .apnsToken, object: token)
    }
    func application(_ application: UIApplication,
                     didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("APNs registration failed: \(error.localizedDescription)")
    }
}

// Tapping a message push notification used to just open the app to whatever screen was
// last shown — there was no client-side handling of the tap at all (confirmed nothing like
// this existed anywhere in the codebase before). sender_cell_id now rides along in the
// APNs payload outside "aps" (see node/push.py) specifically so this delegate can read it
// straight from userInfo and deep-link into the right chat.
extension AppDelegate: UNUserNotificationCenterDelegate {
    // Deliberately does NOT implement willPresent — leaving foreground-presentation
    // behavior exactly as it was before this delegate existed (iOS's own default with no
    // delegate set is to not show a banner while the app is already active).
    nonisolated func userNotificationCenter(_ center: UNUserNotificationCenter,
                                            didReceive response: UNNotificationResponse,
                                            withCompletionHandler completionHandler: @escaping () -> Void) {
        let userInfo = response.notification.request.content.userInfo
        let cellId = userInfo["sender_cell_id"] as? String
        nlog("push tap userInfo=\(userInfo) resolvedCellId=\(cellId ?? "nil")")
        Task { @MainActor in
            if let cellId, !cellId.isEmpty {
                self.store.selectedTab = .chats
                self.store.pendingChatCellId = cellId
                nlog("push tap set pendingChatCellId=\(cellId.prefix(8)) selectedTab=.chats")
            } else {
                nlog("push tap IGNORED — no usable sender_cell_id in payload")
            }
            completionHandler()
        }
    }
}

extension AppDelegate: PKPushRegistryDelegate {
    func pushRegistry(_ registry: PKPushRegistry, didUpdate pushCredentials: PKPushCredentials,
                       for type: PKPushType) {
        guard type == .voIP else { return }
        let token = pushCredentials.token.map { String(format: "%02x", $0) }.joined()
        nlog("voip pushRegistry didUpdate token=\(String(token.prefix(8)))")
        NotificationCenter.default.post(name: .voipToken, object: token)
    }

    func pushRegistry(_ registry: PKPushRegistry, didInvalidatePushTokenFor type: PKPushType) {}

    // Apple's contract: every VoIP push MUST result in reportNewIncomingCall before this
    // returns, or iOS can revoke VoIP push privileges for the app. The real offer (SDP) is
    // still E2E encrypted and hasn't arrived — only what the node put directly in the push
    // payload (caller_id/caller_name) is available here. PKPushRegistry(queue: .main) means
    // this already runs on the main thread, so no Task/MainActor hop needed — call directly,
    // as promptly as possible.
    func pushRegistry(_ registry: PKPushRegistry, didReceiveIncomingPushWith payload: PKPushPayload,
                       for type: PKPushType, completion: @escaping () -> Void) {
        guard type == .voIP else { completion(); return }
        let callerId = payload.dictionaryPayload["caller_id"] as? String ?? ""
        let callerName = payload.dictionaryPayload["caller_name"] as? String ?? ""
        nlog("voip push received callerId=\(String(callerId.prefix(8))) callerName=\(callerName)")
        callManager.reportIncomingCallFromPush(callerId: callerId, callerName: callerName)
        completion()
    }
}
#elseif os(macOS)
@MainActor
class AppDelegate: NSObject, NSApplicationDelegate {
    let callManager = CallManager()
    let store = AppStore()

    override init() {
        super.init()
        callManager.store = store
        store.callSignalHandler = { [weak self] cellId, signal in
            self?.callManager.handleSignal(from: cellId, signal: signal)
        }
        store.onTurnCredentials = { [weak self] info in
            self?.callManager.turnInfo = info
        }
    }

    func application(_ application: NSApplication,
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02x", $0) }.joined()
        NotificationCenter.default.post(name: .apnsToken, object: token)
    }
    func application(_ application: NSApplication,
                     didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("APNs registration failed: \(error.localizedDescription)")
    }
}
#endif

extension Notification.Name {
    static let apnsToken = Notification.Name("nevod.apnsToken")
    static let voipToken = Notification.Name("nevod.voipToken")
}

@main
struct NevdApp: App {
    #if os(iOS)
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    #elseif os(macOS)
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    #endif
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appDelegate.store)
                .environmentObject(appDelegate.callManager)
                // Invite links: nevod.network/join/ hands the token over as nevod://join?t=…
                .onOpenURL { url in appDelegate.store.handleOpenURL(url) }
                .onReceive(NotificationCenter.default.publisher(for: .apnsToken)) { n in
                    if let token = n.object as? String {
                        appDelegate.store.onDeviceToken(token)
                    }
                }
                .onReceive(NotificationCenter.default.publisher(for: .voipToken)) { n in
                    if let token = n.object as? String {
                        appDelegate.store.onVoipToken(token)
                    }
                }
                // App switcher: iOS snapshots whatever is on screen when the app leaves the
                // foreground, so chats would otherwise sit in the switcher (and in the system's
                // snapshot files) in readable form.
                #if os(iOS)
                .overlay {
                    if scenePhase != .active { PrivacyCover() }
                }
                #endif
        }
        .onChange(of: scenePhase) { _, phase in
            nlog("scenePhase -> \(phase)")
            #if os(iOS)
            if phase == .background { appDelegate.store.appDidEnterBackground() }
            if phase == .active { appDelegate.store.appDidBecomeActive() }
            #endif
            if phase == .active {
                UNUserNotificationCenter.current().setBadgeCount(0) { err in
                    nlog("badge clear err=\(err?.localizedDescription ?? "ok")")
                }
                UNUserNotificationCenter.current().removeAllDeliveredNotifications()
                // invite_mode="admin" registration channel — the approval push has no
                // sender_cell_id (see didReceive below), so it can't deep-link; this is what
                // actually notices "approved" and completes registration. Cheap no-op unless
                // a request is genuinely outstanding, see AppStore.retryPendingJoinRequestIfNeeded.
                appDelegate.store.retryPendingJoinRequestIfNeeded()
            }
        }
    }
}

/// Shown instead of the app's content while it isn't active — see the .overlay in NevdApp.
private struct PrivacyCover: View {
    var body: some View {
        ZStack {
            Rectangle().fill(.background)
            Text(verbatim: "Nevod")
                .font(.largeTitle.weight(.semibold))
                .foregroundStyle(.secondary)
        }
        .ignoresSafeArea()
    }
}
