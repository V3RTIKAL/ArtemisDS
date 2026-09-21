package com.limelight.secondary;

import android.app.Presentation;
import android.content.Context;
import android.os.Bundle;
import android.view.Display;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

/** Owns the optional decoder output surface on the selected secondary display. */
public final class SecondaryDisplayPresentation extends Presentation implements SurfaceHolder.Callback {
    public interface SurfaceListener {
        void surfaceAvailable(SurfaceHolder holder, int width, int height);
        void surfaceDestroying(SurfaceHolder holder);
    }

    private final SurfaceListener listener;
    private SurfaceView surfaceView;

    public SecondaryDisplayPresentation(Context context, Display display, SurfaceListener listener) {
        super(context, display);
        this.listener = listener;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        surfaceView = new SurfaceView(getContext());
        surfaceView.getHolder().addCallback(this);
        setContentView(surfaceView);
    }

    @Override
    public void surfaceCreated(SurfaceHolder holder) {
        // Wait for surfaceChanged(), which supplies valid drawable dimensions.
    }

    @Override
    public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        if (width > 0 && height > 0 && holder.getSurface().isValid()) {
            listener.surfaceAvailable(holder, width, height);
        }
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder holder) {
        // Native teardown must complete before Android invalidates the output.
        listener.surfaceDestroying(holder);
    }

    @Override
    public void dismiss() {
        if (surfaceView != null) {
            surfaceView.getHolder().removeCallback(this);
        }
        super.dismiss();
    }
}
