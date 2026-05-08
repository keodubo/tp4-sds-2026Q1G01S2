package ar.edu.itba.sds.tp4.system1;

import java.util.ArrayList;
import java.util.List;

public final class VerletIntegrator implements Integrator {
    @Override
    public String methodName() {
        return "verlet";
    }

    @Override
    public List<OscillatorState> integrate(System1Parameters parameters, double dt) {
        int steps = (int) Math.round(parameters.finalTime() / dt);
        double[] positions = new double[steps + 3];

        positions[0] = previousPosition(parameters, dt);
        positions[1] = parameters.initialPosition();
        for (int step = 0; step <= steps; step++) {
            positions[step + 2] = nextPosition(parameters, dt, positions[step], positions[step + 1]);
        }

        List<OscillatorState> states = new ArrayList<>(steps + 1);
        for (int step = 0; step <= steps; step++) {
            double time = step * dt;
            double position = positions[step + 1];
            double velocity = (positions[step + 2] - positions[step]) / (2.0 * dt);
            states.add(new OscillatorState(time, position, velocity));
        }
        return states;
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
