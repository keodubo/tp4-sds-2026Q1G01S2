package ar.edu.itba.sds.tp4.system1;

import java.util.List;
import java.util.function.Consumer;

public interface Integrator {
    String methodName();

    void integrate(System1Parameters parameters, double dt, Consumer<OscillatorState> stateConsumer);

    default List<OscillatorState> integrate(System1Parameters parameters, double dt) {
        List<OscillatorState> states = new java.util.ArrayList<>();
        integrate(parameters, dt, states::add);
        return states;
    }
}
