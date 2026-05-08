package ar.edu.itba.sds.tp4.system1;

import java.util.function.Consumer;

public final class EulerIntegrator implements Integrator {
    @Override
    public String methodName() {
        return "euler";
    }

    @Override
    public void integrate(System1Parameters parameters, double dt, Consumer<OscillatorState> stateConsumer) {
        Oscillator oscillator = new Oscillator(parameters);
        int steps = (int) Math.round(parameters.finalTime() / dt);

        double time = 0.0;
        double position = parameters.initialPosition();
        double velocity = parameters.initialVelocity();
        stateConsumer.accept(new OscillatorState(time, position, velocity));

        for (int step = 0; step < steps; step++) {
            double acceleration = oscillator.acceleration(position, velocity);
            position = position + velocity * dt + 0.5 * acceleration * dt * dt;
            velocity = velocity + acceleration * dt;
            time = (step + 1) * dt;
            stateConsumer.accept(new OscillatorState(time, position, velocity));
        }
    }
}
