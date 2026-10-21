package com.blazesystems.blazerental;

import android.bluetooth.BluetoothAdapter;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.media.AudioManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.SystemClock;
import android.text.TextUtils;
import android.util.Log;
import android.os.Handler;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import com.android.launcher3.CellLayout;
import com.android.launcher3.Hotseat;
import com.android.launcher3.Launcher;
import com.android.launcher3.Workspace;
import java.util.List;

public final class RentalSystemPages {
    public static final long PAGE_RENTAL = -401L;
    public static final long PAGE_QUICK = -402L;
    public static final long PAGE_NOTIFICATIONS = -403L;

    private static final int PAGER_VIEW_ID = 0x740400;
    private static final int FIXED_RENTAL = 0;
    private static final int FIXED_QUICK = 1;
    private static final int FIXED_NOTIFICATIONS = 2;
    private static final String UI_PREFS = "blaze_rental_ui";
    private static final String UI_FIXED_PAGE = "fixed_page";

    private RentalSystemPages() {}

    public static void apply(final Launcher launcher) {
        Workspace workspace = launcher.getWorkspace();
        if (workspace == null) return;
        boolean restricted = LauncherAccessController.isRentalRestricted(launcher);
        ManagedPolicyController.apply(launcher);
        ManagedPolicyController.enforceLauncherTask(launcher);

        View existing = workspace.findViewById(PAGER_VIEW_ID);
        if (!restricted) {
            // "Use device as is" must restore Launcher3's ordinary workspace once.
            // Avoid a reload loop by only forcing the model when our managed pager
            // is actually still attached.
            if (existing != null) launcher.getModel().forceReload();
            Hotseat hotseat = launcher.getHotseat();
            if (hotseat != null) hotseat.setVisibility(View.VISIBLE);
            return;
        }

        if (existing instanceof RentalFixedPager) {
            ((RentalFixedPager) existing).refreshPolicy();
            reassertRestrictedChrome(launcher);
            return;
        }

        // Use one Launcher3 workspace screen containing a native managed pager.
        // Old Launcher3 page reconstruction was able to reorder/reset sibling
        // workspace screens during model callbacks. Keeping the three operator
        // surfaces inside one fixed managed view makes rental/quick/notification
        // navigation independent of Launcher3 database screen reconciliation while
        // preserving horizontal page gestures and the normal paid app-drawer gesture.
        workspace.removeAllWorkspaceScreens();
        CellLayout rental = workspace.getScreenWithId(Workspace.FIRST_SCREEN_ID);
        if (rental == null) {
            rental = workspace.insertNewWorkspaceScreen(Workspace.FIRST_SCREEN_ID, 0);
        }
        rental.removeAllViews();

        RentalFixedPager pager = new RentalFixedPager(launcher);
        // CellLayout assigns the child ID during insertion. Keep it identical
        // to the ID used above to find and reuse the managed pager.
        attachFullPage(rental, pager, PAGER_VIEW_ID);
        workspace.snapToPageImmediately(0);
        workspace.setCurrentPage(0);

        reassertRestrictedChrome(launcher);
        workspace.post(new Runnable() {
            @Override public void run() { reassertRestrictedChrome(launcher); }
        });
        workspace.postDelayed(new Runnable() {
            @Override public void run() { reassertRestrictedChrome(launcher); }
        }, 750L);
    }

    public static void reassertRestrictedChrome(final Launcher launcher) {
        if (launcher == null || !LauncherAccessController.isRentalRestricted(launcher)) return;
        Hotseat hotseat = launcher.getHotseat();
        if (hotseat != null) {
            hotseat.setVisibility(View.GONE);
            hotseat.setEnabled(false);
        }
        View hotseatView = launcher.findViewById(com.android.launcher3.R.id.hotseat);
        if (hotseatView != null) {
            hotseatView.setVisibility(View.GONE);
            hotseatView.setEnabled(false);
        }
        View pageIndicator = launcher.findViewById(com.android.launcher3.R.id.page_indicator);
        if (pageIndicator != null) {
            pageIndicator.setVisibility(View.GONE);
            pageIndicator.setEnabled(false);
        }
        View allAppsHandle = launcher.findViewById(com.android.launcher3.R.id.all_apps_handle);
        if (allAppsHandle != null) {
            allAppsHandle.setVisibility(View.GONE);
            allAppsHandle.setEnabled(false);
        }
    }

    private static void attachFullPage(CellLayout page, View view, int id) {
        CellLayout.LayoutParams lp = new CellLayout.LayoutParams(
                0, 0, page.getCountX(), page.getCountY());
        lp.canReorder = false;
        page.addViewToCellLayout(view, 0, id, lp, true);
    }

    private static View createRentalPage(final Launcher launcher) {
        final LinearLayout root = basePage(launcher);
        // Launcher3 gives its workspace a shorter viewport than the screen.
        // Keep the primary coin action above the fold; scroll on small devices.
        final TextView state = headline(launcher, "BLAZERENTAL");
        state.setTextSize(22f);
        state.setPadding(0, dp(launcher, 3), 0, dp(launcher, 3));
        final TextView timer = headline(launcher, "00:00:00");
        timer.setTextSize(36f);
        timer.setPadding(0, dp(launcher, 3), 0, dp(launcher, 3));
        final Handler adminHandler = new Handler();
        final long holdMs = RentalUiPolicy.adminHoldMs(launcher);
        final AdminGestureController adminGesture = new AdminGestureController(holdMs);
        final Runnable openAdmin = new Runnable() {
            @Override public void run() {
                if (adminGesture.shouldTrigger(SystemClock.elapsedRealtime())) {
                    adminGesture.cancel();
                    launcher.startActivity(new Intent(launcher, BlazeAdminActivity.class));
                }
            }
        };
        timer.setOnTouchListener(new View.OnTouchListener() {
            @Override public boolean onTouch(View v, MotionEvent event) {
                if (event.getAction() == MotionEvent.ACTION_DOWN) {
                    adminGesture.onDown(SystemClock.elapsedRealtime());
                    adminHandler.postDelayed(openAdmin, holdMs);
                    return true;
                }
                if (event.getAction() == MotionEvent.ACTION_UP
                        || event.getAction() == MotionEvent.ACTION_CANCEL) {
                    adminHandler.removeCallbacks(openAdmin);
                    adminGesture.onUp(SystemClock.elapsedRealtime());
                    return true;
                }
                return true;
            }
        });
        final TextView detail = body(launcher, "TIME FINISHED");
        detail.setPadding(0, dp(launcher, 4), 0, dp(launcher, 4));
        final Button coin = actionButton(launcher, "INSERT COIN");

        root.addView(state);
        root.addView(timer);
        root.addView(detail);
        root.addView(coin, rentalButtonMargins(launcher));

        coin.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                coin.setEnabled(false);
                detail.setText("Waiting for coin controller...");
                new Thread(new Runnable() {
                    @Override public void run() {
                        final String result = LeaseClient.coinStart(launcher, "");
                        launcher.runOnUiThread(new Runnable() {
                            @Override public void run() {
                                detail.setText(result);
                                coin.setEnabled(true);
                            }
                        });
                    }
                }).start();
            }
        });

        final Runnable refresh = new Runnable() {
            @Override public void run() {
                long remaining = RentalLeaseStore.remainingMs(launcher);
                boolean paid = remaining > 0L;
                if (paid) FloatingTimerService.ensure(launcher);
                else FloatingTimerService.stop(launcher);
                setTextIfChanged(timer, formatDuration(remaining));
                setTextIfChanged(detail, paid ? "RENTAL ACTIVE" : "TIME FINISHED");
                setTextIfChanged(coin, paid ? "ADD MORE TIME" : "INSERT COIN");
                if (root.getWindowToken() != null) root.postDelayed(this, 1000L);
            }
        };
        root.post(refresh);
        ScrollView scroll = new ScrollView(launcher);
        scroll.setFillViewport(true);
        scroll.setVerticalScrollBarEnabled(false);
        scroll.addView(root);
        return scroll;
    }

    private static View createQuickPage(final Launcher launcher) {
        LinearLayout root = basePage(launcher);
        root.addView(headline(launcher, "QUICK CONTROLS"));

        final AudioManager audio = (AudioManager) launcher.getSystemService(Context.AUDIO_SERVICE);
        if (RentalUiPolicy.quickControlAllowed(launcher, "volume_down")
                || RentalUiPolicy.quickControlAllowed(launcher, "volume_up")) {
            LinearLayout volume = horizontal(launcher);
            Button down = smallButton(launcher, "VOLUME −");
            Button up = smallButton(launcher, "VOLUME +");
            if (RentalUiPolicy.quickControlAllowed(launcher, "volume_down")) {
                volume.addView(down, weight());
                down.setOnClickListener(new View.OnClickListener() {
                    @Override public void onClick(View v) {
                        QuickControlController.adjustVolume(launcher, AudioManager.ADJUST_LOWER);
                    }
                });
            }
            if (RentalUiPolicy.quickControlAllowed(launcher, "volume_up")) {
                volume.addView(up, weight());
                up.setOnClickListener(new View.OnClickListener() {
                    @Override public void onClick(View v) {
                        QuickControlController.adjustVolume(launcher, AudioManager.ADJUST_RAISE);
                    }
                });
            }
            root.addView(volume, rowMargins(launcher));
        }

        if (RentalUiPolicy.quickControlAllowed(launcher, "bluetooth")) {
            final Button bluetoothToggle = smallButton(launcher,
                    QuickControlController.isBluetoothEnabled() ? "BLUETOOTH: ON" : "BLUETOOTH: OFF");
            root.addView(bluetoothToggle, rowMargins(launcher));
            bluetoothToggle.setOnClickListener(new View.OnClickListener() {
                @Override public void onClick(View v) {
                    boolean next = !QuickControlController.isBluetoothEnabled();
                    boolean requested = QuickControlController.setBluetoothEnabled(next);
                    bluetoothToggle.setText(next && requested ? "BLUETOOTH: ON" : "BLUETOOTH: OFF");
                    if (!requested) Toast.makeText(launcher,
                            "Bluetooth control is unavailable on this device", Toast.LENGTH_SHORT).show();
                }
            });
    
            }

        if (RentalUiPolicy.quickControlAllowed(launcher, "flashlight")) {
            final Button torchToggle = smallButton(launcher,
                    QuickControlController.torchEnabled(launcher) ? "FLASHLIGHT: ON" : "FLASHLIGHT: OFF");
            root.addView(torchToggle, rowMargins(launcher));
            torchToggle.setOnClickListener(new View.OnClickListener() {
                @Override public void onClick(View v) {
                    boolean next = !QuickControlController.torchEnabled(launcher);
                    if (QuickControlController.setTorch(launcher, next)) {
                        torchToggle.setText(next ? "FLASHLIGHT: ON" : "FLASHLIGHT: OFF");
                    } else {
                        Toast.makeText(launcher, "Flashlight unavailable", Toast.LENGTH_SHORT).show();
                    }
                }
            });
    
            }

        if (RentalUiPolicy.quickControlAllowed(launcher, "network_status")) {
            root.addView(infoCard(launcher, networkStatus(launcher)));
        }
        if (RentalUiPolicy.quickControlAllowed(launcher, "battery_status")) {
            root.addView(infoCard(launcher, batteryStatus(launcher)));
        }


        if (RentalUiPolicy.floatingTimerUserToggleAllowed(launcher)) {
            final Button timerToggle = smallButton(launcher,
                    launcher.getSharedPreferences("blaze_rental_ui", Context.MODE_PRIVATE)
                            .getBoolean("floating_timer", true)
                            ? "FLOATING TIMER: ON" : "FLOATING TIMER: OFF");
            root.addView(timerToggle, rowMargins(launcher));
            timerToggle.setOnClickListener(new View.OnClickListener() {
                @Override public void onClick(View v) {
                    boolean current = launcher.getSharedPreferences(
                            "blaze_rental_ui", Context.MODE_PRIVATE)
                            .getBoolean("floating_timer", true);
                    boolean next = !current;
                    QuickControlController.setFloatingTimer(launcher, next);
                    timerToggle.setText(next ? "FLOATING TIMER: ON" : "FLOATING TIMER: OFF");
                    Toast.makeText(launcher, next ? "Floating timer enabled" :
                            "Floating timer disabled", Toast.LENGTH_SHORT).show();
                }
            });
        } else if (RentalUiPolicy.quickControlAllowed(launcher, "floating_timer")) {
            root.addView(infoCard(launcher,
                    RentalUiPolicy.floatingTimerForcedOn(launcher)
                            ? "Floating timer: always on (operator policy)"
                            : "Floating timer: off (operator policy)"));
        }

        root.addView(body(launcher,
                "Safe controls only. Android Settings and the system notification shade stay locked in Rental Mode."));
        ScrollView scroll = new ScrollView(launcher);
        scroll.setFillViewport(true);
        scroll.addView(root);
        return scroll;
    }

    private static View createNotificationsPage(final Launcher launcher) {
        final LinearLayout root = basePage(launcher);
        root.addView(headline(launcher, "NOTIFICATIONS"));
        if (!RentalUiPolicy.notificationsEnabled(launcher)) {
            root.addView(infoCard(launcher, "Notification page disabled by operator policy."));
            ScrollView disabled = new ScrollView(launcher);
            disabled.setFillViewport(true);
            disabled.addView(root);
            return disabled;
        }
        final LinearLayout list = new LinearLayout(launcher);
        list.setOrientation(LinearLayout.VERTICAL);
        root.addView(list, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        final String[] renderedSignature = new String[] { null };
        final Runnable refresh = new Runnable() {
            @Override public void run() {
                List<RentalNotificationService.Entry> entries =
                        RentalNotificationService.snapshot();
                StringBuilder signature = new StringBuilder();
                for (RentalNotificationService.Entry entry : entries) {
                    signature.append(entry.key).append('|')
                            .append(entry.title).append('|')
                            .append(entry.text).append(';');
                }
                String nextSignature = signature.toString();
                if (TextUtils.equals(renderedSignature[0], nextSignature)) {
                    if (root.getWindowToken() != null) root.postDelayed(this, 2000L);
                    return;
                }
                renderedSignature[0] = nextSignature;
                list.removeAllViews();
                if (entries.isEmpty()) {
                    list.addView(infoCard(launcher,
                            "No mirrored notifications yet. Notification access is granted during managed setup."));
                } else {
                    int start = Math.max(0, entries.size() - 8);
                    for (int i = entries.size() - 1; i >= start; i--) {
                        RentalNotificationService.Entry e = entries.get(i);
                        String title = e.title.length() == 0 ? e.packageName : e.title;
                        String text = e.text.length() == 0 ? e.packageName : e.text;
                        final RentalNotificationService.Entry entry = e;
                        TextView card = infoCard(launcher, title + "\n" + text);
                        card.setOnClickListener(new View.OnClickListener() {
                            @Override public void onClick(View v) {
                                if (!RentalNotificationService.open(launcher, entry.key)) {
                                    Toast.makeText(launcher,
                                            "This notification cannot open a blocked app",
                                            Toast.LENGTH_SHORT).show();
                                }
                            }
                        });
                        card.setOnLongClickListener(new View.OnLongClickListener() {
                            @Override public boolean onLongClick(View v) {
                                RentalNotificationService.dismiss(entry.key);
                                return true;
                            }
                        });
                        list.addView(card);
                    }
                }
                if (root.getWindowToken() != null) root.postDelayed(this, 2000L);
            }
        };
        root.post(refresh);
        ScrollView scroll = new ScrollView(launcher);
        scroll.setFillViewport(true);
        scroll.addView(root);
        return scroll;
    }

    private static LinearLayout basePage(final Launcher launcher) {
        LinearLayout root = new LinearLayout(launcher);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        int p = dp(launcher, 24);
        root.setPadding(p, dp(launcher, 54), p, p);
        root.setBackgroundColor(Color.rgb(10, 16, 29));
        return root;
    }

    /**
     * The three operator-owned Rental Mode surfaces live in this one native
     * Launcher3 workspace child. This avoids old Launcher3 screen-db/model
     * reconciliation racing the rental UI while still behaving as a horizontal
     * three-page carousel to the renter.
     */
    private static final class RentalFixedPager extends FrameLayout {
        private final Launcher launcher;
        private int page;
        private float downX;
        private float downY;
        private boolean horizontalGesture;

        RentalFixedPager(Launcher launcher) {
            super(launcher);
            this.launcher = launcher;
            setClickable(true);
            setFocusable(true);
            int saved = launcher.getSharedPreferences(UI_PREFS, Context.MODE_PRIVATE)
                    .getInt(UI_FIXED_PAGE, FIXED_RENTAL);
            page = sanitizePage(saved);
            render();
        }

        @Override
        public boolean dispatchTouchEvent(MotionEvent event) {
            // Launcher3 Workspace is itself a horizontal PagedView. Reserve
            // the touch stream on DOWN so it cannot steal a renter's page
            // swipe before this managed pager can classify it. Hand clearly
            // vertical motion back quickly so the paid app-drawer gesture
            // remains available to Launcher3.
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    downX = event.getX();
                    downY = event.getY();
                    horizontalGesture = false;
                    setOuterInterceptionBlocked(true);
                    break;
                case MotionEvent.ACTION_MOVE:
                    float dx = event.getX() - downX;
                    float dy = event.getY() - downY;
                    if (Math.abs(dy) > dp(launcher, 12)
                            && Math.abs(dy) > Math.abs(dx) * 1.15f) {
                        setOuterInterceptionBlocked(false);
                    } else if (Math.abs(dx) > dp(launcher, 12)
                            && Math.abs(dx) > Math.abs(dy) * 1.15f) {
                        setOuterInterceptionBlocked(true);
                    }
                    break;
                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    setOuterInterceptionBlocked(false);
                    break;
                default:
                    break;
            }
            return super.dispatchTouchEvent(event);
        }

        private void setOuterInterceptionBlocked(boolean blocked) {
            if (getParent() != null) {
                getParent().requestDisallowInterceptTouchEvent(blocked);
            }
        }

        void refreshPolicy() {
            render();
        }

        private int sanitizePage(int value) {
            if (value < FIXED_RENTAL || value > FIXED_NOTIFICATIONS) {
                return FIXED_RENTAL;
            }
            return value;
        }

        private void showPage(int next) {
            int sanitized = sanitizePage(next);
            if (page == sanitized && getChildCount() > 0) return;
            page = sanitized;
            launcher.getSharedPreferences(UI_PREFS, Context.MODE_PRIVATE)
                    .edit().putInt(UI_FIXED_PAGE, page).apply();
            render();
        }

        private void render() {
            removeAllViews();

            View content;
            if (page == FIXED_QUICK) {
                content = createQuickPage(launcher);
            } else if (page == FIXED_NOTIFICATIONS) {
                content = createNotificationsPage(launcher);
            } else {
                page = FIXED_RENTAL;
                content = createRentalPage(launcher);
            }
            addView(content, new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT));

            LinearLayout nav = new LinearLayout(launcher);
            nav.setOrientation(LinearLayout.HORIZONTAL);
            nav.setGravity(Gravity.CENTER_VERTICAL);

            if (page > FIXED_RENTAL) {
                final int previous = page - 1;
                Button left = navButton(launcher,
                        page == FIXED_NOTIFICATIONS ? "< QUICK CONTROLS" : "< RENTAL");
                bindPagerButton(left, previous);
                nav.addView(left, weight());
            } else {
                nav.addView(new View(launcher), weight());
            }

            if (page < FIXED_NOTIFICATIONS) {
                final int next = page + 1;
                Button right = navButton(launcher,
                        page == FIXED_RENTAL ? "QUICK CONTROLS >" : "NOTIFICATIONS >");
                bindPagerButton(right, next);
                nav.addView(right, weight());
            } else {
                nav.addView(new View(launcher), weight());
            }

            FrameLayout.LayoutParams navLp = new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(launcher, 44), Gravity.TOP);
            navLp.setMargins(dp(launcher, 24), dp(launcher, 8), dp(launcher, 24), 0);
            addView(nav, navLp);
            Log.i("BlazeRentalPager", "page=" + page + " children=" + getChildCount());
        }

        private void bindPagerButton(Button button, final int target) {
            button.setOnClickListener(new View.OnClickListener() {
                @Override public void onClick(View v) {
                    showPage(target);
                }
            });
            // ACTION_DOWN makes the fallback deterministic on old Android touch
            // stacks where ScrollView can cancel the eventual Button click.
            button.setOnTouchListener(new View.OnTouchListener() {
                @Override public boolean onTouch(View v, MotionEvent event) {
                    if (event.getActionMasked() == MotionEvent.ACTION_DOWN) {
                        showPage(target);
                        return true;
                    }
                    return true;
                }
            });
        }

        @Override
        public boolean onInterceptTouchEvent(MotionEvent event) {
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    downX = event.getX();
                    downY = event.getY();
                    horizontalGesture = false;
                    return false;
                case MotionEvent.ACTION_MOVE:
                    float dx = event.getX() - downX;
                    float dy = event.getY() - downY;
                    if (Math.abs(dx) > dp(launcher, 40)
                            && Math.abs(dx) > Math.abs(dy) * 1.25f) {
                        horizontalGesture = true;
                        return true;
                    }
                    return false;
                default:
                    return horizontalGesture;
            }
        }

        @Override
        public boolean onTouchEvent(MotionEvent event) {
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_MOVE:
                    // If this pager owns the stream directly (for example a
                    // swipe beginning on non-clickable content), interception
                    // may not have classified the MOVE yet.
                    float moveX = event.getX() - downX;
                    float moveY = event.getY() - downY;
                    if (Math.abs(moveX) > dp(launcher, 40)
                            && Math.abs(moveX) > Math.abs(moveY) * 1.25f) {
                        horizontalGesture = true;
                    }
                    return true;
                case MotionEvent.ACTION_UP:
                    float dx = event.getX() - downX;
                    float dy = event.getY() - downY;
                    if (horizontalGesture
                            && Math.abs(dx) > dp(launcher, 56)
                            && Math.abs(dx) > Math.abs(dy) * 1.25f) {
                        showPage(Math.max(FIXED_RENTAL, Math.min(FIXED_NOTIFICATIONS,
                                page + (dx < 0f ? 1 : -1))));
                    }
                    horizontalGesture = false;
                    return true;
                case MotionEvent.ACTION_CANCEL:
                    horizontalGesture = false;
                    return true;
                default:
                    return true;
            }
        }
    }

    private static Button navButton(Context c, String text) {
        Button b = new Button(c);
        b.setText(text);
        b.setTextSize(11f);
        b.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        b.setTextColor(Color.rgb(226, 232, 240));
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.rgb(30, 41, 59));
        bg.setCornerRadius(dp(c, 12));
        b.setBackground(bg);
        b.setMinHeight(dp(c, 40));
        b.setPadding(dp(c, 8), 0, dp(c, 8), 0);
        return b;
    }

    private static LinearLayout horizontal(Context context) {
        LinearLayout row = new LinearLayout(context);
        row.setOrientation(LinearLayout.HORIZONTAL);
        return row;
    }

    private static TextView headline(Context c, String text) {
        TextView v = new TextView(c);
        v.setText(text);
        v.setTextColor(Color.WHITE);
        v.setTextSize(26f);
        v.setGravity(Gravity.CENTER);
        v.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        v.setPadding(0, dp(c, 8), 0, dp(c, 8));
        return v;
    }

    private static TextView body(Context c, String text) {
        TextView v = new TextView(c);
        v.setText(text);
        v.setTextColor(Color.rgb(180, 194, 217));
        v.setTextSize(15f);
        v.setGravity(Gravity.CENTER);
        v.setPadding(dp(c, 8), dp(c, 10), dp(c, 8), dp(c, 10));
        return v;
    }

    private static TextView infoCard(Context c, String text) {
        TextView v = body(c, text);
        v.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.rgb(20, 30, 49));
        bg.setCornerRadius(dp(c, 14));
        v.setBackground(bg);
        LinearLayout.LayoutParams lp = rowMargins(c);
        v.setLayoutParams(lp);
        return v;
    }

    private static Button actionButton(Context c, String text) {
        Button b = new Button(c);
        b.setText(text);
        b.setTextSize(18f);
        b.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        b.setTextColor(Color.WHITE);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.rgb(37, 99, 235));
        bg.setCornerRadius(dp(c, 14));
        b.setBackground(bg);
        b.setMinHeight(dp(c, 58));
        return b;
    }

    private static Button smallButton(Context c, String text) {
        Button b = actionButton(c, text);
        b.setTextSize(13f);
        b.setMinHeight(dp(c, 48));
        return b;
    }

    private static LinearLayout.LayoutParams rentalButtonMargins(Context c) {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(c, 54));
        lp.setMargins(0, dp(c, 8), 0, dp(c, 12));
        return lp;
    }

    private static LinearLayout.LayoutParams buttonMargins(Context c) {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(c, 62));
        lp.setMargins(0, dp(c, 24), 0, dp(c, 18));
        return lp;
    }

    private static LinearLayout.LayoutParams rowMargins(Context c) {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, dp(c, 8), 0, dp(c, 8));
        return lp;
    }

    private static LinearLayout.LayoutParams weight() {
        return new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
    }

    private static void setTextIfChanged(TextView view, CharSequence value) {
        if (!TextUtils.equals(view.getText(), value)) view.setText(value);
    }

    private static String batteryStatus(Context c) {
        try {
            Intent state = c.registerReceiver(null, new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
            if (state == null) return "Battery: unavailable";
            int level = state.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
            int scale = state.getIntExtra(BatteryManager.EXTRA_SCALE, 100);
            int percent = level < 0 ? -1 : Math.round(level * 100f / Math.max(1, scale));
            return percent < 0 ? "Battery: unavailable" : "Battery: " + percent + "%";
        } catch (Exception ignored) {
            return "Battery: unavailable";
        }
    }

    private static String networkStatus(Context c) {
        try {
            ConnectivityManager cm = (ConnectivityManager)
                    c.getSystemService(Context.CONNECTIVITY_SERVICE);
            NetworkInfo active = cm == null ? null : cm.getActiveNetworkInfo();
            return active != null && active.isConnected()
                    ? "Network: connected via " + active.getTypeName()
                    : "Network: offline";
        } catch (Exception ignored) {
            return "Network: unavailable";
        }
    }

    private static String formatDuration(long ms) {
        long total = Math.max(0L, ms / 1000L);
        long hours = total / 3600L;
        long minutes = (total % 3600L) / 60L;
        long seconds = total % 60L;
        return String.format("%02d:%02d:%02d", hours, minutes, seconds);
    }

    private static int dp(Context c, int value) {
        return Math.round(value * c.getResources().getDisplayMetrics().density);
    }
}
