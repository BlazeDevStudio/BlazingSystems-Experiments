#pragma once
#include <windows.h>
#include <flutter/binary_messenger.h>
#include <flutter/encodable_value.h>
#include <flutter/method_channel.h>
#include <flutter/standard_method_codec.h>
#include <memory>
#include <string>

// Independent Win32 HWND. Incoming calls must never restore/focus the
// main Flutter window, even when the main app was minimized to tray.
class WindowsCallToast {
 public:
  explicit WindowsCallToast(flutter::BinaryMessenger* messenger, HWND main_window);
  ~WindowsCallToast();
  WindowsCallToast(const WindowsCallToast&) = delete;
  WindowsCallToast& operator=(const WindowsCallToast&) = delete;

 private:
  using MethodChannel = flutter::MethodChannel<flutter::EncodableValue>;
  std::unique_ptr<MethodChannel> channel_;
  HWND hwnd_ = nullptr;
  HWND main_window_ = nullptr;
  HWND buttons_[3] = {};
  std::wstring caller_;
  std::string call_id_;
  bool incoming_ = true;
  bool video_ = false;
  bool muted_ = false;
  bool manually_moved_ = false;
  bool EnsureWindow();
  void Show(bool incoming, bool video, bool muted,
            const std::string& id, const std::string& caller);
  void Hide();
  void ResizeButtons();
  void Emit(const char* action);
  LRESULT Handle(HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam);
  static LRESULT CALLBACK WindowProc(HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam);
};