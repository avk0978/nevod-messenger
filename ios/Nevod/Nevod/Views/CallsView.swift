import SwiftUI

struct CallsView: View {
    @EnvironmentObject var store: AppStore
    @EnvironmentObject var callManager: CallManager

    var body: some View {
        NavigationStack {
            List {
                ForEach(store.callLog, id: \.id) { entry in
                    CallLogRow(entry: entry, name: store.displayName(for: entry.cellId),
                               isIdentityDeleted: store.isIdentityDeleted(cellId: entry.cellId),
                               onCallBack: {
                        callManager.startCall(to: entry.cellId,
                                              contactName: store.displayName(for: entry.cellId))
                    })
                }
                .onDelete { indexSet in
                    for i in indexSet { store.deleteCallLogEntry(store.callLog[i]) }
                }
            }
            .listStyle(.plain)
            .navigationTitle("Звонки")
            .overlay {
                if store.callLog.isEmpty {
                    ContentUnavailableView("Нет звонков", systemImage: "phone",
                        description: Text("Звонки, которые вы совершите или примете, появятся здесь"))
                }
            }
        }
    }
}

private struct CallLogRow: View {
    let entry: CallLogEntry
    let name: String
    let isIdentityDeleted: Bool
    let onCallBack: () -> Void

    var body: some View {
        HStack {
            Image(systemName: entry.isOutgoing ? "arrow.up.right" : "arrow.down.left")
                .font(.title3)
                .foregroundStyle(isMissed ? .red : .secondary)
                .frame(width: 24)
            if entry.isVideo {
                Image(systemName: "video.fill").font(.caption).foregroundStyle(.secondary)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(name).font(.headline).foregroundStyle(isMissed ? .red : .primary)
                Text(subtitle).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Text(timeString).font(.caption).foregroundStyle(.secondary)
            Button(action: onCallBack) {
                Image(systemName: "phone.fill").font(.title3).foregroundStyle(.tint)
            }
            .buttonStyle(.plain)
            .disabled(isIdentityDeleted)
            .padding(.leading, 10)
        }
        .padding(.vertical, 2)
    }

    private var isMissed: Bool { entry.outcome == .missed && !entry.isOutgoing }

    private var subtitle: String {
        switch (entry.isOutgoing, entry.outcome) {
        case (true, .answered):  return String(localized: "Исходящий · \(durationString)")
        case (true, .missed):    return String(localized: "Исходящий · Не ответили")
        case (false, .answered): return String(localized: "Входящий · \(durationString)")
        case (false, .missed):   return String(localized: "Пропущенный")
        }
    }

    private var durationString: String {
        let s = entry.durationSecs
        return String(format: "%d:%02d", s / 60, s % 60)
    }

    private var timeString: String {
        let cal = Calendar.current
        if cal.isDateInToday(entry.timestamp) {
            return entry.timestamp.formatted(date: .omitted, time: .shortened)
        }
        if cal.isDateInYesterday(entry.timestamp) {
            return String(localized: "Вчера")
        }
        return entry.timestamp.formatted(date: .numeric, time: .omitted)
    }
}
