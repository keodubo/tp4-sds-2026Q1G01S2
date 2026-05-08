package ar.edu.itba.sds.tp4.system1;

import java.util.function.Consumer;

public final class BeemanIntegrator implements Integrator {
    @Override
    public String methodName() {
        return "beeman";
    }

    @Override
    public void integrate(System1Parameters parameters, double dt, Consumer<OscillatorState> stateConsumer) {
        Oscillator oscillator = new Oscillator(parameters);
        int steps = (int) Math.round(parameters.finalTime() / dt);

        double position = parameters.initialPosition();
        double velocity = parameters.initialVelocity();
        double acceleration = oscillator.acceleration(position, velocity);
        double previousAcceleration = previousAcceleration(parameters, dt, acceleration);
        stateConsumer.accept(new OscillatorState(0.0, position, velocity));

        for (int step = 0; step < steps; step++) {
            double nextPosition = position
                    + velocity * dt
                    + (2.0 / 3.0) * acceleration * dt * dt
                    - (1.0 / 6.0) * previousAcceleration * dt * dt;
            double predictedVelocity = velocity
                    + (3.0 / 2.0) * acceleration * dt
                    - (1.0 / 2.0) * previousAcceleration * dt;
            double nextAcceleration = oscillator.acceleration(nextPosition, predictedVelocity);
            double correctedVelocity = velocity
                    + (1.0 / 3.0) * nextAcceleration * dt
                    + (5.0 / 6.0) * acceleration * dt
                    - (1.0 / 6.0) * previousAcceleration * dt;

            double nextTime = (step + 1) * dt;
            stateConsumer.accept(new OscillatorState(nextTime, nextPosition, correctedVelocity));

            position = nextPosition;
            velocity = correctedVelocity;
            previousAcceleration = acceleration;
            acceleration = nextAcceleration;
        }
    }

    private static double previousAcceleration(System1Parameters parameters, double dt, double currentAcceleration) {
        double previousPosition = parameters.initialPosition()
                - parameters.initialVelocity() * dt
                + 0.5 * currentAcceleration * dt * dt;
        double previousVelocity = parameters.initialVelocity() - currentAcceleration * dt;
        return new Oscillator(parameters).acceleration(previousPosition, previousVelocity);
    }
}
