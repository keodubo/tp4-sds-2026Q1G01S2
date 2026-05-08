package ar.edu.itba.sds.tp4.system1;

import java.util.ArrayList;
import java.util.List;

public final class EulerIntegrator implements Integrator {
    @Override
    public String methodName() {
        return "euler";
    }

    @Override
    public List<OscillatorState> integrate(System1Parameters parameters, double dt) {
        Oscillator oscillator = new Oscillator(parameters);
        int steps = (int) Math.round(parameters.finalTime() / dt);
        List<OscillatorState> states = new ArrayList<>(steps + 1);

        double time = 0.0;
        double position = parameters.initialPosition();
        double velocity = parameters.initialVelocity();
        states.add(new OscillatorState(time, position, velocity));

        for (int step = 0; step < steps; step++) {
            double acceleration = oscillator.acceleration(position, velocity);
            position = position + velocity * dt + 0.5 * acceleration * dt * dt;
            velocity = velocity + acceleration * dt;
            time = (step + 1) * dt;
            states.add(new OscillatorState(time, position, velocity));
        }

        return states;
    }
}
