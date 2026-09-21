package com.limelight.secondary;

import android.view.Display;

import java.util.Arrays;
import java.util.Comparator;

/** Central policy and state machine for the optional streamed display. */
public final class SecondaryDisplayPolicy {
    public enum Mode { DISABLED, AUTOMATIC, FORCED }

    private Mode mode;
    private int selectedDisplayId = Display.INVALID_DISPLAY;
    private boolean primaryOnly = true;
    private boolean reconnect;

    public SecondaryDisplayPolicy(Mode mode) {
        this.mode = mode;
    }

    /** Selects deterministically by displayId, never returning the primary display. */
    public synchronized Display select(Display primary, Display[] displays) {
        if (mode == Mode.DISABLED || displays == null) {
            return null;
        }
        int primaryId = primary == null ? Display.DEFAULT_DISPLAY : primary.getDisplayId();
        return Arrays.stream(displays)
                .filter(display -> display != null && display.isValid())
                .filter(display -> display.getDisplayId() != primaryId)
                .sorted(Comparator.comparingInt(Display::getDisplayId))
                .findFirst().orElse(null);
    }

    public synchronized boolean onDisplayAdded(Display primary, Display[] displays) {
        Display selected = select(primary, displays);
        int nextId = selected == null ? Display.INVALID_DISPLAY : selected.getDisplayId();
        boolean changed = nextId != selectedDisplayId;
        selectedDisplayId = nextId;
        primaryOnly = selected == null;
        reconnect |= changed && selected != null;
        return changed;
    }

    public synchronized boolean onDisplayRemoved(int displayId) {
        if (displayId != selectedDisplayId) {
            return false;
        }
        selectedDisplayId = Display.INVALID_DISPLAY;
        primaryOnly = true;
        reconnect = true;
        return true;
    }

    public synchronized void setMode(Mode mode) {
        if (this.mode != mode) {
            this.mode = mode;
            reconnect = true;
        }
        if (mode == Mode.DISABLED) {
            selectedDisplayId = Display.INVALID_DISPLAY;
            primaryOnly = true;
        }
    }

    public synchronized Mode getMode() { return mode; }
    public synchronized int getSelectedDisplayId() { return selectedDisplayId; }
    public synchronized boolean isPrimaryOnly() { return primaryOnly; }
    public synchronized boolean consumeReconnect() {
        boolean value = reconnect;
        reconnect = false;
        return value;
    }
}
