package ar.edu.itba.sds.tp4.system2.forces;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.contacts.Contact;

public record ContactForce(Contact contact, Vector2 forceOnParticle, Vector2 forceOnOtherBody) {
    public ContactForce {
        if (contact == null) {
            throw new IllegalArgumentException("contact must not be null.");
        }
        if (forceOnParticle == null) {
            throw new IllegalArgumentException("forceOnParticle must not be null.");
        }
        if (forceOnOtherBody == null) {
            throw new IllegalArgumentException("forceOnOtherBody must not be null.");
        }
    }
}
