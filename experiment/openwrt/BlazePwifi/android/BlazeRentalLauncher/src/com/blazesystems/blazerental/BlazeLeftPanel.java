package com.blazesystems.blazerental;

import android.os.SystemClock;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;

import com.android.launcher3.Launcher;

/**
 * BlazeRental v0.5 custom-left surface.
 *
 * Far left: rental / Insert Coin gate.
 * Next: notification mirror.
 * Outside this view: the ordinary Launcher3 workspace.
 */
public final class BlazeLeftPanel extends FrameLayout {
    private static final int PAGE_RENTAL = 0;
    private static final int PAGE_NOTIFICATIONS = 1;
    private static final int SWIPE_DP = 52;

    private final Launcher launcher;
    private int page;
    private float downX;
    private float downY;
    private boolean horizontal;
    private boolean lastCanUseDevice;

    public BlazeLeftPanel(Launcher launcher) {
        super(launcher);
        this.launcher = launcher;
        setClickable(true);
        setFocusable(true);
        lastCanUseDevice = canUseDevice();
        page = lastCanUseDevice ? PAGE_NOTIFICATIONS : PAGE_RENTAL;
        render();
    }

    public static Launcher.CustomContentCallbacks callbacks(
            final Launcher launcher, final BlazeLeftPanel panel) {
        return new Launcher.CustomContentCallbacks() {
            @Override public void onShow(boolean fromResume) {
                panel.refreshPolicy();
            }
            @Override public void onHide() {}
            @Override public void onScrollProgressChanged(float progress) {}
            @Override public boolean isScrollingAllowed() {
                // This is the hard workspace boundary: unpaid rental devices
                // cannot scroll from Blaze content into the normal Home pages.
                return LauncherAccessController.canUseDevice(launcher);
            }
        };
    }

    public void refreshPolicy() {
        boolean allowed = canUseDevice();
        boolean pageChanged = !allowed && page != PAGE_RENTAL;
        boolean policyChanged = allowed != lastCanUseDevice;
        if (pageChanged) {
            page = PAGE_RENTAL;
        }
        lastCanUseDevice = allowed;
        // Keep the current rental view alive while policy is unchanged.
        // Rebuilding it on every Launcher3 onShow can cancel an in-progress
        // secret timer hold and creates unnecessary visual churn.
        if (pageChanged || policyChanged) {
            render();
        }
    }

    private boolean canUseDevice() {
        return LauncherAccessController.canUseDevice(launcher);
    }

    private void render() {
        removeAllViews();

        View content = page == PAGE_NOTIFICATIONS
                ? RentalSystemPages.createNotificationsPage(launcher)
                : RentalSystemPages.createRentalPage(launcher);
        addView(content, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        LinearLayout nav = new LinearLayout(launcher);
        nav.setOrientation(LinearLayout.HORIZONTAL);
        nav.setGravity(Gravity.CENTER_VERTICAL);

        if (page == PAGE_NOTIFICATIONS) {
            Button left = navButton("‹ BLAZERENTAL");
            left.setOnClickListener(new OnClickListener() {
                @Override public void onClick(View v) {
                    page = PAGE_RENTAL;
                    render();
                }
            });
            nav.addView(left, weight());

            Button home = navButton(canUseDevice() ? "HOME ›" : "LOCKED");
            home.setEnabled(canUseDevice());
            nav.addView(home, weight());
        } else {
            nav.addView(new View(launcher), weight());
            Button notifications = navButton(canUseDevice() ? "NOTIFICATIONS ›" : "LOCKED");
            notifications.setEnabled(canUseDevice());
            notifications.setOnClickListener(new OnClickListener() {
                @Override public void onClick(View v) {
                    if (canUseDevice()) {
                        page = PAGE_NOTIFICATIONS;
                        render();
                    }
                }
            });
            nav.addView(notifications, weight());
        }

        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(46), Gravity.TOP);
        lp.setMargins(dp(18), dp(8), dp(18), 0);
        addView(nav, lp);
    }

    private Button navButton(String label) {
        Button b = new Button(launcher);
        b.setText(label);
        b.setAllCaps(false);
        b.setTextSize(11f);
        b.setMinHeight(0);
        b.setMinimumHeight(0);
        return b;
    }

    private LinearLayout.LayoutParams weight() {
        return new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.MATCH_PARENT, 1f);
    }

    @Override public boolean dispatchTouchEvent(MotionEvent event) {
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                downX = event.getX();
                downY = event.getY();
                horizontal = false;
                setOuterBlocked(true);
                break;
            case MotionEvent.ACTION_MOVE:
                float dx = event.getX() - downX;
                float dy = event.getY() - downY;
                if (Math.abs(dy) > dp(12) && Math.abs(dy) > Math.abs(dx) * 1.15f) {
                    setOuterBlocked(false);
                } else if (Math.abs(dx) > dp(12) && Math.abs(dx) > Math.abs(dy) * 1.15f) {
                    // On Notifications, a left swipe belongs to Launcher3 Home,
                    // but only after the rental gate is legitimately open.
                    if (page == PAGE_NOTIFICATIONS && dx < 0 && canUseDevice()) {
                        setOuterBlocked(false);
                    } else {
                        setOuterBlocked(true);
                    }
                }
                break;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                setOuterBlocked(false);
                break;
            default:
                break;
        }
        return super.dispatchTouchEvent(event);
    }

    @Override public boolean onInterceptTouchEvent(MotionEvent event) {
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                downX = event.getX();
                downY = event.getY();
                horizontal = false;
                return false;
            case MotionEvent.ACTION_MOVE:
                float dx = event.getX() - downX;
                float dy = event.getY() - downY;
                if (Math.abs(dx) > dp(SWIPE_DP)
                        && Math.abs(dx) > Math.abs(dy) * 1.20f) {
                    if (page == PAGE_NOTIFICATIONS && dx < 0 && canUseDevice()) {
                        return false;
                    }
                    horizontal = true;
                    return true;
                }
                return false;
            default:
                return horizontal;
        }
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        if (event.getActionMasked() == MotionEvent.ACTION_UP && horizontal) {
            float dx = event.getX() - downX;
            if (dx < -dp(SWIPE_DP) && page == PAGE_RENTAL && canUseDevice()) {
                page = PAGE_NOTIFICATIONS;
                render();
            } else if (dx > dp(SWIPE_DP) && page == PAGE_NOTIFICATIONS) {
                page = PAGE_RENTAL;
                render();
            }
            horizontal = false;
            return true;
        }
        if (event.getActionMasked() == MotionEvent.ACTION_CANCEL) {
            horizontal = false;
        }
        return true;
    }

    private void setOuterBlocked(boolean blocked) {
        if (getParent() != null) {
            getParent().requestDisallowInterceptTouchEvent(blocked);
        }
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
