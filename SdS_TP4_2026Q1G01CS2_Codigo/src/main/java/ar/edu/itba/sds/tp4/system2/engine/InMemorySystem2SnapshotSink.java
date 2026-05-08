package ar.edu.itba.sds.tp4.system2.engine;

import java.util.ArrayList;
import java.util.List;

public final class InMemorySystem2SnapshotSink implements System2SnapshotSink {
    private final List<System2Snapshot> snapshots = new ArrayList<>();

    @Override
    public void accept(System2Snapshot snapshot) {
        if (snapshot == null) {
            throw new IllegalArgumentException("snapshot must not be null.");
        }
        snapshots.add(snapshot);
    }

    public List<System2Snapshot> snapshots() {
        return List.copyOf(snapshots);
    }
}
