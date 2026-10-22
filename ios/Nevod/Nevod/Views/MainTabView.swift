import SwiftUI

// MARK: - Shared tab identity (iPhone TabView selection + iPad sidebar selection both bind to
// the same store.selectedTab — needed so a notification-tap deep link can force the Chats tab
// into view regardless of which layout is active, see AppStore.pendingChatCellId).

enum MainTab: String, CaseIterable, Identifiable {
    case chats    = "Chats"
    case calls    = "Calls"
    case contacts = "Contacts"
    case nodes    = "Nodes"
    case profile  = "Profile"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .chats:    "bubble.left.and.bubble.right"
        case .calls:    "phone"
        case .contacts: "person.2"
        case .nodes:    "network"
        case .profile:  "person.circle"
        }
    }

    // rawValue is used as-is for tag/id identity — it must stay a stable, non-localized
    // English constant. This is the actual display text, kept a separate switch (not just
    // String(localized:) over rawValue) so the catalog key isn't coupled to that identity.
    var title: String {
        switch self {
        case .chats:    String(localized: "Chats")
        case .calls:    String(localized: "Calls")
        case .contacts: String(localized: "Contacts")
        case .nodes:    String(localized: "Nodes")
        case .profile:  String(localized: "Profile")
        }
    }
}

// MARK: - iPhone layout

struct MainTabView: View {
    #if os(iOS)
    @Environment(\.horizontalSizeClass) private var sizeClass
    #endif

    var body: some View {
        #if os(macOS)
        SidebarLayout()
        #else
        if sizeClass == .regular {
            SidebarLayout()
        } else {
            TabLayout()
        }
        #endif
    }
}

private struct TabLayout: View {
    @EnvironmentObject var store: AppStore

    var body: some View {
        TabView(selection: $store.selectedTab) {
            ChatsListView()
                .tabItem { Label("Chats", systemImage: "bubble.left.and.bubble.right") }
                .tag(MainTab.chats as MainTab?)
            CallsView()
                .tabItem { Label("Calls", systemImage: "phone") }
                .tag(MainTab.calls as MainTab?)
            ContactsView()
                .tabItem { Label("Contacts", systemImage: "person.2") }
                .tag(MainTab.contacts as MainTab?)
            NodesView()
                .tabItem { Label("Nodes", systemImage: "network") }
                .tag(MainTab.nodes as MainTab?)
            ProfileView()
                .tabItem { Label("Profile", systemImage: "person.circle") }
                .tag(MainTab.profile as MainTab?)
        }
    }
}

// MARK: - iPad layout

private struct SidebarLayout: View {
    @EnvironmentObject var store: AppStore
    @State private var columnVisibility: NavigationSplitViewVisibility = .all

    var body: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) {
            List(selection: $store.selectedTab) {
                ForEach(MainTab.allCases) { section in
                    Label(section.title, systemImage: section.icon)
                        .tag(section)
                }
            }
            .listStyle(.sidebar)
            .navigationTitle("Nevod")
            .safeAreaInset(edge: .bottom) {
                HStack(spacing: 6) {
                    Circle()
                        .fill(store.client?.isConnected == true ? Color.green : Color.red)
                        .frame(width: 8, height: 8)
                    Text(store.connectionStatus)
                        .font(.caption).foregroundStyle(.secondary)
                    Spacer()
                }
                .padding(.horizontal).padding(.vertical, 8)
            }
        } detail: {
            switch store.selectedTab ?? .chats {
            case .chats:    ChatsListView()
            case .calls:    CallsView()
            case .contacts: ContactsView()
            case .nodes:    NodesView()
            case .profile:  ProfileView()
            }
        }
        .navigationSplitViewStyle(.balanced)
    }
}
