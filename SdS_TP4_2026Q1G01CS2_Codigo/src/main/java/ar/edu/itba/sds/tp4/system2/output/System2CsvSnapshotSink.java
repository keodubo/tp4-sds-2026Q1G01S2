package ar.edu.itba.sds.tp4.system2.output;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.contacts.Contact;
import ar.edu.itba.sds.tp4.system2.contacts.ContactType;
import ar.edu.itba.sds.tp4.system2.engine.System2Snapshot;
import ar.edu.itba.sds.tp4.system2.engine.System2SnapshotSink;
import ar.edu.itba.sds.tp4.system2.forces.ContactForce;
import ar.edu.itba.sds.tp4.system2.forces.ForceSnapshot;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import ar.edu.itba.sds.tp4.system2.state.System2State;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public final class System2CsvSnapshotSink implements System2SnapshotSink, AutoCloseable {
    public static final String METADATA_FILE_NAME = "metadata.json";
    public static final String STATES_FILE_NAME = "states.csv";
    public static final String CONTACTS_FILE_NAME = "contacts.csv";
    public static final String BOUNDARY_FORCES_FILE_NAME = "boundary_forces.csv";

    private final BufferedWriter statesWriter;
    private final BufferedWriter contactsWriter;
    private final BufferedWriter boundaryForcesWriter;
    private final System2OutputConfig outputConfig;
    private boolean closed;

    public System2CsvSnapshotSink(Path outputDirectory, System2OutputMetadata metadata) {
        this(outputDirectory, metadata, new System2OutputConfig(
                metadata.stateStride(),
                metadata.fullContactStride(),
                metadata.boundaryForceStride()
        ));
    }

    public System2CsvSnapshotSink(
            Path outputDirectory,
            System2OutputMetadata metadata,
            System2OutputConfig outputConfig
    ) {
        if (outputDirectory == null) {
            throw new IllegalArgumentException("outputDirectory must not be null.");
        }
        if (metadata == null) {
            throw new IllegalArgumentException("metadata must not be null.");
        }
        if (outputConfig == null) {
            throw new IllegalArgumentException("outputConfig must not be null.");
        }
        this.outputConfig = outputConfig;

        try {
            Files.createDirectories(outputDirectory);
            writeMetadata(outputDirectory.resolve(METADATA_FILE_NAME), metadata);
            statesWriter = Files.newBufferedWriter(outputDirectory.resolve(STATES_FILE_NAME), StandardCharsets.UTF_8);
            contactsWriter = Files.newBufferedWriter(outputDirectory.resolve(CONTACTS_FILE_NAME), StandardCharsets.UTF_8);
            boundaryForcesWriter = Files.newBufferedWriter(
                    outputDirectory.resolve(BOUNDARY_FORCES_FILE_NAME),
                    StandardCharsets.UTF_8
            );
            writeHeaders();
        } catch (IOException exception) {
            throw new UncheckedIOException("Could not initialize System 2 raw output writer.", exception);
        }
    }

    @Override
    public void accept(System2Snapshot snapshot) {
        if (closed) {
            throw new IllegalStateException("Cannot write to a closed snapshot sink.");
        }
        if (snapshot == null) {
            throw new IllegalArgumentException("snapshot must not be null.");
        }

        try {
            if (shouldWriteStateRows(snapshot.state().step())) {
                writeStateRows(snapshot.state());
            }
            writeContactRows(snapshot);
            if (isStrideStep(snapshot.state().step(), outputConfig.boundaryForceStride())) {
                writeBoundaryForceRow(snapshot);
            }
        } catch (IOException exception) {
            throw new UncheckedIOException("Could not write System 2 snapshot.", exception);
        }
    }

    @Override
    public void close() {
        if (closed) {
            return;
        }
        closed = true;
        try {
            IOException failure = null;
            failure = closeCapturing(statesWriter, failure);
            failure = closeCapturing(contactsWriter, failure);
            failure = closeCapturing(boundaryForcesWriter, failure);
            if (failure != null) {
                throw failure;
            }
        } catch (IOException exception) {
            throw new UncheckedIOException("Could not close System 2 raw output writer.", exception);
        }
    }

    private void writeHeaders() throws IOException {
        statesWriter.write("step,t,particle_id,x,y,vx,vy");
        statesWriter.newLine();

        contactsWriter.write("step,t,contact_type,i,j,distance,overlap,nx,ny,fx_i,fy_i,fx_j,fy_j");
        contactsWriter.newLine();

        boundaryForcesWriter.write("step,t,fx_obstacle,fy_obstacle,fx_wall,fy_wall,n_obstacle_contacts,n_wall_contacts");
        boundaryForcesWriter.newLine();
    }

    private void writeStateRows(System2State state) throws IOException {
        for (DynamicParticle particle : state.particles()) {
            statesWriter.write(joinCsv(
                    state.step(),
                    state.time(),
                    particle.id(),
                    particle.position().x(),
                    particle.position().y(),
                    particle.velocity().x(),
                    particle.velocity().y()
            ));
            statesWriter.newLine();
        }
    }

    private void writeContactRows(System2Snapshot snapshot) throws IOException {
        System2State state = snapshot.state();
        boolean fullContactStep = isStrideStep(state.step(), outputConfig.fullContactStride());
        for (ContactForce contactForce : snapshot.forces().snapshot().contactForces()) {
            Contact contact = contactForce.contact();
            if (!fullContactStep && contact.type() != ContactType.PARTICLE_OBSTACLE) {
                continue;
            }
            Vector2 normal = contact.normalFromParticleToOther();
            Vector2 forceOnParticle = contactForce.forceOnParticle();
            Vector2 forceOnOther = contactForce.forceOnOtherBody();

            contactsWriter.write(joinCsv(
                    state.step(),
                    state.time(),
                    contactTypeName(contact.type()),
                    contact.particleId(),
                    contactOtherBodyName(contact),
                    contact.distance(),
                    contact.overlap(),
                    normal.x(),
                    normal.y(),
                    forceOnParticle.x(),
                    forceOnParticle.y(),
                    forceOnOther.x(),
                    forceOnOther.y()
            ));
            contactsWriter.newLine();
        }
    }

    private void writeBoundaryForceRow(System2Snapshot snapshot) throws IOException {
        System2State state = snapshot.state();
        ForceSnapshot forceSnapshot = snapshot.forces().snapshot();
        Vector2 obstacleForce = forceSnapshot.obstacleForce();
        Vector2 wallForce = forceSnapshot.wallForce();

        boundaryForcesWriter.write(joinCsv(
                state.step(),
                state.time(),
                obstacleForce.x(),
                obstacleForce.y(),
                wallForce.x(),
                wallForce.y(),
                countContacts(snapshot, ContactType.PARTICLE_OBSTACLE),
                countContacts(snapshot, ContactType.PARTICLE_WALL)
        ));
        boundaryForcesWriter.newLine();
    }

    private long countContacts(System2Snapshot snapshot, ContactType type) {
        return snapshot.forces().contacts().stream()
                .filter(contact -> contact.type() == type)
                .count();
    }

    private boolean shouldWriteStateRows(long step) {
        return isStrideStep(step, outputConfig.stateStride())
                || isStrideStep(step, outputConfig.fullContactStride());
    }

    private boolean isStrideStep(long step, int stride) {
        return step % stride == 0;
    }

    private String contactOtherBodyName(Contact contact) {
        return switch (contact.type()) {
            case PARTICLE_PARTICLE -> Integer.toString(contact.otherParticleId());
            case PARTICLE_OBSTACLE -> "obstacle";
            case PARTICLE_WALL -> "wall";
        };
    }

    private String contactTypeName(ContactType type) {
        return switch (type) {
            case PARTICLE_PARTICLE -> "particle_particle";
            case PARTICLE_OBSTACLE -> "particle_obstacle";
            case PARTICLE_WALL -> "particle_wall";
        };
    }

    private String joinCsv(Object... values) {
        StringBuilder builder = new StringBuilder();
        for (int index = 0; index < values.length; index++) {
            if (index > 0) {
                builder.append(',');
            }
            builder.append(values[index]);
        }
        return builder.toString();
    }

    private void writeMetadata(Path path, System2OutputMetadata metadata) throws IOException {
        Files.writeString(path, metadata.toJson(), StandardCharsets.UTF_8);
    }

    private IOException closeCapturing(BufferedWriter writer, IOException previousFailure) {
        try {
            writer.close();
            return previousFailure;
        } catch (IOException exception) {
            if (previousFailure != null) {
                previousFailure.addSuppressed(exception);
                return previousFailure;
            }
            return exception;
        }
    }
}
