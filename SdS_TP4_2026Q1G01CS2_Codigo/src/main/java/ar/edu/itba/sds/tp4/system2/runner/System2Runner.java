package ar.edu.itba.sds.tp4.system2.runner;

import ar.edu.itba.sds.tp4.system2.engine.System2Engine;
import ar.edu.itba.sds.tp4.system2.engine.System2RunResult;
import ar.edu.itba.sds.tp4.system2.forces.System2ForceEvaluator;
import ar.edu.itba.sds.tp4.system2.initialization.System2InitialStateGenerator;
import ar.edu.itba.sds.tp4.system2.integrators.VelocityVerletIntegrator;
import ar.edu.itba.sds.tp4.system2.output.System2CsvSnapshotSink;
import ar.edu.itba.sds.tp4.system2.output.System2OutputConfig;
import ar.edu.itba.sds.tp4.system2.output.System2OutputMetadata;
import ar.edu.itba.sds.tp4.system2.state.System2State;

public final class System2Runner {
    public static final String INTEGRATOR_NAME = "velocity_verlet";

    private final System2InitialStateGenerator initialStateGenerator;

    public System2Runner() {
        this(new System2InitialStateGenerator());
    }

    public System2Runner(System2InitialStateGenerator initialStateGenerator) {
        if (initialStateGenerator == null) {
            throw new IllegalArgumentException("initialStateGenerator must not be null.");
        }
        this.initialStateGenerator = initialStateGenerator;
    }

    public System2RunnerResult run(System2RunRequest request) {
        if (request == null) {
            throw new IllegalArgumentException("request must not be null.");
        }

        System2State initialState = initialStateGenerator.generate(request.config());
        System2ForceEvaluator forceEvaluator = new System2ForceEvaluator(
                request.config().geometry(),
                request.config().stiffness()
        );
        System2Engine engine = new System2Engine(forceEvaluator, new VelocityVerletIntegrator());
        System2OutputMetadata metadata = new System2OutputMetadata(
                request.runId(),
                request.realization(),
                request.config(),
                INTEGRATOR_NAME,
                request.outputConfig().stateStride(),
                request.outputConfig().fullContactStride(),
                System2OutputConfig.OBSTACLE_CONTACT_STRIDE,
                request.outputConfig().boundaryForceStride()
        );

        try (System2CsvSnapshotSink sink = new System2CsvSnapshotSink(
                request.outputDirectory(),
                metadata,
                request.outputConfig()
        )) {
            System2RunResult runResult = engine.run(
                    initialState,
                    request.config().dt(),
                    request.config().steps(),
                    sink
            );
            return new System2RunnerResult(request.outputDirectory(), runResult);
        }
    }
}
