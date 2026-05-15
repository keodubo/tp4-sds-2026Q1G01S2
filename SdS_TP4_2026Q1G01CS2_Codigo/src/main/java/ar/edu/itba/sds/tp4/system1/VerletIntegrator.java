package ar.edu.itba.sds.tp4.system1;

import java.util.function.Consumer;

public final class VerletIntegrator implements Integrator {
    @Override
    public String methodName() {
        return "verlet";
    }

    @Override
    public void integrate(System1Parameters parameters, double dt, Consumer<OscillatorState> stateConsumer) {
        int steps = (int) Math.round(parameters.finalTime() / dt);

        double previousPosition = previousPosition(parameters, dt);
        double position = parameters.initialPosition();
        double velocity = parameters.initialVelocity();
        for (int step = 0; step <= steps; step++) {
            double time = step * dt;
            stateConsumer.accept(new OscillatorState(time, position, velocity));
            if (step == steps) {
                break;
            }

            double nextPosition = nextPosition(parameters, dt, previousPosition, position, velocity);
            double nextVelocity = (nextPosition - position) / dt;
            previousPosition = position;
            position = nextPosition;
            velocity = nextVelocity;
        }
    }

    private static double previousPosition(System1Parameters parameters, double dt) {
        Oscillator oscillator = new Oscillator(parameters);
        double acceleration = oscillator.acceleration(parameters.initialPosition(), parameters.initialVelocity());
        return parameters.initialPosition()
                - parameters.initialVelocity() * dt
                + 0.5 * acceleration * dt * dt;
    }

    private static double nextPosition(
            System1Parameters parameters,
            double dt,
            double previousPosition,
            double position,
            double velocity
    ) {
        Oscillator oscillator = new Oscillator(parameters);
        double acceleration = oscillator.acceleration(position, velocity);
        return 2.0 * position - previousPosition + acceleration * dt * dt;
    }
}
