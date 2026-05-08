package ar.edu.itba.sds.tp4.system2.integrators;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.forces.ForceEvaluation;
import ar.edu.itba.sds.tp4.system2.forces.ForceEvaluator;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import ar.edu.itba.sds.tp4.system2.state.System2State;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public final class VelocityVerletIntegrator {
    public IntegrationResult step(System2State state, double dt, ForceEvaluator forceEvaluator) {
        if (state == null) {
            throw new IllegalArgumentException("state must not be null.");
        }
        if (dt <= 0.0) {
            throw new IllegalArgumentException("dt must be positive.");
        }
        if (forceEvaluator == null) {
            throw new IllegalArgumentException("forceEvaluator must not be null.");
        }

        ForceEvaluation initialForces = forceEvaluator.evaluate(state);
        return step(state, dt, forceEvaluator, initialForces);
    }

    public IntegrationResult step(
            System2State state,
            double dt,
            ForceEvaluator forceEvaluator,
            ForceEvaluation initialForces
    ) {
        if (state == null) {
            throw new IllegalArgumentException("state must not be null.");
        }
        if (dt <= 0.0) {
            throw new IllegalArgumentException("dt must be positive.");
        }
        if (forceEvaluator == null) {
            throw new IllegalArgumentException("forceEvaluator must not be null.");
        }
        if (initialForces == null) {
            throw new IllegalArgumentException("initialForces must not be null.");
        }

        List<DynamicParticle> predictedParticles = predictPositions(
                state.particles(),
                initialForces.snapshot().particleForces(),
                dt
        );
        System2State predictedState = new System2State(state.step() + 1, state.time() + dt, predictedParticles);

        ForceEvaluation nextForces = forceEvaluator.evaluate(predictedState);
        List<DynamicParticle> nextParticles = correctVelocities(
                state.particles(),
                predictedState.particles(),
                initialForces.snapshot().particleForces(),
                nextForces.snapshot().particleForces(),
                dt
        );
        System2State nextState = new System2State(predictedState.step(), predictedState.time(), nextParticles);

        return new IntegrationResult(state, initialForces, nextState, nextForces);
    }

    private List<DynamicParticle> predictPositions(
            List<DynamicParticle> particles,
            Map<Integer, Vector2> forces,
            double dt
    ) {
        List<DynamicParticle> predicted = new ArrayList<>(particles.size());
        double halfDtSquared = 0.5 * dt * dt;

        for (DynamicParticle particle : particles) {
            Vector2 acceleration = accelerationFor(particle, forces);
            Vector2 nextPosition = particle.position()
                    .add(particle.velocity().multiply(dt))
                    .add(acceleration.multiply(halfDtSquared));
            predicted.add(new DynamicParticle(
                    particle.id(),
                    nextPosition,
                    particle.velocity(),
                    particle.radius(),
                    particle.mass()
            ));
        }
        return List.copyOf(predicted);
    }

    private List<DynamicParticle> correctVelocities(
            List<DynamicParticle> previousParticles,
            List<DynamicParticle> predictedParticles,
            Map<Integer, Vector2> initialForces,
            Map<Integer, Vector2> nextForces,
            double dt
    ) {
        List<DynamicParticle> corrected = new ArrayList<>(predictedParticles.size());
        for (int index = 0; index < predictedParticles.size(); index++) {
            DynamicParticle previousParticle = previousParticles.get(index);
            DynamicParticle predictedParticle = predictedParticles.get(index);
            if (previousParticle.id() != predictedParticle.id()) {
                throw new IllegalArgumentException("Particle order changed during integration.");
            }

            Vector2 initialAcceleration = accelerationFor(previousParticle, initialForces);
            Vector2 nextAcceleration = accelerationFor(predictedParticle, nextForces);
            Vector2 nextVelocity = previousParticle.velocity()
                    .add(initialAcceleration.add(nextAcceleration).multiply(0.5 * dt));
            corrected.add(new DynamicParticle(
                    predictedParticle.id(),
                    predictedParticle.position(),
                    nextVelocity,
                    predictedParticle.radius(),
                    predictedParticle.mass()
            ));
        }
        return List.copyOf(corrected);
    }

    private Vector2 accelerationFor(DynamicParticle particle, Map<Integer, Vector2> forces) {
        Vector2 force = forces.get(particle.id());
        if (force == null) {
            throw new IllegalArgumentException("Missing force for particle id " + particle.id() + ".");
        }
        return force.multiply(1.0 / particle.mass());
    }
}
