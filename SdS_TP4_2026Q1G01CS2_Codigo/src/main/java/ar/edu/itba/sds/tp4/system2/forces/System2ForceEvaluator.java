package ar.edu.itba.sds.tp4.system2.forces;

import ar.edu.itba.sds.tp4.system2.contacts.Contact;
import ar.edu.itba.sds.tp4.system2.contacts.ContactDetector;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.System2State;

import java.util.List;

public final class System2ForceEvaluator implements ForceEvaluator {
    private final System2Geometry geometry;
    private final ContactDetector contactDetector;
    private final ElasticForceCalculator forceCalculator;

    public System2ForceEvaluator(System2Geometry geometry, double stiffness) {
        this(geometry, new ContactDetector(), new ElasticForceCalculator(stiffness));
    }

    public System2ForceEvaluator(
            System2Geometry geometry,
            ContactDetector contactDetector,
            ElasticForceCalculator forceCalculator
    ) {
        if (geometry == null) {
            throw new IllegalArgumentException("geometry must not be null.");
        }
        if (contactDetector == null) {
            throw new IllegalArgumentException("contactDetector must not be null.");
        }
        if (forceCalculator == null) {
            throw new IllegalArgumentException("forceCalculator must not be null.");
        }
        this.geometry = geometry;
        this.contactDetector = contactDetector;
        this.forceCalculator = forceCalculator;
    }

    @Override
    public ForceEvaluation evaluate(System2State state) {
        if (state == null) {
            throw new IllegalArgumentException("state must not be null.");
        }
        List<Contact> contacts = contactDetector.detect(state, geometry);
        ForceSnapshot snapshot = forceCalculator.evaluate(state.particles(), contacts);
        return new ForceEvaluation(contacts, snapshot);
    }
}
