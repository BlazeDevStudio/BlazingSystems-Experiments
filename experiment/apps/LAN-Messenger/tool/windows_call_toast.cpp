#include "windows_call_toast.h"
#include <windowsx.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <string>
#include <variant>

namespace {
constexpr wchar_t kToastClass[] = L"BlazingSystems.LanMessenger.CallToast.v028";
constexpr int kWidth = 304;
constexpr int kHeight = 134;
constexpr int kTitleHeight = 76;
constexpr int kButtonTop = 88;
std::wstring ToWide(const std::string& source) {
  if (source.empty()) return L"LAN Messenger";
  const auto count = MultiByteToWideChar(CP_UTF8, 0, source.c_str(),
                                        static_cast<int>(source.size()), nullptr, 0);
  if (count <= 0) return L"LAN Messenger";
  std::wstring result(count, L'\0');
  MultiByteToWideChar(CP_UTF8, 0, source.c_str(),
                      static_cast<int>(source.size()), result.data(), count);
  if (result.size() > 48) result.resize(48);
  return result;
}
std::string StringArg(const flutter::EncodableMap& args, const char* key) {
  auto it = args.find(flutter::EncodableValue(std::string(key)));
  if (it == args.end()) return "";
  if (auto v = std::get_if<std::string>(&it->second)) return *v;
  return "";
}
bool BoolArg(const flutter::EncodableMap& args, const char* key) {
  auto it = args.find(flutter::EncodableValue(std::string(key)));
  if (it == args.end()) return false;
  if (auto v = std::get_if<bool>(&it->second)) return *v;
  return false;
}
}  // namespace

WindowsCallToast::WindowsCallToast(flutter::BinaryMessenger* messenger,
                                   HWND main_window)
    : main_window_(main_window) {
  channel_ = std::make_unique<MethodChannel>(
      messenger, "lan_messenger/desktop_call",
      &flutter::StandardMethodCodec::GetInstance());
  channel_->SetMethodCallHandler(
      [this](const flutter::MethodCall<flutter::EncodableValue>& call,
             std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>> result) {
        if (call.method_name() == "restoreMainInactive") {
          if (!main_window_ || !IsWindow(main_window_)) {
            result->Success(flutter::EncodableValue(false));
          } else {
            ShowWindow(main_window_, SW_SHOWNOACTIVATE);
            result->Success(flutter::EncodableValue(true));
          }
          return;
        }
        if (call.method_name() == "dismiss") {
          Hide();
          result->Success(flutter::EncodableValue(true));
          return;
        }
        if (call.method_name() != "incoming" && call.method_name() != "ongoing") {
          result->NotImplemented();
          return;
        }
        const auto* args = call.arguments()
            ? std::get_if<flutter::EncodableMap>(call.arguments()) : nullptr;
        if (!args) {
          result->Error("BAD_ARGS", "Expected call metadata");
          return;
        }
        const auto id = StringArg(*args, "callId");
        const auto caller = StringArg(*args, "caller");
        if (id.empty() || id.size() > 64 || caller.empty()) {
          result->Error("BAD_CALL", "A caller and call ID are required");
          return;
        }
        // Native safeguard against late Dart calls after restoring Messenger.
        if (main_window_ && IsWindow(main_window_) &&
            IsWindowVisible(main_window_) && !IsIconic(main_window_)) {
          Hide();
          result->Success(flutter::EncodableValue(false));
          return;
        }
        Show(call.method_name() == "incoming", BoolArg(*args, "video"),
             BoolArg(*args, "muted"), id, caller);
        result->Success(flutter::EncodableValue(hwnd_ != nullptr));
      });
}

WindowsCallToast::~WindowsCallToast() {
  if (channel_) channel_->SetMethodCallHandler(nullptr);
  if (hwnd_) {
    DestroyWindow(hwnd_);
    hwnd_ = nullptr;
  }
}

bool WindowsCallToast::EnsureWindow() {
  if (hwnd_) return true;
  static bool registered = false;
  if (!registered) {
    WNDCLASSEXW wc = {};
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = WindowsCallToast::WindowProc;
    wc.hInstance = GetModuleHandleW(nullptr);
    wc.lpszClassName = kToastClass;
    wc.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    wc.hbrBackground = reinterpret_cast<HBRUSH>(GetStockObject(BLACK_BRUSH));
    if (!RegisterClassExW(&wc) && GetLastError() != ERROR_CLASS_ALREADY_EXISTS)
      return false;
    registered = true;
  }
  hwnd_ = CreateWindowExW(
      WS_EX_TOOLWINDOW | WS_EX_TOPMOST | WS_EX_NOACTIVATE,
      kToastClass, L"LAN Messenger call", WS_POPUP | WS_CLIPSIBLINGS,
      0, 0, kWidth, kHeight, nullptr, nullptr,
      GetModuleHandleW(nullptr), this);
  return hwnd_ != nullptr;
}

void WindowsCallToast::ResizeButtons() {
  if (!hwnd_) return;
  const wchar_t* captions[3];
  if (incoming_) {
    captions[0] = L"Answer";
    captions[1] = L"Decline";
    captions[2] = L"Open call";
  } else {
    captions[0] = muted_ ? L"Unmute" : L"Mute";
    captions[1] = L"End call";
    captions[2] = L"Open call";
  }
  // Incoming is deliberately TWO actions, like a Messenger call.
  // The third Open Thread action belongs only to an ongoing conversation.
  if (incoming_ && buttons_[2]) ShowWindow(buttons_[2], SW_HIDE);
  const int count = incoming_ ? 2 : 3;
  const int gap = 8;
  const int width = (kWidth - 24 - gap * (count - 1)) / count;
  for (int i = 0; i < count; ++i) {
    if (!buttons_[i]) {
      buttons_[i] = CreateWindowExW(0, L"BUTTON", captions[i],
          WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_PUSHBUTTON,
          0, 0, 100, 34, hwnd_,
          reinterpret_cast<HMENU>(static_cast<INT_PTR>(101 + i)),
          GetModuleHandleW(nullptr), nullptr);
      SendMessageW(buttons_[i], WM_SETFONT,
          reinterpret_cast<WPARAM>(GetStockObject(DEFAULT_GUI_FONT)), TRUE);
    }
    SetWindowTextW(buttons_[i], captions[i]);
    MoveWindow(buttons_[i], 12 + i * (width + gap),
               kButtonTop, width, 34, TRUE);
    ShowWindow(buttons_[i], SW_SHOWNA);
  }
}

void WindowsCallToast::Show(bool incoming, bool video, bool muted,
                            const std::string& id, const std::string& caller) {
  if (!EnsureWindow()) return;
  const bool new_call = call_id_ != id;
  call_id_ = id;
  caller_ = ToWide(caller);
  incoming_ = incoming;
  video_ = video;
  muted_ = muted;
  ResizeButtons();
  if (new_call || !IsWindowVisible(hwnd_)) {
    MONITORINFO monitor = {};
    monitor.cbSize = sizeof(monitor);
    // Place near the clock on Messenger's monitor, not necessarily primary.
    const HWND monitor_owner =
        (main_window_ && IsWindow(main_window_)) ? main_window_ : GetDesktopWindow();
    GetMonitorInfoW(MonitorFromWindow(monitor_owner, MONITOR_DEFAULTTONEAREST),
                    &monitor);
    const RECT& r = monitor.rcWork;
    const int x = r.right - kWidth - 14;
    const int y = r.bottom - kHeight - 14;
    SetWindowPos(hwnd_, HWND_TOPMOST, x, y, kWidth, kHeight,
                 SWP_NOACTIVATE | SWP_SHOWWINDOW);
    manually_moved_ = false;
  } else {
    ShowWindow(hwnd_, SW_SHOWNOACTIVATE);
  }
  InvalidateRect(hwnd_, nullptr, TRUE);
}

void WindowsCallToast::Hide() {
  if (hwnd_) ShowWindow(hwnd_, SW_HIDE);
  call_id_.clear();
}

void WindowsCallToast::Emit(const char* action) {
  if (!channel_ || call_id_.empty()) return;
  flutter::EncodableMap msg;
  msg[flutter::EncodableValue("action")] = flutter::EncodableValue(action);
  msg[flutter::EncodableValue("callId")] = flutter::EncodableValue(call_id_);
  channel_->InvokeMethod("callAction",
      std::make_unique<flutter::EncodableValue>(msg));
}

LRESULT CALLBACK WindowsCallToast::WindowProc(
    HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam) {
  auto* self = reinterpret_cast<WindowsCallToast*>(
      GetWindowLongPtrW(hwnd, GWLP_USERDATA));
  if (message == WM_NCCREATE) {
    const auto* cs = reinterpret_cast<CREATESTRUCTW*>(lparam);
    self = static_cast<WindowsCallToast*>(cs->lpCreateParams);
    SetWindowLongPtrW(hwnd, GWLP_USERDATA,
                      reinterpret_cast<LONG_PTR>(self));
  }
  if (self) return self->Handle(hwnd, message, wparam, lparam);
  return DefWindowProcW(hwnd, message, wparam, lparam);
}

LRESULT WindowsCallToast::Handle(
    HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam) {
  switch (message) {
    case WM_MOUSEACTIVATE:
      return MA_NOACTIVATE;  // A toast must never steal typing focus.
    case WM_NCHITTEST: {
      const auto result = DefWindowProcW(hwnd, message, wparam, lparam);
      if (result == HTCLIENT) {
        POINT pt = {GET_X_LPARAM(lparam), GET_Y_LPARAM(lparam)};
        ScreenToClient(hwnd, &pt);
        // Drag by the heading, independently of the main Flutter window.
        if (pt.y >= 0 && pt.y < kTitleHeight) return HTCAPTION;
      }
      return result;
    }
    case WM_COMMAND: {
      if (HIWORD(wparam) != BN_CLICKED) break;
      const int id = LOWORD(wparam);
      if (id == 101) Emit(incoming_ ? "answer" : "mute");
      else if (id == 102) Emit(incoming_ ? "decline" : "end");
      else if (id == 103) Emit("open");
      return 0;
    }
    case WM_PAINT: {
      PAINTSTRUCT ps;
      HDC dc = BeginPaint(hwnd, &ps);
      RECT rect;
      GetClientRect(hwnd, &rect);
      HBRUSH background = CreateSolidBrush(RGB(17, 34, 56));
      FillRect(dc, &rect, background);
      DeleteObject(background);
      SetBkMode(dc, TRANSPARENT);
      SetTextColor(dc, RGB(249, 252, 255));
      HFONT font = static_cast<HFONT>(GetStockObject(DEFAULT_GUI_FONT));
      const auto oldfont = SelectObject(dc, font);
      RECT title = {14, 13, kWidth - 14, 39};
      DrawTextW(dc, caller_.c_str(), -1, &title,
                DT_LEFT | DT_SINGLELINE | DT_END_ELLIPSIS | DT_NOPREFIX);
      const wchar_t* detail = incoming_
          ? (video_ ? L"Incoming video call" : L"Incoming voice call")
          : (video_ ? L"Video call connected" : L"Voice call connected");
      RECT subtitle = {14, 42, kWidth - 14, 75};
      SetTextColor(dc, RGB(170, 214, 237));
      DrawTextW(dc, detail, -1, &subtitle, DT_LEFT | DT_SINGLELINE);
      SelectObject(dc, oldfont);
      EndPaint(hwnd, &ps);
      return 0;
    }
    case WM_CLOSE:
      // Dismissing the popup must never answer/decline without consent.
      Hide();
      return 0;
    case WM_DESTROY:
      hwnd_ = nullptr;
      for (auto& button : buttons_) button = nullptr;
      return 0;
  }
  return DefWindowProcW(hwnd, message, wparam, lparam);
}
