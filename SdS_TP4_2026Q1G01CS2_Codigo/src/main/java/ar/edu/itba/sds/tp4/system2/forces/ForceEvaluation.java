package ar.edu.itba.sds.tp4.system2.forces;

import ar.edu.itba.sds.tp4.system2.contacts.Contact;

import java.util.List;

public record ForceEvaluation(List<Contact> contacts, ForceSnapshot snapshot) {
    public ForceEvaluation {
        if (contacts == null) {
            throw new IllegalArgumentException("contacts must not be null.");
        }
        if (snapshot == null) {
            throw new IllegalArgumentException("snapshot must not be null.");
        }
        contacts = List.copyOf(contacts);
    }
}
