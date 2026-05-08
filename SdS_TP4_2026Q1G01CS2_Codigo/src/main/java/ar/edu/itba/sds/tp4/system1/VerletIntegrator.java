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
        for (int step = 0; step <= steps; step++) {
            double nextPosition = nextPosition(parameters, dt, previousPosition, position);
            double time = step * dt;
            double velocity = (nextPosition - previousPosition) / (2.0 * dt);
            stateConsumer.accept(new OscillatorState(time, position, velocity));
            previousPosition = position;
            position = nextPosition;
        }
    }

    private static double previousPosition(System1Parameters parameters, double dt) {
        Oscillator oscillator = new Oscillator(parameters);
        double acceleration = oscillator.acceleration(parameters.initialPosition(), parameters.initialVelocity());
        return parameters.initialPosition()
                - parameters.initialVelocity() * dt
                + 0.5 * acceleration * dt * dt;
    }

    private static double nextPosition(System1Parameters parameters, double dt, double previousPosition, double position) {
        double mass = parameters.mass();
        double gamma = parameters.gamma();
        double numerator = (2.0 * mass - parameters.springConstant() * dt * dt) * position
                + (gamma * dt / 2.0 - mass) * previousPosition;
        double denominator = mass + gamma * dt / 2.0;
        return numerator / denominator;
    }
}
