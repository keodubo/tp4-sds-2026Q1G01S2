package ar.edu.itba.sds.tp4.system2.engine;

import ar.edu.itba.sds.tp4.system2.forces.ForceEvaluation;
import ar.edu.itba.sds.tp4.system2.forces.ForceEvaluator;
import ar.edu.itba.sds.tp4.system2.integrators.IntegrationResult;
import ar.edu.itba.sds.tp4.system2.integrators.VelocityVerletIntegrator;
import ar.edu.itba.sds.tp4.system2.state.System2State;

public final class System2Engine {
    private final ForceEvaluator forceEvaluator;
    private final VelocityVerletIntegrator integrator;

    public System2Engine(ForceEvaluator forceEvaluator) {
        this(forceEvaluator, new VelocityVerletIntegrator());
    }

    public System2Engine(ForceEvaluator forceEvaluator, VelocityVerletIntegrator integrator) {
        if (forceEvaluator == null) {
            throw new IllegalArgumentException("forceEvaluator must not be null.");
        }
        if (integrator == null) {
            throw new IllegalArgumentException("integrator must not be null.");
        }
        this.forceEvaluator = forceEvaluator;
        this.integrator = integrator;
    }

    public System2RunResult run(
            System2State initialState,
            double dt,
            long steps,
            System2SnapshotSink snapshotSink
    ) {
        if (initialState == null) {
            throw new IllegalArgumentException("initialState must not be null.");
        }
        if (dt <= 0.0) {
            throw new IllegalArgumentException("dt must be positive.");
        }
        if (steps < 0) {
            throw new IllegalArgumentException("steps must be non-negative.");
        }
        if (snapshotSink == null) {
            throw new IllegalArgumentException("snapshotSink must not be null.");
        }

        System2State currentState = initialState;
        ForceEvaluation currentForces = forceEvaluator.evaluate(currentState);
        long snapshotsWritten = 0;

        snapshotSink.accept(new System2Snapshot(currentState, currentForces));
        snapshotsWritten++;

        for (long stepIndex = 0; stepIndex < steps; stepIndex++) {
            IntegrationResult integrationResult = integrator.step(currentState, dt, forceEvaluator, currentForces);
            currentState = integrationResult.nextState();
            currentForces = integrationResult.nextForces();

            snapshotSink.accept(new System2Snapshot(currentState, currentForces));
            snapshotsWritten++;
        }

        return new System2RunResult(currentState, steps, snapshotsWritten);
    }
}
